// ── State ──────────────────────────────────────────────────────────────────
let sortField = 'date_submitted';
let sortOrder = 'desc';
let editingId  = null;

const filters = { search: '', platform: '', role_type: '', status: '' };

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupFilters();
    setupSortHeaders();
    setupModal();
    loadStats();
});

// ── Tabs ───────────────────────────────────────────────────────────────────
function setupTabs() {
    document.querySelectorAll('.tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
            btn.classList.add('active');
            const view = document.getElementById(`view-${btn.dataset.tab}`);
            view.classList.remove('hidden');
            if (btn.dataset.tab === 'log') loadLog();
        });
    });
}

// ── Stats ──────────────────────────────────────────────────────────────────
async function loadStats() {
    const data = await api('/api/stats');
    if (!data) return;

    const { totals, rates, by_platform, by_role_type, by_month } = data;

    // Metric cards
    setText('m-total',     totals.all);
    setText('m-view-rate', pct(rates.view));
    setText('m-like-rate', pct(rates.like));
    setText('m-book-rate', pct(rates.booking));
    setText('m-earnings',  formatPay(totals.earnings, 'USD'));

    renderFunnel(totals);
    renderMonthlyChart(by_month, totals.all);
    renderBreakdownTable('platform-table', by_platform, 'platform');
    renderBreakdownTable('role-type-table', by_role_type, 'role_type');
}

function renderFunnel(t) {
    const max = t.all || 1;
    const rows = [
        { label: 'submitted', count: t.all,    cls: 'submitted', pct: 1 },
        { label: 'viewed',    count: t.viewed,  cls: 'viewed',    pct: t.viewed  / max },
        { label: 'liked',     count: t.liked,   cls: 'liked',     pct: t.liked   / max },
        { label: 'booked',    count: t.booked,  cls: 'booked',    pct: t.booked  / max },
    ];

    document.getElementById('funnel').innerHTML = rows.map(r => `
        <div class="funnel-row">
            <span class="funnel-label">${r.label}</span>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar ${r.cls}" style="width:${Math.max(r.pct * 100, 0.5).toFixed(1)}%">
                    ${r.pct > 0.12 ? pct(r.pct) : ''}
                </div>
            </div>
            <span class="funnel-count">${r.count}</span>
        </div>
    `).join('');
}

function renderMonthlyChart(byMonth, totalAll) {
    if (!byMonth.length) {
        document.getElementById('monthly-chart').innerHTML =
            '<span style="color:#9ca3af;font-size:0.8rem">no data yet</span>';
        return;
    }

    const maxTotal = Math.max(...byMonth.map(m => m.total), 1);
    const HEIGHT   = 100; // px available for bars

    document.getElementById('monthly-chart').innerHTML = byMonth.map(m => {
        const label    = m.month ? m.month.slice(0, 7) : '';
        const shortLbl = label ? label.slice(5) : ''; // MM
        const totalH   = Math.round((m.total / maxTotal) * HEIGHT);
        const bookedH  = Math.round(((m.booked || 0) / maxTotal) * HEIGHT);

        return `
            <div class="month-col" title="${label}: ${m.total} submitted, ${m.booked || 0} booked">
                <div class="month-bar-wrap">
                    <div class="month-bar total"  style="height:${totalH}px"></div>
                    <div class="month-bar booked" style="height:${bookedH}px"></div>
                </div>
                <span class="month-label">${shortLbl}</span>
            </div>
        `;
    }).join('');
}

function renderBreakdownTable(tableId, rows, keyField) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="color:#9ca3af;padding:1rem">no data</td></tr>';
        return;
    }

    tbody.innerHTML = rows.map(r => {
        const total = r.total || 0;
        const vPct  = pct(total ? (r.viewed || 0) / total : 0);
        const lPct  = pct(total ? (r.liked  || 0) / total : 0);
        const bPct  = pct(total ? (r.booked || 0) / total : 0);

        return `
            <tr>
                <td>${r[keyField] || '—'}</td>
                <td>${total}</td>
                <td>${r.viewed || 0} <span class="pct">${vPct}</span></td>
                <td>${r.liked  || 0} <span class="pct">${lPct}</span></td>
                <td>${r.booked || 0} <span class="pct">${bPct}</span></td>
                <td>${r.earnings ? formatPay(r.earnings, 'USD') : '—'}</td>
            </tr>
        `;
    }).join('');
}

