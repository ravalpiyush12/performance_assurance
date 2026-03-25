# =============================================================================
# ADD TO: monitoring/pc/routes.py
#
# New endpoint: POST /api/v1/monitoring/pc/upload-results
# Accepts a .zip file + run metadata, extracts summary.html,
# parses with existing SummaryHTMLParser, inserts into
# API_PC_TEST_RUNS + API_LR_TRANSACTION_RESULTS — same tables as fetch-results.
# =============================================================================

import io
import zipfile

# (These imports should already exist in routes.py)
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from .parser import SummaryHTMLParser


@router.post("/upload-results")
async def upload_pc_results(
    file:             UploadFile = File(..., description="PC results ZIP file"),
    run_id:           str        = Form(..., description="Master run ID"),
    pc_run_id:        str        = Form(..., description="PC Run ID"),
    lob_name:         str        = Form(...),
    track:            Optional[str] = Form(None),
    test_name:        Optional[str] = Form(None),
    test_set_name:    Optional[str] = Form(None),
    test_instance_id: Optional[str] = Form(None),
):
    """
    POST /api/v1/monitoring/pc/upload-results

    Upload a PC results ZIP file manually (alternative to fetch-results).
    Extracts summary.html from the ZIP, parses transactions using
    SummaryHTMLParser, and stores into Oracle — same tables as fetch-results.

    ZIP structure expected (any of these paths are tried):
      summary.html
      Report/summary.html
      Results/summary.html
      *.html  (first HTML found, fallback)
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    # ── 1. Validate file type ────────────────────────────────────────────────
    filename = file.filename or ''
    if not filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail=f"Expected a .zip file, got: {filename}"
        )

    # ── 2. Read ZIP into memory ──────────────────────────────────────────────
    try:
        raw = await file.read()
        if len(raw) < 100:
            raise HTTPException(status_code=400, detail="Uploaded file is empty or too small.")

        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="File is not a valid ZIP archive. Download the results ZIP from Performance Center and upload it here."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read ZIP: {e}")

    # ── 3. Find summary.html inside the ZIP ──────────────────────────────────
    names = zf.namelist()
    logger.info(f"ZIP contents ({len(names)} files): {names[:20]}")

    # Priority order — same filenames PC uses
    CANDIDATES = [
        'summary.html',
        'Summary.html',
        'Report/summary.html',
        'Report/Summary.html',
        'Results/summary.html',
        'Results/Summary.html',
    ]
    summary_path = None
    for candidate in CANDIDATES:
        if candidate in names:
            summary_path = candidate
            break

    # Fallback: first .html file in the ZIP
    if not summary_path:
        html_files = [n for n in names if n.lower().endswith('.html')]
        if html_files:
            summary_path = html_files[0]
            logger.warning(f"summary.html not found by name, using fallback: {summary_path}")

    if not summary_path:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Could not find summary.html in the ZIP. "
                f"Files found: {', '.join(names[:10])}{'...' if len(names) > 10 else ''}"
            )
        )

    # ── 4. Parse summary.html ─────────────────────────────────────────────────
    try:
        html_bytes   = zf.read(summary_path)
        html_content = html_bytes.decode('utf-8', errors='replace')
        logger.info(f"Read {summary_path} ({len(html_content)} chars)")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read {summary_path}: {e}")

    try:
        parser       = SummaryHTMLParser(html_content)
        transactions = parser.parse_transactions()
        logger.info(f"Parsed {len(transactions)} transactions from ZIP")
    except Exception as e:
        logger.error(f"SummaryHTMLParser error: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Failed to parse summary.html: {e}")

    if not transactions:
        raise HTTPException(
            status_code=422,
            detail="No transactions found in summary.html. Check that the ZIP is a valid PC results export."
        )

    # ── 5. Validate master run exists ─────────────────────────────────────────
    master_run = pc_db.get_master_run_by_pc_id(pc_run_id)
    if not master_run:
        raise HTTPException(
            status_code=400,
            detail=f"Run {pc_run_id} not registered. Validate the PC Run ID first so the master run exists."
        )
    run_id = master_run['run_id']   # always use the DB run_id, not what frontend sent

    # ── 6. Save PC test run row ───────────────────────────────────────────────
    try:
        pc_test_id = pc_db.save_pc_test_run(
            run_id           = run_id,
            pc_run_id        = pc_run_id,
            pc_url           = 'MANUAL_UPLOAD',
            pc_domain        = '',
            pc_project       = '',
            test_status      = 'Finished',
            collation_status = 'Collated',
            test_set_name    = test_set_name or test_name or '',
            test_instance_id = test_instance_id or '',
        )
        logger.info(f"Saved PC test run, pc_test_id={pc_test_id}")
    except Exception as e:
        logger.error(f"save_pc_test_run error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save PC test run: {e}")

    # ── 7. Save transactions — same as fetch-results ──────────────────────────
    try:
        # transactions from SummaryHTMLParser are LRTransaction objects or dicts
        # normalise to list of dicts matching save_lr_transactions expectations
        tx_dicts = []
        for t in transactions:
            if hasattr(t, 'dict'):
                tx_dicts.append(t.dict())    # Pydantic model
            elif isinstance(t, dict):
                tx_dicts.append(t)
            else:
                tx_dicts.append(vars(t))

        pc_db.save_lr_transactions(run_id, pc_run_id, tx_dicts)
        logger.info(f"Saved {len(tx_dicts)} transactions for run {run_id}")
    except Exception as e:
        logger.error(f"save_lr_transactions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save transactions: {e}")

    # ── 8. Update master run status ───────────────────────────────────────────
    try:
        pc_db.update_master_run_status(run_id, 'COMPLETED')
    except Exception as e:
        logger.warning(f"update_master_run_status warning (non-critical): {e}")

    # ── 9. Calculate summary stats ────────────────────────────────────────────
    total   = len(tx_dicts)
    passed  = sum(1 for t in tx_dicts if float(t.get('pass_percentage', 0)) >= 95.0)
    failed  = total - passed
    avg_rt  = (
        sum(float(t.get('average_time', 0)) for t in tx_dicts) / total
        if total else 0.0
    )

    return {
        "success":             True,
        "run_id":              run_id,
        "pc_run_id":           pc_run_id,
        "source":              "MANUAL_UPLOAD",
        "zip_file":            filename,
        "summary_file":        summary_path,
        "total_transactions":  total,
        "passed_transactions": passed,
        "failed_transactions": failed,
        "average_response_time": round(avg_rt, 3),
        "message":             f"Successfully processed {total} transactions from ZIP upload.",
    }
