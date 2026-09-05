const state = {
  apiBase: localStorage.getItem('iovApiBase') || 'http://127.0.0.1:5000',
  latestPrediction: null
};

const demoPayload = {
  vehicle_id: "veh_1",
  message_id: "demo-msg-001",
  sequence: 1,
  timestamp: Math.floor(Date.now() / 1000),
  features: {
    posx: 300,
    posy: 120,
    posz: 0,
    spdx: 4.5,
    spdy: 9.8,
    spdz: 2.2,
    aclx: 4.2,
    acly: 8.5,
    aclz: 0.5,
    hedx: 2.4,
    hedy: -2.1,
    hedz: 1.3
  }
};

const el = (id) => document.getElementById(id);

document.addEventListener('DOMContentLoaded', () => {
  el('apiBase').value = state.apiBase;
  el('vehicleJson').value = JSON.stringify(demoPayload, null, 2);

  bindNav();
  bindActions();
  refreshAll();
});

function bindNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.section).classList.add('active');
    });
  });
}

function bindActions() {
  el('saveApiBase').addEventListener('click', () => {
    state.apiBase = el('apiBase').value.trim().replace(/\/$/, '');
    localStorage.setItem('iovApiBase', state.apiBase);
    logActivity(`Saved API base URL: ${state.apiBase}`);
    refreshAll();
  });

  el('refreshAll').addEventListener('click', refreshAll);

  el('loadDemo').addEventListener('click', () => {
    el('vehicleJson').value = JSON.stringify(demoPayload, null, 2);
    logActivity('Loaded demo JSON into input editor.');
  });

  el('formatJson').addEventListener('click', () => {
    try {
      const parsed = JSON.parse(el('vehicleJson').value);
      el('vehicleJson').value = JSON.stringify(parsed, null, 2);
      logActivity('Formatted JSON input.');
    } catch (err) {
      showError(el('predictResult'), `Invalid JSON: ${err.message}`);
      logActivity(`JSON format failed: ${err.message}`);
    }
  });

  el('sendPredict').addEventListener('click', sendPrediction);
  el('fetchTrust').addEventListener('click', fetchTrustById);
}

function normalizeErrorMessage(value) {
  if (value == null) return 'Unknown error';
  if (typeof value === 'string') return value;
  if (value instanceof Error) return value.message;
  if (typeof value === 'object') {
    if (typeof value.message === 'string') return value.message;
    if (typeof value.reason === 'string') return value.reason;
    if (value.error) return normalizeErrorMessage(value.error);
    if (value.code && value.message) return `${value.code}: ${value.message}`;
    return JSON.stringify(value);
  }
  return String(value);
}

async function apiGet(path) {
  const res = await fetch(`${state.apiBase}${path}`);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) throw new Error(normalizeErrorMessage(data));
  return data;
}

