
// ═══ STATE ════════════════════════════════════════════
let apiBase = 'http://localhost:8000';
let jwtToken = '';
let webhookLog = [];        // local entries (simulate + in-dashboard actions), persisted in localStorage
let dbWebhooks = [];         // real webhook events fetched from /admin/webhooks/
let allUsers = [], allInvoices = [], allSubs = [], allPayments = [], allPlans = [];

// Server-side pagination state per table. Filter/sort still apply client-side
// to the current page.
const PAGE_SIZE = 50;
const pager = {
  users:    { offset: 0, hasNext: false },
  subs:     { offset: 0, hasNext: false },
  invoices: { offset: 0, hasNext: false },
  payments: { offset: 0, hasNext: false },
};
let pendingCancelSubId = null;

// On load — restore session if token exists
window.onload = () => {
  // Restore webhook log from localStorage
  try {
    const savedLog = localStorage.getItem('billing_webhook_log');
    if (savedLog) webhookLog = JSON.parse(savedLog);
  } catch { webhookLog = []; }

  const saved = localStorage.getItem('billing_token');
  const savedBase = localStorage.getItem('billing_base');
  if (saved && savedBase) {
    jwtToken = saved;
    apiBase = savedBase;
    document.getElementById('login-base-url').value = savedBase;
    document.getElementById('api-url-display').textContent = savedBase.replace(/^https?:\/\//, '');
    document.getElementById('tester-base').value = savedBase;
    document.getElementById('tester-token').value = saved;
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    renderWebhooks();
    loadAllData();
  }
};

// ═══ LOGIN ════════════════════════════════════════════
async function doLogin() {
  const btn = document.getElementById('login-btn');
  const errEl = document.getElementById('login-error');
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  apiBase = (document.getElementById('login-base-url').value.trim() || 'http://localhost:8000').replace(/\/$/, '');

  if (!email || !password) { errEl.textContent = 'Email and password are required.'; return; }
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Signing in…';
  errEl.textContent = '';

  try {
    const r = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await r.json().catch(() => ({}));

    if (!r.ok) { errEl.textContent = data.detail || `Login failed (${r.status})`; return; }

    jwtToken = data.access_token || data.token || '';
    if (!jwtToken) { errEl.textContent = 'No token returned — check API response.'; return; }

    localStorage.setItem('billing_token', jwtToken);
    localStorage.setItem('billing_base', apiBase);

    // Boot UI
    document.getElementById('api-url-display').textContent = apiBase.replace(/^https?:\/\//,'');
    document.getElementById('logged-in-as').textContent = email;
    document.getElementById('tester-base').value = apiBase;
    document.getElementById('tester-token').value = jwtToken;

    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');

    loadAllData();
  } catch(e) {
    errEl.textContent = 'Connection refused — is the API running at ' + apiBase + '?';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sign in';
  }
}

function doLogout() {
  jwtToken = '';
  allUsers = []; allInvoices = []; allSubs = []; allPayments = []; webhookLog = [];
  localStorage.removeItem('billing_token');
  localStorage.removeItem('billing_base');
  localStorage.removeItem('billing_webhook_log');
  document.getElementById('app').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('login-password').value = '';
  document.getElementById('login-error').textContent = '';
}

// ═══ API HELPERS ══════════════════════════════════════
function ah() { return { 'Authorization': `Bearer ${jwtToken}`, 'Content-Type': 'application/json' }; }

async function apiFetch(path, opts = {}) {
  const r = await fetch(`${apiBase}${path}`, { headers: ah(), ...opts });
  if (r.status === 401) { doLogout(); throw new Error('Session expired — please log in again'); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `${r.status} ${r.statusText}`);
  return data;
}

function toArray(data) {
  if (Array.isArray(data)) return data;
  // Handle paginated shapes like {items:[...]} or {subscriptions:[...]}
  for (const key of ['items','data','results','subscriptions','payments','invoices','users']) {
    if (data[key] && Array.isArray(data[key])) return data[key];
  }
  return [];
}

// ═══ DATA LOADING ════════════════════════════════════
async function loadAllData() {
  await Promise.all([loadSubscriptions(), loadInvoices(), loadPayments(), loadUsers(), loadWebhooks()]);
  renderDashboard();
}

async function loadWebhooks() {
  try {
    const data = await apiFetch('/admin/webhooks/?limit=200');
    dbWebhooks = toArray(data);
  } catch {
    dbWebhooks = [];
  }
  renderWebhooks();
}

// ═══ PLANS ════════════════════════════════════════════
async function loadPlans() {
  try {
    const data = await apiFetch('/admin/plans/');
    allPlans = toArray(data);
  } catch(e) {
    showToast('Plans: ' + e.message, 'error');
    allPlans = [];
  }
  renderPlans();
}

function renderPlans() {
  const tb = document.getElementById('plans-tbody');
  if (!allPlans.length) { tb.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">▣</div>No plans</div></td></tr>'; return; }
  tb.innerHTML = allPlans.map(p => {
    const prices = (p.prices || []).map(pr => fmtAmt(pr.amount, pr.currency)).join(' · ') || '—';
    return `<tr>
      <td style="font-size:12px">${esc(p.name)}</td>
      <td style="font-size:12px;color:var(--muted)">${Number(p.api_limit).toLocaleString()}</td>
      <td style="font-size:11px">${prices}</td>
      <td>${mkbadge(p.is_active ? 'active' : 'canceled')}</td>
      <td>
        <button class="btn" style="font-size:10px;padding:4px 8px" onclick="openPlanForm('${p.id}')">Edit</button>
        <button class="btn btn-danger" style="font-size:10px;padding:4px 8px" onclick="deletePlan('${p.id}')">Delete</button>
      </td>
    </tr>`;
  }).join('');
}

function planPrice(plan, cur) {
  const pr = (plan.prices || []).find(x => (x.currency || '').toUpperCase() === cur);
  return pr ? pr.amount : '';
}

function openPlanForm(planId) {
  const plan = planId ? allPlans.find(p => String(p.id) === String(planId)) : null;
  document.getElementById('plan-form-title').textContent = plan ? 'Edit Plan' : 'New Plan';
  document.getElementById('plan-form-id').value = plan ? plan.id : '';
  document.getElementById('plan-form-name').value = plan ? plan.name : '';
  document.getElementById('plan-form-limit').value = plan ? plan.api_limit : '';
  document.getElementById('plan-form-usd').value = plan ? planPrice(plan, 'USD') : '';
  document.getElementById('plan-form-rub').value = plan ? planPrice(plan, 'RUB') : '';
  document.getElementById('plan-form-active').checked = plan ? plan.is_active !== false : true;
  openModal('plan-form');
}

async function savePlan() {
  const id = document.getElementById('plan-form-id').value;
  const name = document.getElementById('plan-form-name').value.trim();
  const limit = parseInt(document.getElementById('plan-form-limit').value, 10);
  const usd = document.getElementById('plan-form-usd').value;
  const rub = document.getElementById('plan-form-rub').value;
  const active = document.getElementById('plan-form-active').checked;

  if (!name) { showToast('Name is required', 'error'); return; }
  if (!Number.isFinite(limit)) { showToast('API limit must be a number', 'error'); return; }

  const prices = [];
  if (usd !== '') prices.push({ currency: 'USD', amount: Number(usd) });
  if (rub !== '') prices.push({ currency: 'RUB', amount: Number(rub) });
  if (!id && !prices.length) { showToast('Set at least one price', 'error'); return; }

  try {
    if (id) {
      const body = { name, api_limit: limit, is_active: active };
      if (prices.length) body.prices = prices;
      await apiFetch(`/admin/plans/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      showToast('Plan updated ✓', 'ok');
    } else {
      await apiFetch('/admin/plans/', { method: 'POST', body: JSON.stringify({ name, api_limit: limit, is_active: active, prices }) });
      showToast('Plan created ✓', 'ok');
    }
    closeModalForce();
    await loadPlans();
  } catch(e) {
    showToast('Save failed: ' + e.message, 'error');
  }
}

async function deletePlan(id) {
  if (!confirm('Delete this plan? This cannot be undone.')) return;
  try {
    await apiFetch(`/admin/plans/${id}`, { method: 'DELETE' });
    showToast('Plan deleted ✓', 'ok');
    await loadPlans();
  } catch(e) {
    showToast('Delete failed: ' + e.message, 'error');
  }
}

function pageQuery(name) {
  return `?limit=${PAGE_SIZE}&offset=${pager[name].offset}`;
}

async function loadUsers() {
  try {
    const data = await apiFetch('/admin/subscriptions/subscribers' + pageQuery('users'));
    allUsers = toArray(data);
    pager.users.hasNext = allUsers.length === PAGE_SIZE;
    applyView('users');
  } catch {
    // endpoint may not exist yet
    renderUsers([]);
  }
  renderPager('users');
}

async function loadSubscriptions() {
  try {
    const data = await apiFetch('/admin/subscriptions/' + pageQuery('subs'));
    allSubs = toArray(data);
    pager.subs.hasNext = allSubs.length === PAGE_SIZE;
    applyView('subs');
  } catch(e) {
    showToast('Subscriptions: ' + e.message, 'error');
    renderSubscriptions([]);
  }
  renderPager('subs');
}

async function loadInvoices() {
  try {
    const data = await apiFetch('/admin/invoices/' + pageQuery('invoices'));
    allInvoices = toArray(data);
    pager.invoices.hasNext = allInvoices.length === PAGE_SIZE;
    applyView('invoices');
  } catch(e) {
    showToast('Invoices: ' + e.message, 'error');
    renderInvoices([]);
  }
  renderPager('invoices');
}

async function loadPayments() {
  try {
    const data = await apiFetch('/admin/payments/' + pageQuery('payments'));
    allPayments = toArray(data);
    pager.payments.hasNext = allPayments.length === PAGE_SIZE;
    applyView('payments');
  } catch(e) {
    showToast('Payments: ' + e.message, 'error');
    renderPayments([]);
  }
  renderPager('payments');
}

const pagerLoaders = { users: loadUsers, subs: loadSubscriptions, invoices: loadInvoices, payments: loadPayments };

function renderPager(name) {
  const el = document.getElementById('pager-' + name);
  if (!el) return;
  const p = pager[name];
  // Hide the pager entirely when there's only a single page.
  if (p.offset === 0 && !p.hasNext) { el.innerHTML = ''; return; }
  const page = Math.floor(p.offset / PAGE_SIZE) + 1;
  el.innerHTML =
    `<button class="btn" ${p.offset === 0 ? 'disabled' : ''} onclick="changePage('${name}',-1)">‹ Prev</button>` +
    `<span style="font-size:11px;color:var(--muted)">Page ${page}</span>` +
    `<button class="btn" ${p.hasNext ? '' : 'disabled'} onclick="changePage('${name}',1)">Next ›</button>`;
}

function changePage(name, dir) {
  const p = pager[name];
  const next = p.offset + dir * PAGE_SIZE;
  if (next < 0) return;
  p.offset = next;
  pagerLoaders[name]();
}

function refreshCurrentTab() {
  const t = document.getElementById('page-title').textContent;
  if (t === 'Dashboard') loadAllData();
  else if (t === 'Subscribers') loadUsers();
  else if (t === 'Subscriptions') loadSubscriptions();
  else if (t === 'Invoices') loadInvoices();
  else if (t === 'Payments') loadPayments();
  else if (t === 'Plans') loadPlans();
  else if (t === 'Webhooks') loadWebhooks();
}

// ═══ DASHBOARD ════════════════════════════════════════
function renderDashboard() {
  const active = allSubs.filter(s => s.status === 'active').length;
  const failed = allPayments.filter(p => p.status === 'failed').length;
  const open = allInvoices.filter(i => i.status === 'open').length;

  // Sum pending amounts per currency — mixing USD and RUB into one number is wrong.
  const pendingByCur = {};
  allInvoices.filter(i => i.status === 'open').forEach(i => {
    const cur = (i.currency || 'USD').toUpperCase();
    pendingByCur[cur] = (pendingByCur[cur] || 0) + Number(i.amount || 0);
  });
  const pendingText = Object.entries(pendingByCur)
    .map(([cur, amt]) => fmtAmt(amt, cur))
    .join(' + ') || fmtAmt(0, 'USD');

  document.getElementById('stat-active').textContent = active;
  document.getElementById('stat-active-sub').textContent = allSubs.filter(s=>s.status==='incomplete').length + ' incomplete';
  document.getElementById('stat-failed').textContent = failed;
  document.getElementById('stat-failed-sub').textContent = allPayments.filter(p=>p.status==='pending').length + ' pending';
  document.getElementById('stat-open').textContent = open;
  document.getElementById('stat-open-sub').textContent = pendingText + ' pending';
  document.getElementById('stat-total').textContent = allSubs.length;
  document.getElementById('stat-total-sub').textContent = allPayments.filter(p=>p.status==='succeeded').length + ' succeeded';

  const recent = [...allPayments].slice(-5).reverse();
  document.getElementById('dash-payments-table').innerHTML = recent.length ? `
    <table><thead><tr><th>ID</th><th>Invoice</th><th>Provider</th><th>Status</th><th>Created</th></tr></thead>
    <tbody>${recent.map(p=>`
      <tr>
        <td class="id-cell" title="${p.id}">${shortId(p.id)}</td>
        <td class="id-cell" title="${p.invoice_id}">${shortId(p.invoice_id)}</td>
        <td style="font-size:12px;color:var(--muted)">${p.provider||'—'}</td>
        <td>${mkbadge(p.status)}</td>
        <td style="color:var(--muted);font-size:12px">${fmtDate(p.created_at)}</td>
      </tr>`).join('')}
    </tbody></table>` :
    '<div class="empty-state"><div class="empty-icon">◆</div>No payments yet</div>';

  const recentWH = allWebhookEntries().slice(0, 5);
  document.getElementById('dash-webhook-table').innerHTML = recentWH.length ? `<div>
    ${recentWH.map(w=>`
      <div class="log-entry">
        <span class="log-time">${(w.time||'').split(' ')[1]||w.time}</span>
        <div style="flex:1"><div class="log-event">${w.event}</div><div class="log-payload">${w.resource}</div></div>
        <span>${mkbadge(w.status)}</span>
      </div>`).join('')}</div>` :
    '<div class="empty-state"><div class="empty-icon">⟳</div>No activity yet</div>';
}

// ═══ RENDER TABLES ════════════════════════════════════
function renderUsers(users) {
  const tb = document.getElementById('users-tbody');
  if (!users.length) { tb.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">◎</div>No subscribers found</div></td></tr>'; return; }
  tb.innerHTML = users.map(u=>`<tr>
    <td class="id-cell" title="${u.id}">${short(u.id)}</td>
    <td>${esc(u.user.email)}</td>
    <td style="font-size:11px;color:var(--muted)">${u.role||'user'}</td>
    <td>${mkbadge(u.is_active!==false?'active':'canceled')}</td>
    <td style="color:var(--muted);font-size:11px">${fmtDate(u.created_at)}</td>
    <td>${esc(u.plan?.name)}</td>
  </tr>`).join('');
}

// ═══ SORT + FILTER CONTROLLER ════════════════════════
// Each table has: a data source, a render fn, sortable column accessors,
// and a filter predicate. State (current sort + active filters) lives on
// the config object so it survives data reloads.
const views = {
  users: {
    panel: 'tab-subscribers', data: () => allUsers, render: renderUsers,
    sort: null, dir: 1, text: '',
    cols: { id: r => r.id, email: r => r.user?.email || '', role: r => r.role || 'user',
            created: r => r.created_at, plan: r => r.plan?.name || '' },
    matches: (r, st) => !st.text ||
      (r.user?.email || '').toLowerCase().includes(st.text) || String(r.id).includes(st.text),
  },
  subs: {
    panel: 'tab-subscriptions', data: () => allSubs, render: renderSubscriptions,
    sort: null, dir: 1, status: '', text: '',
    cols: { id: r => r.id, user: r => r.user_id, plan: r => r.plan?.name || r.plan_id || '',
            status: r => r.status, period: r => r.current_period_end },
    matches: (r, st) => (!st.status || r.status === st.status) &&
      (!st.text || matchesText(st.text, r.id, r.user_id, r.plan?.name, r.plan_id)),
  },
  invoices: {
    panel: 'tab-invoices', data: () => allInvoices, render: renderInvoices,
    sort: null, dir: 1, status: '', text: '',
    cols: { id: r => r.id, sub: r => r.subscription_id, amount: r => Number(r.amount || 0),
            currency: r => (r.currency || '').toUpperCase(), status: r => r.status, due: r => r.due_date },
    matches: (r, st) => (!st.status || r.status === st.status) &&
      (!st.text || matchesText(st.text, r.id, r.subscription_id)),
  },
  payments: {
    panel: 'tab-payments', data: () => allPayments, render: renderPayments,
    sort: null, dir: 1, status: '', provider: '', text: '',
    cols: { id: r => r.id, invoice: r => r.invoice_id, provider: r => r.provider || '',
            status: r => r.status, created: r => r.created_at },
    matches: (r, st) => (!st.status || r.status === st.status) && (!st.provider || r.provider === st.provider) &&
      (!st.text || matchesText(st.text, r.id, r.invoice_id, r.provider)),
  },
};

// Case-insensitive substring match of `q` against any of the given fields.
function matchesText(q, ...fields) {
  return fields.some(f => String(f || '').toLowerCase().includes(q));
}

function cmpValues(a, b) {
  if (a == null && b == null) return 0;
  if (a == null) return -1;
  if (b == null) return 1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  const da = Date.parse(a), db = Date.parse(b);
  if (!isNaN(da) && !isNaN(db)) return da - db;
  return String(a).localeCompare(String(b));
}

// Filtered + sorted rows for a table (without rendering) — shared by render and CSV export.
function viewRows(name) {
  const v = views[name];
  let rows = v.data().filter(r => v.matches(r, v));
  if (v.sort && v.cols[v.sort]) {
    const acc = v.cols[v.sort];
    rows = [...rows].sort((a, b) => cmpValues(acc(a), acc(b)) * v.dir);
  }
  return rows;
}

function applyView(name) {
  views[name].render(viewRows(name));
  updateSortIndicators(name);
}

function sortBy(name, key) {
  const v = views[name];
  if (v.sort === key) v.dir *= -1;
  else { v.sort = key; v.dir = 1; }
  applyView(name);
}

function setFilter(name, field, value) {
  views[name][field] = field === 'text' ? value.toLowerCase() : value;
  applyView(name);
}

function updateSortIndicators(name) {
  const v = views[name];
  const thead = document.querySelector(`#${v.panel} thead`);
  if (!thead) return;
  thead.querySelectorAll('.sort-ind').forEach(s => s.textContent = '');
  if (!v.sort) return;
  const active = thead.querySelector(`[data-sort="${v.sort}"] .sort-ind`);
  if (active) active.textContent = v.dir > 0 ? '▲' : '▼';
}

// Backwards-compatible thin wrappers.
function filterUsers(q) { setFilter('users', 'text', q); }

// ═══ CSV EXPORT ══════════════════════════════════════
// Columns exported per table (header name + value accessor).
const CSV_COLS = {
  users: [
    ['ID', r => r.id], ['Email', r => r.user?.email || ''], ['Role', r => r.role || 'user'],
    ['Active', r => r.is_active !== false ? 'yes' : 'no'], ['Created', r => fmtDateTime(r.created_at)], ['Plan', r => r.plan?.name || ''],
  ],
  subs: [
    ['ID', r => r.id], ['User ID', r => r.user_id], ['Plan', r => r.plan?.name || r.plan_id || ''],
    ['Currency', r => (r.currency || '').toUpperCase()], ['Status', r => r.status], ['Period End', r => fmtDateTime(r.current_period_end)],
  ],
  invoices: [
    ['ID', r => r.id], ['Subscription ID', r => r.subscription_id], ['Amount', r => r.amount],
    ['Currency', r => (r.currency || '').toUpperCase()], ['Status', r => r.status], ['Due Date', r => fmtDateTime(r.due_date)],
  ],
  payments: [
    ['ID', r => r.id], ['Invoice ID', r => r.invoice_id], ['Provider', r => r.provider || ''],
    ['Status', r => r.status], ['Created', r => fmtDateTime(r.created_at)],
  ],
};

function csvEscape(v) {
  const s = String(v == null ? '' : v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function exportCSV(name) {
  const cols = CSV_COLS[name];
  const rows = viewRows(name);
  if (!rows.length) { showToast('Nothing to export', 'error'); return; }
  const header = cols.map(c => c[0]).join(',');
  const lines = rows.map(r => cols.map(c => csvEscape(c[1](r))).join(','));
  // BOM keeps UTF-8 intact (currency symbols, Cyrillic). The 'sep=,' hint tells
  // Excel to split on commas regardless of the OS list-separator locale
  // (RU/EU Excel defaults to ';', which otherwise dumps each row into one cell).
  const csv = '﻿sep=,\r\n' + [header, ...lines].join('\r\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${name}-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Exported ${rows.length} row${rows.length === 1 ? '' : 's'}`, 'ok');
}

function renderSubscriptions(subs) {
  const tb = document.getElementById('subs-tbody');
  if (!subs.length) { tb.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">↻</div>No subscriptions</div></td></tr>'; return; }
  tb.innerHTML = subs.map(s=>`<tr onclick="openSubDetail('${s.id}')" title="Click for details">
    <td class="id-cell" title="${s.id}">${short(s.id)}</td>
    <td class="id-cell" title="${s.user_id}">${short(s.user_id)}</td>
    <td style="font-size:11px">${s.plan?.name || s.plan_id || '—'}</td>
    <td>${mkbadge(s.status)}</td>
    <td style="color:var(--muted);font-size:11px">${fmtDate(s.current_period_end)}</td>
    <td>${['active','incomplete','past_due'].includes(s.status)
      ? `<button class="btn btn-danger" style="font-size:10px;padding:4px 8px" onclick="event.stopPropagation();promptCancelSub('${s.id}')">Cancel</button>`
      : '<span style="color:var(--muted);font-size:10px">—</span>'}</td>
  </tr>`).join('');
}

// Drill-down: show a subscription's invoices and the payments linked to them.
// Works on the currently loaded page of invoices/payments (see pagination note).
function openSubDetail(subId) {
  const sub = allSubs.find(s => String(s.id) === String(subId));
  if (!sub) return;
  const invoices = allInvoices.filter(i => String(i.subscription_id) === String(subId));
  const invoiceIds = new Set(invoices.map(i => String(i.id)));
  const payments = allPayments.filter(p => invoiceIds.has(String(p.invoice_id)));

  const cell = c => `<td style="font-size:11px;padding:8px 10px;border-bottom:1px solid var(--border)">${c}</td>`;
  const th = h => `<th style="font-size:9px;text-align:left;letter-spacing:1px;text-transform:uppercase;padding:8px 10px;color:var(--muted)">${h}</th>`;
  const miniTable = (headers, rows) => rows.length
    ? `<table style="width:100%;border-collapse:collapse"><thead><tr>${headers.map(th).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`
    : '<div style="font-size:11px;color:var(--muted);padding:8px 0">None</div>';

  const invRows = invoices.map(i => `<tr>${[
    `<span class="id-cell" title="${i.id}">${shortId(i.id)}</span>`,
    fmtAmt(i.amount, i.currency),
    mkbadge(i.status),
    fmtDate(i.due_date),
  ].map(cell).join('')}</tr>`);

  const payRows = payments.map(p => `<tr>${[
    `<span class="id-cell" title="${p.id}">${shortId(p.id)}</span>`,
    p.provider || '—',
    mkbadge(p.status),
    fmtDate(p.created_at),
  ].map(cell).join('')}</tr>`);

  const meta = [
    ['ID', `<span style="word-break:break-all">${sub.id}</span>`],
    ['User ID', `<span style="word-break:break-all">${sub.user_id}</span>`],
    ['Plan', sub.plan?.name || sub.plan_id || '—'],
    ['Currency', (sub.currency || '—').toUpperCase()],
    ['Status', mkbadge(sub.status)],
    ['Period end', fmtDate(sub.current_period_end)],
  ].map(([k, val]) => `<div style="color:var(--muted)">${k}</div><div>${val}</div>`).join('');

  document.getElementById('sub-detail-body').innerHTML = `
    <div style="display:grid;grid-template-columns:auto 1fr;gap:6px 16px;font-size:11px;margin-bottom:22px">${meta}</div>
    <div style="font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:8px">Invoices (${invoices.length})</div>
    ${miniTable(['ID','Amount','Status','Due'], invRows)}
    <div style="font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin:22px 0 8px">Payments (${payments.length})</div>
    ${miniTable(['ID','Provider','Status','Created'], payRows)}`;
  openModal('sub-detail');
}

function renderInvoices(invs) {
  const tb = document.getElementById('invoices-tbody');
  if (!invs.length) { tb.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">◻</div>No invoices</div></td></tr>'; return; }
  tb.innerHTML = invs.map(i=>`<tr>
    <td class="id-cell" title="${i.id}">${short(i.id)}</td>
    <td class="id-cell" title="${i.subscription_id}">${short(i.subscription_id)}</td>
    <td class="amount ${i.status==='paid'?'amount-positive':i.status==='failed'?'amount-negative':''}">${fmtAmt(i.amount, i.currency)}</td>
    <td style="font-size:11px;color:var(--muted)">${(i.currency||'USD').toUpperCase()}</td>
    <td>${mkbadge(i.status)}</td>
    <td style="color:var(--muted);font-size:11px">${fmtDate(i.due_date)}</td>
  </tr>`).join('');
}

function filterInvoices(status) { setFilter('invoices', 'status', status); }

function renderPayments(pays) {
  const tb = document.getElementById('payments-tbody');
  if (!pays.length) { tb.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">◆</div>No payments</div></td></tr>'; return; }
  tb.innerHTML = pays.map(p=>`<tr>
    <td class="id-cell" title="${p.id}">${short(p.id)}</td>
    <td class="id-cell" title="${p.invoice_id}">${short(p.invoice_id)}</td>
    <td style="font-size:11px;color:var(--muted)">${p.provider||'—'}</td>
    <td>${mkbadge(p.status)}</td>
    <td style="color:var(--muted);font-size:11px">${fmtDate(p.created_at)}</td>
    <td>${p.status==='pending'
      ? `<button class="btn btn-primary" style="font-size:10px;padding:4px 8px" onclick="confirmPayment('${p.id}')">Confirm</button>`
      : '<span style="color:var(--muted);font-size:10px">—</span>'}</td>
  </tr>`).join('');
}

// ═══ ACTIONS ══════════════════════════════════════════
function promptCancelSub(id) {
  pendingCancelSubId = id;
  document.getElementById('cancel-sub-id-display').textContent = id;
  openModal('confirm-cancel');
}

async function executeCancelSub() {
  if (!pendingCancelSubId) return;
  const id = pendingCancelSubId;
  closeModalForce();
  try {
    await apiFetch(`/admin/subscriptions/${id}/cancel?immediate=true`, { method: 'POST' });
    addWebhookEntry('subscription.canceled', id, 'succeeded');
    showToast('Subscription canceled', 'ok');
    await loadSubscriptions();
    renderDashboard();
  } catch(e) {
    showToast('Cancel failed: ' + e.message, 'error');
  }
}

async function confirmPayment(id) {
  try {
    await apiFetch(`/admin/payments/${id}/confirm`, { method: 'PATCH' });
    addWebhookEntry('payment.succeeded', id, 'succeeded');
    showToast('Payment confirmed ✓', 'ok');
    // Confirming a payment also flips the invoice (→ paid) and subscription (→ active),
    // so refresh those views too — not just the payments table.
    await Promise.all([loadPayments(), loadInvoices(), loadSubscriptions()]);
    renderDashboard();
  } catch(e) {
    showToast('Confirm failed: ' + e.message, 'error');
  }
}

// ═══ WEBHOOKS ════════════════════════════════════════
function fmtDateTime(d) {
  if (!d) return '';
  const dt = new Date(d);
  if (isNaN(dt)) return String(d);
  const p = n => String(n).padStart(2,'0');
  return `${dt.getFullYear()}-${p(dt.getMonth()+1)}-${p(dt.getDate())} ${p(dt.getHours())}:${p(dt.getMinutes())}:${p(dt.getSeconds())}`;
}

// Merge persisted webhook events (DB) with local simulate/action entries, newest first.
function allWebhookEntries() {
  const db = dbWebhooks.map(e => ({
    ts: Date.parse(e.created_at) || 0,
    time: fmtDateTime(e.created_at),
    event: e.event_type,
    status: e.status,
    resource: e.provider_payment_id || '—',
    payload: typeof e.payload === 'string' ? e.payload : JSON.stringify(e.payload || {}, null, 2),
    source: 'db',
  }));
  const local = webhookLog.map(w => ({
    ts: Date.parse(w.time) || 0,
    time: w.time,
    event: w.event,
    status: w.status,
    resource: w.resource,
    payload: w.payload,
    source: 'local',
  }));
  return [...db, ...local].sort((a, b) => b.ts - a.ts);
}

function renderWebhooks() {
  const c = document.getElementById('webhook-entries');
  const entries = allWebhookEntries();
  if (!entries.length) { c.innerHTML = '<div class="empty-state"><div class="empty-icon">⟳</div>No webhook events yet</div>'; return; }
  c.innerHTML = entries.map(w=>`
    <div class="log-entry" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='block'?'none':'block'">
      <span class="log-time">${w.time}</span>
      <div style="flex:1"><div class="log-event">${w.event} <span style="color:var(--muted);font-size:9px;letter-spacing:1px">${w.source==='db'?'DB':'LOCAL'}</span></div><div class="log-payload">${w.resource}</div></div>
      <span>${mkbadge(w.status)}</span>
    </div>
    <div style="display:none;padding:10px 16px;background:var(--bg);border-bottom:1px solid var(--border)">
      <pre style="font-size:10px;color:var(--muted);line-height:1.6">${w.payload}</pre>
    </div>`).join('');
  const fc = entries.filter(w=>w.status==='failed').length;
  const b = document.getElementById('webhook-badge');
  b.textContent = fc; b.style.display = fc ? '' : 'none';
}

function addWebhookEntry(event, resource, status) {
  const now = new Date();
  const p = n => String(n).padStart(2,'0');
  const time = `${now.getFullYear()}-${p(now.getMonth()+1)}-${p(now.getDate())} ${p(now.getHours())}:${p(now.getMinutes())}:${p(now.getSeconds())}`;
  webhookLog.unshift({ time, event, status, resource, payload: JSON.stringify({event,resource,timestamp:time},null,2) });
  // Keep at most 200 entries so localStorage doesn't grow unbounded
  if (webhookLog.length > 200) webhookLog = webhookLog.slice(0, 200);
  try { localStorage.setItem('billing_webhook_log', JSON.stringify(webhookLog)); } catch {}
  renderWebhooks();
  renderDashboard();
}

function clearWebhooks() {
  webhookLog = [];
  localStorage.removeItem('billing_webhook_log');
  renderWebhooks();
  renderDashboard();
}

function fireSimulatedWebhook() {
  const event = document.getElementById('wh-event-type').value;
  const resource = document.getElementById('wh-resource-id').value || 'demo_resource';
  addWebhookEntry(event, resource, event.includes('failed') ? 'failed' : 'succeeded');
  closeModalForce();
  showToast('Event fired: ' + event, 'ok');
}

// ═══ API TESTER ═══════════════════════════════════════
async function runEndpoint(name) {
  const base = document.getElementById('tester-base').value || apiBase;
  const tok = document.getElementById('tester-token').value || jwtToken;
  const H = { 'Authorization': `Bearer ${tok}`, 'Content-Type': 'application/json' };
  const el = document.getElementById('res-' + name);
  if (el) { el.textContent = '// Sending…'; el.className = 'response-box empty'; }

  const show = (r, data) => {
    if (!el) return;
    el.textContent = JSON.stringify(data, null, 2);
    el.className = r.ok ? 'response-box' : 'response-box error';
  };

  try {
    let r;
    const G = path => fetch(`${base}${path}`, { headers: H });
    const P = (path, body) => fetch(`${base}${path}`, { method:'POST', headers: H, body: body ? JSON.stringify(body) : undefined });
    const PA = (path) => fetch(`${base}${path}`, { method:'PATCH', headers: H });

    if (name === 'register')        r = await P('/auth/register', { email: v('reg-email'), password: v('reg-password') });
    else if (name === 'tester-login') r = await P('/auth/login', { email: v('te-email'), password: v('te-password') });
    else if (name === 'admin-subs')  r = await G('/admin/subscriptions/');
    else if (name === 'admin-pays')  r = await G('/admin/payments/');
    else if (name === 'admin-cancel') r = await P(`/admin/subscriptions/${v('te-cancel-id')}/cancel`);
    else if (name === 'list-invoices') r = await G('/invoices/');
    else if (name === 'create-payment') r = await P('/payments/', { invoice_id: v('pay-invoice'), provider: v('pay-provider') });
    else if (name === 'confirm-payment') r = await PA(`/admin/payments/${v('confirm-id')}/confirm`);
    else if (name === 'get-sub')     r = await G('/subscriptions/me');

    if (r) {
      const data = await r.json().catch(() => ({}));
      show(r, data);
      if ((name === 'tester-login') && data.access_token) {
        document.getElementById('tester-token').value = data.access_token;
        jwtToken = data.access_token;
        showToast('JWT captured ✓', 'ok');
      }
    }
  } catch(e) {
    if (el) { el.textContent = `// Failed: ${e.message}`; el.className = 'response-box error'; }
  }
}

// ═══ NAV ══════════════════════════════════════════════
const tabTitles = { dashboard:'Dashboard', subscribers:'Subscribers', subscriptions:'Subscriptions', invoices:'Invoices', payments:'Payments', plans:'Plans', webhooks:'Webhooks', api:'API Tester' };

function showTab(name, el) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (el) el.classList.add('active');
  document.getElementById('page-title').textContent = tabTitles[name] || name;
  const btn = document.getElementById('topbar-action');
  btn.textContent = name === 'webhooks' ? '⚡ Simulate' : '⟳ Refresh';
  btn.style.display = name === 'api' ? 'none' : '';
  // Pull fresh data whenever a tab is opened so it never shows a stale cache
  // from login time (the Webhooks tab in particular has no Refresh button).
  if (jwtToken) refreshCurrentTab();
}

// Open a tab and pre-apply a status filter — used by the clickable dashboard cards.
function showFiltered(tab, navIdx, view, selectId, status) {
  showTab(tab, document.querySelectorAll('.nav-item')[navIdx]);
  const sel = document.getElementById(selectId);
  if (sel) sel.value = status;
  setFilter(view, 'status', status);
}

function handleTopbarAction() {
  if (document.getElementById('page-title').textContent === 'Webhooks') openModal('simulate-webhook');
  else refreshCurrentTab();
}

// ═══ MODAL ════════════════════════════════════════════
function openModal(name) {
  document.getElementById('modal-overlay').classList.add('open');
  document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
  const el = document.getElementById('modal-' + name);
  if (el) el.style.display = 'block';
}
function closeModal(e) { if (e.target === document.getElementById('modal-overlay')) closeModalForce(); }
function closeModalForce() { document.getElementById('modal-overlay').classList.remove('open'); }

// ═══ UTILS ════════════════════════════════════════════
function mkbadge(status) {
  const s = String(status||'unknown').replace(/ /g,'_');
  return `<span class="badge badge-${s}">${s}</span>`;
}
function short(id) {
  // Returns the full ID — the .id-cell CSS truncates with an ellipsis only
  // when the column is too narrow to show it in full.
  return id ? String(id) : '—';
}
function shortId(id) {
  // Always-truncated form for compact widgets (e.g. dashboard summary) where
  // there isn't room for a full UUID.
  if (!id) return '—';
  const s = String(id);
  return s.length > 12 ? s.slice(0,8) + '…' : s;
}
function fmtDate(d) {
  if (!d) return '—';
  try { return new Date(d).toISOString().split('T')[0]; } catch { return String(d); }
}
const CURRENCY_SYMBOLS = { USD: '$', EUR: '€', GBP: '£', RUB: '₽' };
function fmtAmt(a, currency) {
  if (a == null) return '—';
  const cur = (currency || 'USD').toUpperCase();
  const sym = CURRENCY_SYMBOLS[cur];
  const n = Number(a).toFixed(2);
  return sym ? sym + n : n + ' ' + cur;
}
function esc(s) { return String(s||'').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function v(id) { return (document.getElementById(id)||{}).value || ''; }

function showToast(msg, type='ok') {
  const t = document.createElement('div');
  t.style.cssText = 'position:fixed;bottom:24px;right:24px;padding:12px 18px;border-radius:7px;font-family:"DM Mono",monospace;font-size:11px;z-index:9999;border:1px solid;background:var(--surface);max-width:340px;animation:fadeIn 0.2s ease';
  t.style.color = type==='ok'?'var(--accent)':type==='error'?'var(--accent2)':'var(--accent3)';
  t.style.borderColor = type==='ok'?'rgba(79,255,176,0.2)':type==='error'?'rgba(255,107,107,0.2)':'rgba(255,201,71,0.2)';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}