// ── Log ────────────────────────────────────────────────────────────────────
async function loadLog() {
    const params = new URLSearchParams({ sort: sortField, order: sortOrder });

    if (filters.search)    params.set('search',    filters.search);
    if (filters.platform)  params.set('platform',  filters.platform);
    if (filters.role_type) params.set('role_type', filters.role_type);

    if (filters.status === 'booked')    params.set('booked', '1');
    if (filters.status === 'liked')     params.set('liked',  '1');
    if (filters.status === 'viewed')    params.set('viewed', '1');
    if (filters.status === 'not-viewed') params.set('viewed', '0');

    const rows = await api(`/api/auditions?${params}`);
    if (!rows) return;

    const tbody = document.getElementById('log-body');
    const empty = document.getElementById('log-empty');

    if (!rows.length) {
        tbody.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    tbody.innerHTML = rows.map(r => `
        <tr>
            <td>${r.date_submitted ? fmtDate(r.date_submitted) : '—'}</td>
            <td><span class="platform-badge ${r.platform}">${platformLabel(r.platform)}</span></td>
            <td>${r.client || '—'}</td>
            <td>${r.role   || '—'}</td>
            <td><span class="type-badge">${r.role_type || '—'}</span></td>
            <td><span class="status-dot ${r.viewed ? 'viewed-on' : 'off'}" title="${r.viewed ? 'viewed' : 'not viewed'}"></span></td>
            <td><span class="status-dot ${r.liked  ? 'liked-on'  : 'off'}" title="${r.liked  ? 'liked'  : 'not liked'}"></span></td>
            <td><span class="status-dot ${r.booked ? 'on'        : 'off'}" title="${r.booked ? 'booked' : 'not booked'}"></span></td>
            <td>${r.booked && r.pay ? formatPay(r.pay, r.pay_currency) : '—'}</td>
            <td>
                <div class="row-actions">
                    <button class="btn-icon" title="edit"   onclick="openModal(${JSON.stringify(r).replace(/"/g, '&quot;')})">✏️</button>
                    <button class="btn-icon" title="delete" onclick="deleteAudition(${r.id})">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// ── Filters ────────────────────────────────────────────────────────────────
function setupFilters() {
    let searchTimer;
    document.getElementById('filter-search').addEventListener('input', e => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => { filters.search = e.target.value; loadLog(); }, 300);
    });
    document.getElementById('filter-platform').addEventListener('change', e => {
        filters.platform = e.target.value; loadLog();
    });
    document.getElementById('filter-role-type').addEventListener('change', e => {
        filters.role_type = e.target.value; loadLog();
    });
    document.getElementById('filter-status').addEventListener('change', e => {
        filters.status = e.target.value; loadLog();
    });
}

// ── Sort ───────────────────────────────────────────────────────────────────
function setupSortHeaders() {
    document.querySelectorAll('.log-table th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const field = th.dataset.sort;
            if (sortField === field) {
                sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                sortField = field;
                sortOrder = 'desc';
            }
            document.querySelectorAll('.log-table th').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            th.classList.add(`sort-${sortOrder}`);
            loadLog();
        });
    });
}

// ── Modal ──────────────────────────────────────────────────────────────────
function setupModal() {
    document.getElementById('btn-add').addEventListener('click', () => openModal(null));
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('btn-cancel').addEventListener('click', closeModal);
    document.getElementById('modal-overlay').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeModal();
    });

    document.getElementById('f-booked').addEventListener('change', e => {
        document.getElementById('pay-row').style.display = e.target.checked ? 'grid' : 'none';
    });

    document.getElementById('audition-form').addEventListener('submit', async e => {
        e.preventDefault();
        await saveAudition();
    });
}

function openModal(data) {
    editingId = data?.id ?? null;
    document.getElementById('modal-title').textContent = editingId ? 'edit audition' : 'add audition';

    const form = document.getElementById('audition-form');
    form.reset();
    document.getElementById('pay-row').style.display = 'none';

    if (data) {
        setField('f-platform',  data.platform);
        setField('f-date',      data.date_submitted);
        setField('f-client',    data.client);
        setField('f-role',      data.role);
        setField('f-role-type', data.role_type);
        setField('f-notes',     data.notes);
        document.getElementById('f-viewed').checked = !!data.viewed;
        document.getElementById('f-liked').checked  = !!data.liked;
        document.getElementById('f-booked').checked = !!data.booked;
        if (data.booked) {
            document.getElementById('pay-row').style.display = 'grid';
            setField('f-pay',      data.pay);
            setField('f-currency', data.pay_currency || 'USD');
        }
    }

    document.getElementById('modal-overlay').classList.remove('hidden');
    document.getElementById('f-client').focus();
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    editingId = null;
}

async function saveAudition() {
    const payload = {
        platform:       val('f-platform'),
        date_submitted: val('f-date') || null,
        client:         val('f-client')    || null,
        role:           val('f-role')      || null,
        role_type:      val('f-role-type') || null,
        notes:          val('f-notes')     || null,
        viewed:         document.getElementById('f-viewed').checked ? 1 : 0,
        liked:          document.getElementById('f-liked').checked  ? 1 : 0,
        booked:         document.getElementById('f-booked').checked ? 1 : 0,
        pay:            document.getElementById('f-booked').checked ? (parseFloat(val('f-pay')) || null) : null,
        pay_currency:   val('f-currency') || 'USD',
    };

    const url    = editingId ? `/api/auditions/${editingId}` : '/api/auditions';
    const method = editingId ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    if (res.ok) {
        closeModal();
        loadLog();
        loadStats();
    } else {
        alert('Save failed — check the console.');
        console.error(await res.text());
    }
}

async function deleteAudition(id) {
    if (!confirm('Delete this audition?')) return;
    const res = await fetch(`/api/auditions/${id}`, { method: 'DELETE' });
    if (res.ok) { loadLog(); loadStats(); }
    else alert('Delete failed.');
}

// ── Helpers ────────────────────────────────────────────────────────────────
async function api(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(res.statusText);
        return res.json();
    } catch (e) {
        console.error('API error:', e);
        return null;
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
}

function val(id)     { return document.getElementById(id)?.value ?? ''; }
function setField(id, v) { const el = document.getElementById(id); if (el && v != null) el.value = v; }

function pct(rate) {
    if (rate == null || isNaN(rate)) return '—';
    return `${Math.round(rate * 100)}%`;
}

function formatPay(amount, currency) {
    if (!amount && amount !== 0) return '—';
    const symbol = { USD: '$', EUR: '€', GBP: '£', CAD: 'CA$', AUD: 'A$' }[currency] ?? '';
    return `${symbol}${Number(amount).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso + (iso.includes('T') ? '' : 'T00:00:00'));
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function platformLabel(p) {
    return { voice123: 'Voice123', acx: 'ACX', ccc: 'CCC' }[p] ?? p;
}