async function apiPost(path, payload) {
  const res = await fetch(`${state.apiBase}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) throw new Error(normalizeErrorMessage(data));
  return data;
}

async function refreshAll() {
  await Promise.allSettled([
    loadHealth(),
    loadArchitecture(),
    loadShards(),
    loadChain()
  ]);
}

async function loadHealth() {
  try {
    const data = await apiGet('/api/health');
    el('healthStatus').textContent = data.status || 'ok';
    el('healthMessage').textContent = data.message || 'Backend reachable';
    el('ethereumStatus').textContent = data.ethereum || 'N/A';
    el('healthText').textContent = data.ethereum ? `Ethereum: ${data.ethereum}` : 'Backend online';
    setHealthDot(data.ethereum && String(data.ethereum).includes('disabled') ? 'warn' : 'ok');
  } catch (err) {
    el('healthStatus').textContent = 'offline';
    el('healthMessage').textContent = err.message;
    el('ethereumStatus').textContent = 'unavailable';
    el('healthText').textContent = err.message;
    setHealthDot('error');
    logActivity(`Health check failed: ${err.message}`);
  }
}

async function loadArchitecture() {
  try {
    const data = await apiGet('/api/architecture');
    renderKv(el('architectureBox'), data);
  } catch (err) {
    showError(el('architectureBox'), err.message);
  }
}

async function loadShards() {
  try {
    const data = await apiGet('/api/shards');
    renderShardBars(data.shard_load || {});
    renderObjectTable(el('vehicleShardWrap'), data.vehicle_to_shard || {}, ['vehicle_id', 'shard']);
    renderTransferTable(data.cross_shard_transfers || []);
    el('vehicleCount').textContent = Object.keys(data.vehicle_to_shard || {}).length;
    el('crossShardCount').textContent = (data.cross_shard_transfers || []).length;
  } catch (err) {
    showError(el('transferTableWrap'), err.message);
    showError(el('vehicleShardWrap'), err.message);
  }
}

async function loadChain() {
  try {
    const data = await apiGet('/api/chain');
    el('chainResult').textContent = JSON.stringify(data, null, 2);
    const summary = {};
    Object.entries(data || {}).forEach(([shard, blocks]) => {
      summary[shard] = `${Array.isArray(blocks) ? blocks.length : 0} blocks`;
    });
    renderKv(el('chainSummary'), summary);
  } catch (err) {
    showError(el('chainResult'), err.message);
  }
}

async function sendPrediction() {
  try {
    const payload = JSON.parse(el('vehicleJson').value);
    const data = await apiPost('/api/predict', payload);
    state.latestPrediction = data;
    el('predictResult').textContent = JSON.stringify(data, null, 2);
    el('latestPrediction').textContent = JSON.stringify(data, null, 2);
    if (payload.vehicle_id) el('vehicleIdInput').value = payload.vehicle_id;
    logActivity(`Prediction sent for ${payload.vehicle_id || 'unknown vehicle'} → ${data.prediction?.label || 'no label'}`);
    await refreshAll();
  } catch (err) {
    showError(el('predictResult'), normalizeErrorMessage(err));
    logActivity(`Prediction failed: ${normalizeErrorMessage(err)}`);
  }
}

async function fetchTrustById() {
  const vehicleId = el('vehicleIdInput').value.trim();
  if (!vehicleId) {
    showError(el('trustResult'), 'Enter a vehicle ID first.');
    return;
  }

  try {
    const data = await apiGet(`/api/trust/${encodeURIComponent(vehicleId)}`);
    el('trustResult').textContent = JSON.stringify(data, null, 2);
    logActivity(`Fetched trust status for ${vehicleId}.`);
  } catch (err) {
    showError(el('trustResult'), err.message);
    logActivity(`Trust lookup failed for ${vehicleId}: ${err.message}`);
  }
}

function renderKv(container, data) {
  container.innerHTML = '';
  Object.entries(data || {}).forEach(([k, v]) => {
    const item = document.createElement('div');
    item.className = 'kv-item';
    item.innerHTML = `<span class="k">${escapeHtml(k)}</span><span class="v">${escapeHtml(String(v))}</span>`;
    container.appendChild(item);
  });
}

function renderShardBars(loadMap) {
  const container = el('shardBars');
  container.innerHTML = '';
  const values = Object.values(loadMap || {});
  const max = Math.max(1, ...values);

  if (!values.length) {
    container.innerHTML = '<div class="kv-item"><span class="v">No shard data yet.</span></div>';
    return;
  }

  Object.entries(loadMap).forEach(([shard, value]) => {
    const row = document.createElement('div');
    row.className = 'bar-row';
    const percent = Math.round((value / max) * 100);
    row.innerHTML = `
      <div class="bar-head">
        <span>${escapeHtml(shard)}</span>
        <span>${value}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${percent}%"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderTransferTable(transfers) {
  const wrap = el('transferTableWrap');
  if (!transfers.length) {
    wrap.innerHTML = '<div class="kv-item"><span class="v">No cross-shard transfers yet.</span></div>';
    return;
  }

  const rows = transfers.map(t => `
    <tr>
      <td>${escapeHtml(String(t.vehicle_id || ''))}</td>
      <td>${escapeHtml(String(t.from_shard || ''))}</td>
      <td>${escapeHtml(String(t.to_shard || ''))}</td>
      <td>${escapeHtml(String(t.reason || ''))}</td>
      <td>${escapeHtml(String(t.zone ?? ''))}</td>
      <td>${escapeHtml(String(t.trust_bucket ?? ''))}</td>
    </tr>
  `).join('');

  wrap.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Vehicle</th>
          <th>From</th>
          <th>To</th>
          <th>Reason</th>
          <th>Zone</th>
          <th>Trust Bucket</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderObjectTable(wrap, obj, headers) {
  const entries = Object.entries(obj || {});
  if (!entries.length) {
    wrap.innerHTML = '<div class="kv-item"><span class="v">No data yet.</span></div>';
    return;
  }

  const rows = entries.map(([k, v]) => `
    <tr>
      <td>${escapeHtml(String(k))}</td>
      <td>${escapeHtml(String(v))}</td>
    </tr>
  `).join('');

  wrap.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>${escapeHtml(headers[0])}</th>
          <th>${escapeHtml(headers[1])}</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function setHealthDot(mode) {
  const dot = el('healthDot');
  dot.className = 'status-dot';
  dot.classList.add(`status-${mode}`);
}

function showError(target, message) {
  if ('textContent' in target) {
    target.textContent = `Error: ${message}`;
  } else {
    target.innerHTML = `<div class="kv-item"><span class="v">Error: ${escapeHtml(message)}</span></div>`;
  }
}

function logActivity(message) {
  const row = document.createElement('div');
  row.className = 'log-item';
  row.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  const box = el('activityLog');
  box.prepend(row);
  while (box.children.length > 40) box.removeChild(box.lastChild);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}