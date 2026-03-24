// =============================================================================
// FRONTEND PATCH — upload-reports.html
// Replace the entire fetchFromPC() function with this.
//
// Key change: sends pc_config_id (from loaded config) instead of
// pc_url / pc_domain / username / password.
// Backend resolves all credentials itself.
// =============================================================================

async function fetchFromPC() {
  const pcRunId  = el('pcRunField').value.trim();
  const track    = el('trackField').value;
  const project  = el('pcProject').value;       // display name e.g. "DT - CDV3"
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

  const tok = localStorage.getItem('session_token');

  // Helper — uses your existing apiFetch if available, otherwise raw fetch
  async function callApi(url, options = {}) {
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
      const msg = data.detail
        ? (Array.isArray(data.detail)
            ? data.detail.map(e => `${(e.loc || []).slice(-1)[0]}: ${e.msg}`).join(', ')
            : String(data.detail))
        : `HTTP ${resp.status}`;
      throw new Error(msg);
    }
    return data;
  }

  try {
    // ── STEP 1: Load PC config to get pc_config_id ────────────────────────
    log(`Loading PC config for project: ${project}...`);

    const configData = await callApi(
      `${API_BASE}/nft/config/pc/${encodeURIComponent(lobName)}`
      // API_BASE should already be defined at top of your script,
      // e.g. const API_BASE = 'http://localhost:8000/api/v1';
    );

    // Response: { success, lob_name, total, config: [...] }
    const configs = configData.config
                 || configData.configs
                 || configData.data
                 || [];

    // Match by display_name ("DT - CDV3") first, then project_name
    const pcConfig = configs.find(c => c.display_name  === project)
                  || configs.find(c => c.project_name   === project)
                  || configs.find(c => c.pc_project      === project)
                  || configs[0];

    if (!pcConfig) {
      throw new Error(
        `No PC configuration found for project "${project}" under LOB "${lobName}". ` +
        `Configure it in Admin → PC Config first.`
      );
    }

    const pcConfigId = pcConfig.pc_config_id || pcConfig.config_id;
    if (!pcConfigId) {
      throw new Error('PC config found but has no pc_config_id. Check DB schema.');
    }

    log(`✓ Config matched: ${pcConfig.display_name || pcConfig.project_name} (ID: ${pcConfigId})`);

    // ── STEP 2: Register test run if not already done ─────────────────────
    let runId = el('pcRunField').dataset.runId || '';
    if (!runId) {
      log('Registering test run in Oracle...');
      try {
        const reg = await callApi(`${API_BASE}/monitoring/pc/test-run/register`, {
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
        el('pcRunField').dataset.runId = runId;
      } catch (e) {
        log(`⚠ Run registration warning: ${e.message}`);
      }
    } else {
      log(`Using existing Run ID: ${runId}`);
    }

    // ── STEP 3: Fetch results — send pc_config_id, no passwords ──────────
    log(`Connecting to Performance Center for PC Run ID: ${pcRunId}...`);

    const payload = {
      run_id:           runId || `FETCH_${pcRunId}`,
      pc_run_id:        pcRunId,
      lob_name:         lobName,
      track:            track,
      pc_config_id:     pcConfigId,   // ← backend resolves all creds from this
      test_set_name:    testName || '',
      test_instance_id: null,
      test_name:        testName || '',
    };

    const d = await callApi(`${API_BASE}/monitoring/pc/fetch-results`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    // ── STEP 4: Show results ──────────────────────────────────────────────
    log(`✓ Connected to Performance Center`);
    if (d.test_status)      log(`Test status: ${d.test_status}`);
    if (d.collation_status) log(`Collation:   ${d.collation_status}`);

    const txCount = d.total_transactions
                 || d.transactions?.length
                 || d.passed_transactions
                 || 0;
    log(`✓ ${txCount} transactions processed`);
    log(`✓ Saved to Oracle`);

    showResults(
      [
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
    if (typeof el === 'function' && el('fetchStatus')) {
      el('fetchStatus').innerHTML = alertHtml('danger', '✗ Fetch failed: ' + e.message);
      show('fetchStatus');
    }
    console.error('fetchFromPC error:', e);
  }

  btn.disabled = false;
  btn.textContent = '🔌 Fetch from Performance Center';
}
