// ============================================================
// DROP-IN FIX: Replace your fetchFromPC() function in
// upload-reports.html with this entire block.
//
// ROOT CAUSE:
//   POST /api/v1/monitoring/pc/fetch-results expects:
//     pc_url (required str), pc_domain (required str),
//     pc_port (int), username (required str), password (required str)
//   But the frontend was sending pc_url:"" and pc_domain:""
//   and not sending username/password at all → 422.
//
// FIX:
//   Step 1 — GET /api/v1/nft/config/pc/{lob_name}
//            to load stored pc_url, pc_domain, pc_port,
//            username, password for the selected project.
//   Step 2 — Merge those into the fetch-results payload.
//   Step 3 — Call POST /api/v1/monitoring/pc/fetch-results.
// ============================================================

async function fetchFromPC() {
  const pcRunId  = el('pcRunField').value.trim();
  const track    = el('trackField').value;
  const project  = el('pcProject').value;          // e.g. "DT - CDV3"
  const lobName  = el('lobField').value;
  const testName = el('testNameField').value.trim();

  if (!pcRunId || !track) {
    alert('⚠ PC Run ID and Track are required.');
    return;
  }
  if (!project) {
    alert('⚠ Select a PC Project before fetching.');
    return;
  }

  const btn = el('btnFetch');
  btn.disabled = true;
  btn.textContent = '⏳ Fetching...';
  hide('uploadResults');
  show('fetchLog');
  el('fetchLogBox').innerHTML = '';

  function log(msg) {
    const d = document.createElement('div');
    d.textContent = '[' + new Date().toTimeString().slice(0, 8) + '] ' + msg;
    el('fetchLogBox').appendChild(d);
    el('fetchLogBox').scrollTop = el('fetchLogBox').scrollHeight;
  }

  try {
    // ── STEP 1: Load stored PC config for this LOB ──────────────────────────
    // GET /api/v1/nft/config/pc/{lob_name}
    // Returns array of PC configs; find the one matching selected project.
    log(`Loading PC config for project: ${project}...`);
    let pcConfig = null;
    try {
      const configData = await apiFetch(`${API_BASE}/nft/config/pc/${encodeURIComponent(lobName)}`);
      // Response is { configs: [...] } or an array directly
      const configs = configData.configs || configData.data || configData || [];
      // Match by project name — pc_project field
      pcConfig = configs.find(c =>
        c.pc_project === project ||
        `${c.lob_name} - ${c.track_name}` === project ||
        c.project_name === project
      ) || configs[0];   // fall back to first config for this LOB
    } catch (e) {
      log(`⚠ Could not load PC config: ${e.message}`);
      // Don't abort — some backends embed creds differently; try anyway
    }

    if (!pcConfig) {
      throw new Error(
        `No PC configuration found for project "${project}" under LOB "${lobName}". ` +
        `Configure it in Admin → PC Config first.`
      );
    }

    log(`✓ Config loaded — URL: ${pcConfig.pc_url || pcConfig.base_url || '(stored)'}, Domain: ${pcConfig.pc_domain || pcConfig.domain || 'DEFAULT'}`);

    // ── STEP 2: Register test run if not already done ───────────────────────
    let runId = el('pcRunField').dataset.runId || '';   // set by validateRunId()
    if (!runId) {
      log('Registering test run in Oracle...');
      try {
        const reg = await apiFetch(`${API_BASE}/monitoring/pc/test-run/register`, {
          method: 'POST',
          body: JSON.stringify({
            lob_name:  lobName,
            track:     track,
            pc_run_id: pcRunId,
            test_name: testName || `Fetch_${pcRunId}`,
          })
        });
        runId = reg.run_id || reg.master_run_id || '';
        log(`✓ Run registered. Master Run ID: ${runId}`);
        // Cache it so upload tab can also use it
        el('pcRunField').dataset.runId = runId;
      } catch (e) {
        log(`⚠ Run registration warning: ${e.message}`);
      }
    } else {
      log(`Using existing Run ID: ${runId}`);
    }

    // ── STEP 3: Call fetch-results with FULL payload ─────────────────────────
    log(`Connecting to Performance Center for PC Run ID: ${pcRunId}...`);

    const payload = {
      run_id:           runId || `FETCH_${pcRunId}`,
      pc_run_id:        pcRunId,
      lob_name:         lobName,
      track:            track,

      // Credentials from stored config — these are what the model requires
      pc_url:           pcConfig.pc_url    || pcConfig.base_url  || '',
      pc_port:          pcConfig.pc_port   || pcConfig.port       || 8080,
      pc_domain:        pcConfig.pc_domain || pcConfig.domain     || 'DEFAULT',
      pc_project:       pcConfig.pc_project|| pcConfig.project_name || project,
      username:         pcConfig.username  || pcConfig.pc_username || '',
      password:         pcConfig.password  || pcConfig.pc_password || '',

      // Optional fields
      test_set_name:    testName || pcConfig.test_set_name || '',
      test_instance_id: null,
      test_name:        testName || '',
    };

    // Guard — if username is still empty after config load, stop with clear message
    if (!payload.username) {
      throw new Error(
        'PC username not found in stored config. ' +
        'Open Admin → PC Config, edit the project, and ensure username & password are saved.'
      );
    }
    if (!payload.pc_url) {
      throw new Error(
        'PC URL not found in stored config. ' +
        'Open Admin → PC Config and confirm the PC Base URL is saved for this project.'
      );
    }

    const d = await apiFetch(`${API_BASE}/monitoring/pc/fetch-results`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

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

  } catch (e) {
    log(`✗ Error: ${e.message}`);
    el('fetchStatus').innerHTML = alertHtml('danger', '✗ Fetch failed: ' + e.message);
    show('fetchStatus');
    console.error('fetchFromPC error:', e);
  }

  btn.disabled = false;
  btn.textContent = '🔌 Fetch from Performance Center';
}


// ============================================================
// ALSO: Update apiFetch() if it doesn't already handle
// non-OK responses gracefully. Replace or confirm this exists:
// ============================================================
async function apiFetch(url, options = {}) {
  const tok = Auth.getToken();    // or localStorage.getItem('session_token')
  const resp = await fetch(url, {
    ...options,
    headers: {
      'Authorization': 'Bearer ' + tok,
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    // Surface the detail message so log() shows something meaningful
    const msg = data.detail
      ? (Array.isArray(data.detail)
          ? data.detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', ')
          : String(data.detail))
      : `HTTP ${resp.status}`;
    throw new Error(msg);
  }
  return data;
}
