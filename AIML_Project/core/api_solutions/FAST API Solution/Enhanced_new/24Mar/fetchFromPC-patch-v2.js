// ============================================================
// PATCH — replace ONLY the config-loading block inside
// your fetchFromPC() function.
// Two fixes:
//   1. Use your existing base URL variable (PC_API / API_BASE)
//   2. Match config using display_name OR project_name
// ============================================================

// ── Find your base URL variable at the top of your file ────
// It will be one of:
//   const API_BASE = 'http://localhost:8000/api/v1';
//   const PC_API   = `${API_BASE}/monitoring/pc`;
//   const NFT_API  = `${API_BASE}/nft`;
// Check the top of your upload-reports.html <script> block.
// In the patch below, replace NFT_CONFIG_API with whatever
// resolves to  http://localhost:8000/api/v1

// ── REPLACE this block in fetchFromPC() ─────────────────────
//
//   OLD (broken):
//     const configData = await apiFetch(`${API_BASE}/nft/config/pc/...`);
//
//   NEW (below) — paste this in place of the entire
//   "STEP 1: Load stored PC config" try/catch block:
// ─────────────────────────────────────────────────────────────

    // ── STEP 1: Load stored PC config for this LOB ───────────
    log(`Loading PC config for project: ${project}...`);
    let pcConfig = null;
    try {
      // Use your file's existing base URL variable.
      // From your file it is likely one of these — pick the one
      // that already works for other calls:
      //   API_BASE  →  'http://localhost:8000/api/v1'
      //   NFT_API   →  `${API_BASE}/nft`
      //   PC_API    →  `${API_BASE}/monitoring/pc`
      //
      // The endpoint is:  GET /api/v1/nft/config/pc/{lob_name}
      // So the call should be:
      const configUrl = `${API_BASE}/nft/config/pc/${encodeURIComponent(lobName)}`;
      //                   ^^^^^^^^ replace API_BASE with your variable if needed

      const tok = localStorage.getItem('session_token');
      const resp = await fetch(configUrl, {
        headers: { 'Authorization': 'Bearer ' + tok }
      });
      const configData = await resp.json();

      // Response shape confirmed from Network tab:
      // { "success": true, "lob_name": "...", "total": 1, "config": [...] }
      const configs = configData.config      // ← correct key from Network tab
                   || configData.configs
                   || configData.data
                   || [];

      // Match by display_name first (what the dropdown shows: "DT - CDV3")
      // then fall back to project_name ("GTS_BE13A_PTE")
      // then fall back to first config for this LOB
      pcConfig = configs.find(c => c.display_name === project)
              || configs.find(c => c.project_name === project)
              || configs.find(c => c.pc_project    === project)
              || configs[0];

      if (pcConfig) {
        log(`✓ Config matched: ${pcConfig.display_name || pcConfig.project_name} (ID: ${pcConfig.pc_config_id})`);
      }

    } catch (e) {
      log(`⚠ Could not load PC config: ${e.message}`);
    }

    if (!pcConfig) {
      throw new Error(
        `No PC configuration found for project "${project}" under LOB "${lobName}". ` +
        `Configure it in Admin → PC Config first.`
      );
    }

    // ── Build credentials from confirmed field names ──────────
    // Field names confirmed from Network tab response:
    //   pc_url, pc_port, domain, project_name, username, pass_env_var
    //
    // NOTE: pass_env_var = "PC_DT_PASSWORD" means the password is stored
    // as an environment variable on the server, not returned directly.
    // The backend fetch-results endpoint should resolve it internally.
    // So we send pass_env_var and let backend handle it,
    // OR the backend already reads it from config by pc_config_id.
    //
    // Check your fetch_pc_results route (Image 3 from earlier):
    // it calls  pc_db.get_master_run_by_pc_id  and builds the client itself.
    // So the SIMPLEST fix is to send pc_config_id and let the backend
    // look up credentials — if the model supports it.
    //
    // If not, send what we have:

    const fetchPayload = {
      run_id:           runId || `FETCH_${pcRunId}`,
      pc_run_id:        pcRunId,
      lob_name:         lobName,
      track:            track,

      // Confirmed field names from Network response:
      pc_url:           pcConfig.pc_url      || '',
      pc_port:          pcConfig.pc_port      || 8080,
      pc_domain:        pcConfig.domain       || pcConfig.pc_domain || 'DEFAULT',
      pc_project:       pcConfig.project_name || pcConfig.pc_project || project,
      username:         pcConfig.username     || '',

      // Password: stored as env var name on server (pass_env_var = "PC_DT_PASSWORD")
      // The backend should resolve this — send the env var name or empty string.
      // If your PCConnectionRequest has a pass_env_var field, send that instead.
      password:         pcConfig.password     || pcConfig.pass_env_var || '',

      test_set_name:    testName || pcConfig.test_set_name || '',
      test_instance_id: null,
      test_name:        testName || '',
    };

    log(`URL: ${fetchPayload.pc_url}, Domain: ${fetchPayload.pc_domain}, Project: ${fetchPayload.pc_project}`);

    // ── Guard checks ─────────────────────────────────────────
    if (!fetchPayload.pc_url) {
      throw new Error('PC URL missing from config. Check Admin → PC Config.');
    }
    if (!fetchPayload.username) {
      throw new Error('PC username missing from config. Check Admin → PC Config.');
    }

    // ── STEP 3: Call fetch-results ────────────────────────────
    log(`Connecting to Performance Center for PC Run ID: ${pcRunId}...`);
    const tok2 = localStorage.getItem('session_token');
    const fetchResp = await fetch(`${API_BASE}/monitoring/pc/fetch-results`, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + tok2,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(fetchPayload)
    });
    const d = await fetchResp.json();
    if (!fetchResp.ok) {
      const msg = d.detail
        ? (Array.isArray(d.detail)
            ? d.detail.map(e => `${(e.loc||[]).join('.')}: ${e.msg}`).join(', ')
            : String(d.detail))
        : `HTTP ${fetchResp.status}`;
      throw new Error(msg);
    }

    // ── Rest of your existing success handling (unchanged) ────
    log(`✓ Connected to Performance Center`);
    if (d.test_status)      log(`Test status: ${d.test_status}`);
    if (d.collation_status) log(`Collation:   ${d.collation_status}`);
    const txCount = d.total_transactions || d.transactions?.length || 0;
    log(`✓ ${txCount} transactions processed`);
    log(`✓ Saved to Oracle`);

    showResults([
      { t: 'PC_TEST_RUNS',           n: 1 },
      { t: 'LR_TRANSACTION_RESULTS', n: txCount },
    ],
    d.success ? 'success' : 'warning',
    d.success
      ? `✓ PC results fetched and stored. Run ID: ${d.run_id || runId}`
      : `⚠ Partial results: ${d.message || 'Check PC connection settings'}`
    );

// ============================================================
// IMPORTANT NOTE on password:
// Your config returns  pass_env_var: "PC_DT_PASSWORD"
// This means the password is an env variable on the server.
// Two options:
//
// Option A (recommended): modify PCConnectionRequest to accept
//   pass_env_var: Optional[str]
// and in fetch_pc_results, do:
//   password = os.environ.get(request.pass_env_var, '') if request.pass_env_var else request.password
//
// Option B: modify fetch_pc_results to load creds by pc_config_id:
//   add  pc_config_id: Optional[int]  to PCConnectionRequest
//   if pc_config_id is provided, load config from DB and get creds there
//   (backend already has this data — no need to send creds from frontend)
// ============================================================
