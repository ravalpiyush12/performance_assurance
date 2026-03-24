// ============================================================
// DROP-IN FIX: Replace your validateRunId() function in
// upload-reports.html with this entire block.
//
// Root cause: GET /api/v1/monitoring/pc/test-run/recent
// returns  { success, count, test_runs: [...] }
// Old code was checking  data.runs  or  data.data  — both wrong.
// Fix: tries test_runs first, then every key that is an array.
// ============================================================

async function validateRunId() {
  const pcRunId = el('pcRunField').value.trim();
  const validationMsg = el('runIdValidation');   // your status span/div

  if (!pcRunId) {
    validationMsg.textContent = '';
    return;
  }

  validationMsg.innerHTML = '<span style="color:#6b7280">⏳ Validating…</span>';

  try {
    const tok = Auth.getToken();
    const resp = await fetch(`${API_BASE}/monitoring/pc/test-run/recent?limit=50`, {
      headers: { 'Authorization': 'Bearer ' + tok }
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    // ── ROBUST KEY RESOLUTION ──────────────────────────────
    // Try the canonical key first, then fall back to any array
    // value in the response so future backend renames don't break this.
    let runs = null;
    if (Array.isArray(data.test_runs))       runs = data.test_runs;   // ✅ correct key
    else if (Array.isArray(data.runs))       runs = data.runs;
    else if (Array.isArray(data.data))       runs = data.data;
    else if (Array.isArray(data.results))    runs = data.results;
    else {
      // Last resort: find first array value in response object
      for (const val of Object.values(data)) {
        if (Array.isArray(val)) { runs = val; break; }
      }
    }

    if (!runs) {
      console.error('[validateRunId] No array found in response:', data);
      validationMsg.innerHTML = '<span style="color:#ef4444">✗ Unexpected response from server</span>';
      return;
    }

    // ── MATCH against pc_run_id (string compare, trim both sides)
    const match = runs.find(r =>
      String(r.pc_run_id).trim() === String(pcRunId).trim()
    );

    if (match) {
      validationMsg.innerHTML = `<span style="color:#10b981">✓ Valid — ${match.test_name || 'Test'} | Track: ${match.track || '—'} | Status: ${match.status || '—'}</span>`;
      // Store on the element so upload() can read it without another fetch
      el('pcRunField').dataset.runId    = match.run_id    || '';
      el('pcRunField').dataset.lobName  = match.lob_name  || '';
      el('pcRunField').dataset.track    = match.track     || '';
      el('pcRunField').dataset.testName = match.test_name || '';
    } else {
      validationMsg.innerHTML = `<span style="color:#ef4444">✗ PC Run ID ${pcRunId} not found in registered runs</span>`;
      el('pcRunField').dataset.runId = '';
    }

  } catch (err) {
    console.error('[validateRunId] error:', err);
    validationMsg.innerHTML = `<span style="color:#ef4444">✗ Validation error: ${err.message}</span>`;
  }
}

// ── Also update your upload trigger to guard on runId being set ──────────
// In your uploadReports() / processUpload() function, add this at the top:
//
//   const runId = el('pcRunField').dataset.runId;
//   if (!runId) {
//     alert('⚠ Validate a PC Run ID first before uploading.');
//     return;
//   }
//
// Then pass  run_id: runId  in the FormData / JSON body.
