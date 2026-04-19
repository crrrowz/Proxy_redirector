/* ═══════════════════════════════════════════════
   Proxy Redirector — Dashboard JS v3.0
   Tab-based navigation + Ad Blocker + Search/Filter
   ═══════════════════════════════════════════════ */

let updateInterval = null;
let _trafficCache = [];
let _rulesCache = [];
let _proxiesCache = [];
let _clientsCache = [];
let _analyticsTopCache = [];
let _analyticsCountriesCache = [];
let _lastStatus = {};
let _currentTab = 'dashboard';
let _sortState = {}; // { tableId: { col: 'key', asc: true } }
async function fetchJSON(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) return null;
        return await res.json();
    } catch { return null; }
}

// ══════════════════════════════════════════════
// Tab Navigation
// ══════════════════════════════════════════════
function switchTab(tabId, navEl) {
    // Hide all tabs
    document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
    // Show selected
    const target = document.getElementById('tab-' + tabId);
    if (target) target.classList.add('active');

    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    if (navEl) navEl.classList.add('active');

    _currentTab = tabId;

    // Load tab specific data
    if (tabId === 'settings') loadSettings();
    if (tabId === 'analytics') loadAnalytics();
}

// ══════════════════════════════════════════════
// Engine Controls
// ══════════════════════════════════════════════
function setEngineLoadingState() {
    document.getElementById('engine-status-label').innerText = 'Loading...';
    document.getElementById('engine-status-label').style.color = 'var(--text-muted)';
    document.getElementById('status-dot').classList.remove('off');
    document.getElementById('status-dot').classList.add('pulse');
    document.getElementById('btn-start').style.opacity = '0.5';
    document.getElementById('btn-stop').style.opacity = '0.5';
    document.getElementById('btn-start').style.pointerEvents = 'none';
    document.getElementById('btn-stop').style.pointerEvents = 'none';
}

function clearEngineLoadingState() {
    document.getElementById('status-dot').classList.remove('pulse');
    document.getElementById('btn-start').style.opacity = '1';
    document.getElementById('btn-stop').style.opacity = '1';
    document.getElementById('btn-start').style.pointerEvents = 'auto';
    document.getElementById('btn-stop').style.pointerEvents = 'auto';
}

/* ── Engine Startup Modal ── */
function startEngine() {
    // Synchronize the Modal values exactly with the Settings page
    const mainCountry = document.getElementById('cfg-COUNTRY_FILTER');
    const mainSpeed = document.getElementById('cfg-MAX_SPEED_MS');
    const modalCountry = document.getElementById('modal-country');
    const modalSpeed = document.getElementById('modal-speed');

    // If Settings page drop-down exists, use its value. (It might have unsaved changes!)
    if (mainCountry && modalCountry && mainCountry.value) {
        modalCountry.value = mainCountry.value;
    }
    if (mainSpeed && modalSpeed) {
        modalSpeed.value = mainSpeed.value || '';
    }

    document.getElementById('start-modal').classList.add('active');
}

function closeStartModal(e) {
    if (e) { e.preventDefault(); e.stopPropagation(); }
    document.getElementById('start-modal').classList.remove('active');
}

async function confirmStartEngine() {
    const qCountry = document.getElementById('modal-country');
    const qSpeed = document.getElementById('modal-speed');
    
    if (qCountry && qSpeed) {
        let speedVal = parseInt(qSpeed.value, 10);
        if (isNaN(speedVal) || speedVal < 0) speedVal = 0;
        
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                COUNTRY_FILTER: qCountry.value,
                MAX_SPEED_MS: speedVal
            })
        });
        
        // Sync to main settings UI if exists
        const cs = document.getElementById('cfg-COUNTRY_FILTER');
        if (cs) cs.value = qCountry.value;
        const cms = document.getElementById('cfg-MAX_SPEED_MS');
        if (cms) cms.value = speedVal;
    }

    closeStartModal();
    setEngineLoadingState();
    await fetch('/api/start', { method: 'POST' });
    setTimeout(updateDashboard, 500);
}

async function stopEngine() {
    setEngineLoadingState();
    await fetch('/api/stop', { method: 'POST' });
    setTimeout(updateDashboard, 500);
}

async function clearTraffic() {
    await fetch('/api/traffic/clear', { method: 'POST' });
    _trafficCache = [];
    renderTrafficTable(_trafficCache);
}

// ══════════════════════════════════════════════
// Dashboard Tab Renderers
// ══════════════════════════════════════════════
function renderServerInfo(status) {
    // Engine state
    const dot = document.getElementById('status-dot');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const label = document.getElementById('engine-status-label');

    // Handle the special starting/restarting state
    if (status.starting) {
        label.innerText = 'Restarting / Scanning...';
        label.style.color = 'var(--text-muted)';
        dot.classList.remove('off');
        dot.classList.add('pulse');
        btnStart.style.display = 'none';
        btnStop.style.display = 'flex';
        btnStop.style.opacity = '0.5';
        btnStop.style.pointerEvents = 'none';
    } else {
        // Ensure UI is fully restored
        if (typeof clearEngineLoadingState === 'function') {
            clearEngineLoadingState();
        }

        if (status.running) {
            dot.classList.remove('off');
            btnStart.style.display = 'none';
            btnStop.style.display = 'flex';
            label.innerText = 'Running';
            label.style.color = 'var(--success)';
        } else {
            dot.classList.add('off');
            btnStart.style.display = 'flex';
            btnStop.style.display = 'none';
            label.innerText = 'Stopped';
            label.style.color = 'var(--danger)';
        }
    }

    // Stat cards
    const conns = (status.socks5_connections || 0) + (status.http_connections || 0);
    document.getElementById('stat-connections').innerText = conns;
    document.getElementById('stat-alive').innerText = (status.pool && status.pool.alive) || 0;

    // Server info card
    const srvHtml = `
        <div class="info-row">
            <span class="info-label">SOCKS5 Server</span>
            <span class="badge ${status.socks5_ok ? 'on' : 'off'}">
                0.0.0.0:${status.socks5_port}
            </span>
        </div>
        <div class="info-row">
            <span class="info-label">HTTP Proxy</span>
            <span class="badge ${status.http_ok ? 'on' : 'off'}">
                0.0.0.0:${status.http_port}
            </span>
        </div>
        <div class="info-row">
            <span class="info-label">Auth</span>
            <span class="info-value" style="color: ${status.auth_enabled ? 'var(--warning)' : 'var(--text-muted)'}">
                ${status.auth_enabled ? `${status.auth_user} / ${status.auth_pass}` : 'Disabled'}
            </span>
        </div>
    `;
    document.getElementById('server-info').innerHTML = srvHtml;

    // Network IPs
    let ipsHtml = '';
    if (status.local_ips && status.local_ips.length > 0) {
        status.local_ips.forEach(ip => {
            ipsHtml += `<div class="code-block">${ip}:${status.http_port} (HTTP)</div>`;
            ipsHtml += `<div class="code-block">${ip}:${status.socks5_port} (SOCKS5)</div>`;
        });
    } else {
        ipsHtml = `<span class="info-label">No local IP detected</span>`;
    }
    document.getElementById('network-ips').innerHTML = ipsHtml;

    // Active proxy
    if (status.active_proxy) {
        const ap = status.active_proxy;
        document.getElementById('active-proxy').innerHTML =
            `<strong>${ap.ip}:${ap.port}</strong> <span class="badge on">${ap.type}</span> ` +
            `| ${ap.speed_ms ? Math.round(ap.speed_ms) + 'ms' : '--'} ` +
            `| Switches: ${ap.switches || 0}`;
    } else {
        document.getElementById('active-proxy').innerText = '-- searching...';
    }
}

function renderClients(clients) {
    const tbody = document.getElementById('clients-table-body');
    document.getElementById('clients-count').innerText = clients ? clients.length : 0;
    
    _clientsCache = clients || [];

    if (!clients || clients.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-muted)">No active connections</td></tr>`;
        return;
    }

    let arr = sortArray(_clientsCache, _sortState['clients-table-body']);
    let html = '';
    arr.forEach(c => {
        const pClass = c.protocol === 'HTTP' ? 'http' : 'socks5';
        let target = c.target;
        if (target.length > 40) target = target.substring(0, 37) + '...';
        html += `
            <tr>
                <td style="font-family:monospace; font-size:12px;">${c.ip}</td>
                <td><span class="badge ${pClass}">${c.protocol}</span></td>
                <td style="font-size:12px;">${target}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// ══════════════════════════════════════════════
// Proxy Pool Tab
// ══════════════════════════════════════════════
// Cache declared at top

function renderProxyPool(status, proxies) {
    const pool = status.pool || {};
    document.getElementById('pool-stats-text').innerText =
        `${pool.alive || 0} alive | ${pool.dead_retryable || 0} retry | ${pool.blacklisted || 0} blocked | ${pool.unchecked || 0} unchecked | ${pool.total || 0} total`;

    _proxiesCache = proxies || [];
    renderProxyTable(_proxiesCache);
}

function renderProxyTable(proxies) {
    const tbody = document.getElementById('proxy-table-body');
    if (!proxies || proxies.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted)">No proxies loaded</td></tr>`;
        return;
    }

    let arr = sortArray(proxies, _sortState['proxy-table-body']);
    let html = '';
    arr.forEach((p, i) => {
        const marker = p.active ? '► ' : '';
        const statusBadge = p.alive
            ? '<span class="badge on">UP</span>'
            : '<span class="badge off">DN</span>';
        const spd = p.speed_ms ? Math.round(p.speed_ms) + 'ms' : '--';
        const rowBg = p.active ? 'background:var(--primary-glow);' : '';

        html += `
            <tr style="${rowBg}">
                <td>${marker}${i + 1}</td>
                <td style="font-family:monospace; font-size:12px;">${p.ip}:${p.port}</td>
                <td><span class="badge ${p.type === 'SOCKS5' ? 'socks5' : 'http'}">${p.type}</span></td>
                <td>${p.country || '??'}</td>
                <td>${statusBadge}</td>
                <td>${spd}</td>
                <td>${p.score.toFixed(1)}</td>
                <td>${p.failures}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function filterProxies() {
    const q = document.getElementById('proxy-search').value.toLowerCase();
    if (!q) { renderProxyTable(_proxiesCache); return; }
    const filtered = _proxiesCache.filter(p =>
        `${p.ip}:${p.port}`.includes(q) || p.type.toLowerCase().includes(q)
    );
    renderProxyTable(filtered);
}

// ══════════════════════════════════════════════
// Traffic Log Tab
// ══════════════════════════════════════════════
function renderTraffic(traffic) {
    if (!traffic) return;

    const stats = traffic.stats || {};
    document.getElementById('traffic-stats').innerText =
        `${stats.total_requests || 0} requests | ${stats.total_bytes_human || '0 B'} | ${stats.unique_clients || 0} clients`;
    document.getElementById('stat-requests').innerText = stats.total_requests || 0;

    _trafficCache = traffic.recent || [];
    filterTraffic();
}

function renderTrafficTable(entries) {
    const tbody = document.getElementById('traffic-table-body');

    if (!entries || entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted)">No traffic recorded</td></tr>`;
        return;
    }

    let arr = entries.slice();
    if (_sortState['traffic-table-body']) {
        arr = sortArray(arr, _sortState['traffic-table-body']);
    } else {
        arr.reverse(); // Default is newest first
    }

    let html = '';
    arr.forEach(r => {
        let icon, color;
        if (r.status === 'blocked') {
            icon = '🚫'; color = 'var(--orange)';
        } else if (r.status === 'success') {
            icon = '✓'; color = 'var(--success)';
        } else {
            icon = '✗'; color = 'var(--danger)';
        }
        const pClass = r.protocol === 'HTTP' ? 'http' : 'socks5';
        let target = r.target;
        if (target.length > 40) target = target.substring(0, 37) + '...';
        const rowBg = r.status === 'blocked' ? 'background:rgba(249,115,22,0.04);' : '';

        html += `
            <tr style="${rowBg}">
                <td style="color:var(--text-muted); font-size:12px;">${r.time}</td>
                <td style="color:${color}; font-weight:bold">${icon}</td>
                <td style="font-family:monospace; font-size:12px;">${r.client_ip}</td>
                <td><span class="badge ${pClass}">${r.protocol}</span></td>
                <td>${r.method}</td>
                <td style="font-size:12px;">${target}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function filterTraffic() {
    const statusFilter = document.getElementById('traffic-filter').value;
    const search = document.getElementById('traffic-search').value.toLowerCase();

    let filtered = _trafficCache;
    if (statusFilter !== 'all') {
        filtered = filtered.filter(r => r.status === statusFilter);
    }
    if (search) {
        filtered = filtered.filter(r =>
            r.target.toLowerCase().includes(search) ||
            r.client_ip.includes(search) ||
            r.method.toLowerCase().includes(search)
        );
    }
    renderTrafficTable(filtered);
}

// ══════════════════════════════════════════════
// Ad Blocker Tab
// ══════════════════════════════════════════════
async function toggleAdBlock(enabled) {
    await fetch('/api/blocklist/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
    });
    updateAdBlockUI();
}

async function toggleCategory(category, enabled) {
    await fetch('/api/blocklist/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, enabled })
    });
    updateAdBlockUI();
}

async function addBlockRule() {
    const input = document.getElementById('new-rule-domain');
    const catSel = document.getElementById('new-rule-category');
    const domain = input.value.trim();
    if (!domain) return;

    await fetch('/api/blocklist/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'add', domain, category: catSel.value })
    });
    input.value = '';
    updateAdBlockUI();
}

async function removeBlockRule(domain) {
    await fetch('/api/blocklist/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'remove', domain })
    });
    updateAdBlockUI();
}

async function addWhitelist() {
    const input = document.getElementById('new-whitelist-domain');
    const domain = input.value.trim();
    if (!domain) return;

    await fetch('/api/blocklist/whitelist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'add', domain })
    });
    input.value = '';
    updateAdBlockUI();
}

async function removeWhitelist(domain) {
    await fetch('/api/blocklist/whitelist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'remove', domain })
    });
    updateAdBlockUI();
}

function getCategoryBadge(cat) {
    const map = {
        'ads': 'ads',
        'tracking': 'tracking',
        'malware': 'malware',
        'custom': 'custom',
    };
    const cls = map[cat] || 'custom';
    const label = cat.charAt(0).toUpperCase() + cat.slice(1);
    return `<span class="badge ${cls}">${label}</span>`;
}

async function updateAdBlockUI() {
    const data = await fetchJSON('/api/blocklist');
    if (!data) return;

    const stats = data.stats || {};
    const rules = data.rules || [];
    const whitelist = data.whitelist || [];
    const categories = data.categories || {};

    _rulesCache = rules;

    // Toggle
    document.getElementById('adblock-toggle').checked = stats.enabled;

    // Stats
    document.getElementById('adblock-stats').innerText =
        `${stats.total_blocked || 0} blocked | ${stats.total_rules || 0} rules | ${stats.total_whitelist || 0} exceptions`;
    document.getElementById('stat-blocked').innerText = stats.total_blocked || 0;

    // Nav badge
    const navBadge = document.getElementById('nav-blocked-count');
    if (stats.total_blocked > 0) {
        navBadge.style.display = 'inline';
        navBadge.innerText = stats.total_blocked > 999 ? '999+' : stats.total_blocked;
    } else {
        navBadge.style.display = 'none';
    }

    // Category checkboxes
    for (const cat of ['ads', 'tracking', 'malware', 'custom']) {
        const el = document.getElementById(`cat-${cat}`);
        if (el) el.checked = categories[cat] !== false;
    }

    // Top blocked
    const topEl = document.getElementById('top-blocked');
    const topDomains = stats.top_blocked_domains || [];
    if (topDomains.length > 0) {
        let topHtml = '<div style="display:flex; gap:8px; flex-wrap:wrap;">';
        topDomains.slice(0, 8).forEach(d => {
            topHtml += `<span class="badge blocked">${d.domain} (${d.count})</span>`;
        });
        topHtml += '</div>';
        topEl.innerHTML = topHtml;
    } else {
        topEl.innerHTML = '<span style="color:var(--text-muted); font-size:12px;">No blocked requests yet</span>';
    }

    // Rules
    filterRules();

    // Whitelist
    document.getElementById('whitelist-count').innerText = whitelist.length;
    const wlEl = document.getElementById('whitelist-list');
    if (whitelist.length === 0) {
        wlEl.innerHTML = '<span style="color:var(--text-muted); font-size:12px;">No exceptions</span>';
    } else {
        let wlHtml = '';
        whitelist.forEach(d => {
            wlHtml += `
                <div class="whitelist-item">
                    <span>${d}</span>
                    <button class="btn-delete" onclick="removeWhitelist('${d}')">✕</button>
                </div>
            `;
        });
        wlEl.innerHTML = wlHtml;
    }
}

function filterRules() {
    const searchEl = document.getElementById('rules-search');
    const q = (searchEl ? searchEl.value : '').toLowerCase();
    let filtered = _rulesCache;
    if (q) {
        filtered = filtered.filter(r => r.domain.toLowerCase().includes(q) || r.category.includes(q));
    }
    renderRulesTable(filtered);
}

function renderRulesTable(rules) {
    const tbody = document.getElementById('rules-table-body');
    if (!rules || rules.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted)">No rules found</td></tr>`;
        return;
    }

    let arr = sortArray(rules, _sortState['rules-table-body']);
    let html = '';
    arr.forEach(r => {
        html += `
            <tr>
                <td style="font-family:monospace; font-size:12px;">${r.domain}</td>
                <td>${getCategoryBadge(r.category)}</td>
                <td style="color:var(--text-muted); font-size:11px;">${r.type}</td>
                <td><button class="btn-delete" onclick="removeBlockRule('${r.domain}')">✕</button></td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// ══════════════════════════════════════════════
// Settings Tab
// ══════════════════════════════════════════════

// Settings keys that are boolean (rendered as checkboxes)
const _BOOL_KEYS = ['AUTH_ENABLED', 'ANONYMITY_CHECK', 'ADBLOCK_ENABLED', 'START_WITH_GUI', 'HIDE_CONSOLE'];

async function loadSettings() {
    // Load available countries first
    const cData = await fetchJSON('/api/countries');
    if (cData && cData.countries) {
        const select = document.getElementById('cfg-COUNTRY_FILTER');
        if (select) {
            let html = '<option value="GLOBAL">🌍 Global</option>';
            cData.countries.forEach(c => {
                const name = new Intl.DisplayNames(['en'], {type: 'region'}).of(c.code) || c.code;
                html += `<option value="${c.code}">${c.code} - ${name} (${c.count})</option>`;
            });
            select.innerHTML = html;
            // Set current
            if (cData.current) select.value = cData.current;
        }
    }

    const cfg = await fetchJSON('/api/config');
    if (!cfg) return;

    for (const [key, value] of Object.entries(cfg)) {
        const el = document.getElementById('cfg-' + key);
        if (!el) continue;

        if (_BOOL_KEYS.includes(key)) {
            el.checked = !!value;
        } else {
            el.value = value;
        }
    }
}

async function saveSettings() {
    const updates = {};
    document.querySelectorAll('.cfg-input').forEach(el => {
        const key = el.id.replace('cfg-', '');
        if (_BOOL_KEYS.includes(key)) {
            updates[key] = el.checked;
        } else if (el.type === 'number') {
            updates[key] = parseInt(el.value, 10);
        } else {
            updates[key] = el.value;
        }
    });

    // Check if we need to auto-restart
    const statusObj = await fetchJSON('/api/status');
    const wasRunning = statusObj && statusObj.running;

    if (wasRunning) {
        setEngineLoadingState();
        await fetch('/api/stop', { method: 'POST' });
    }

    const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    });

    if (res.ok) {
        if (wasRunning) {
            await fetch('/api/start', { method: 'POST' });
            setTimeout(updateDashboard, 500); // UI will clear loading state via renderServerInfo
        }

        const msg = document.getElementById('settings-saved-msg');
        if (msg) {
            msg.innerText = wasRunning 
                ? "✅ Settings saved! Engine was automatically restarted to apply changes." 
                : "✅ Settings saved successfully!";
            msg.style.display = 'block';
            setTimeout(() => { msg.style.display = 'none'; }, 4000);
        }
    } else {
        if (wasRunning) clearEngineLoadingState();
    }
}

async function initQuickSettings() {
    // Populate Countries
    const cData = await fetchJSON('/api/countries');
    if (cData && cData.countries) {
        const modalCountry = document.getElementById('modal-country');
        const cfgCountry = document.getElementById('cfg-COUNTRY_FILTER');
        const selects = [modalCountry, cfgCountry];
        
        let html = '<option value="GLOBAL">🌍 Global</option>';
        cData.countries.forEach(c => {
            const name = new Intl.DisplayNames(['en'], {type: 'region'}).of(c.code) || c.code;
            html += `<option value="${c.code}">${c.code} - ${name} (${c.count})</option>`;
        });

        selects.forEach(select => {
            if (!select) return;
            // Only set innerHTML if it's currently empty, or keep user selection
            const currentSelected = select.value;
            select.innerHTML = html;
            
            if (currentSelected && currentSelected !== "GLOBAL") {
                select.value = currentSelected;
            } else if (cData.current) {
                select.value = cData.current;
            }
        });
    }

    // Populate Speed
    const cfg = await fetchJSON('/api/config');
    if (cfg && cfg.MAX_SPEED_MS !== undefined) {
        const qs = document.getElementById('modal-speed');
        if (qs && !qs.value) qs.value = cfg.MAX_SPEED_MS > 0 ? cfg.MAX_SPEED_MS : '';
        const cs = document.getElementById('cfg-MAX_SPEED_MS');
        if (cs && !cs.value) cs.value = cfg.MAX_SPEED_MS > 0 ? cfg.MAX_SPEED_MS : '';
    }
}



// ══════════════════════════════════════════════
// Main Update Loop
// ══════════════════════════════════════════════
async function updateDashboard() {
    const status = await fetchJSON('/api/status');
    if (status) {
        renderServerInfo(status);
        const proxies = await fetchJSON('/api/proxies');
        renderProxyPool(status, proxies);
    }

    const clients = await fetchJSON('/api/clients');
    renderClients(clients);

    const traffic = await fetchJSON('/api/traffic');
    renderTraffic(traffic);

    updateAdBlockUI();

    if (_currentTab === 'analytics') {
        loadAnalytics();
    }
}

// ══════════════════════════════════════════════
// Analytics Tab
// ══════════════════════════════════════════════
async function loadAnalytics() {
    const summary = await fetchJSON('/api/analytics');
    if (!summary) return;

    document.getElementById('an-tracked').innerText = summary.total_tracked;
    document.getElementById('an-avg-speed').innerText = summary.avg_speed || '--';
    document.getElementById('an-avg-uptime').innerText = summary.avg_uptime ? summary.avg_uptime + '%' : '--';
    document.getElementById('an-best-score').innerText = summary.best_proxy ? summary.best_proxy.score : '--';

    const top = await fetchJSON('/api/analytics/top');
    if (top) _analyticsTopCache = top;
    renderAnalyticsTop(_analyticsTopCache);

    const countries = await fetchJSON('/api/analytics/countries');
    if (countries) _analyticsCountriesCache = countries;
    renderAnalyticsCountries(_analyticsCountriesCache);
}

function renderAnalyticsTop(top) {
    const tbody = document.getElementById('top-proxies-body');
    if (top && top.length > 0) {
        let arr = sortArray(top, _sortState['top-proxies-body']);
        let html = '';
        arr.forEach((p, i) => {
            let tags = p.tags.map(t => `<span class="badge ${t}">${t}</span>`).join(' ');
            let speedClass = p.avg_speed_ms < 200 ? 'text-success' : '';
            html += `<tr>
                <td>${i+1}</td>
                <td style="font-family:monospace; font-size:12px;">${p.id}</td>
                <td>${p.country}</td>
                <td class="${speedClass}">${p.avg_speed_ms}ms</td>
                <td>${p.uptime_pct}%</td>
                <td><strong>${p.reliability_score}</strong></td>
                <td>${p.total_checks}</td>
                <td>${tags}</td>
            </tr>`;
        });
        tbody.innerHTML = html;
    }
}

function renderAnalyticsCountries(countries) {
    const ctbody = document.getElementById('country-stats-body');
    if (countries && countries.length > 0) {
        let arr = sortArray(countries.slice(0, 50), _sortState['country-stats-body']);
        let html = '';
        arr.forEach(c => {
            const name = new Intl.DisplayNames(['en'], {type: 'region'}).of(c.country) || c.country;
            html += `<tr>
                <td>${c.country} - ${name}</td>
                <td>${c.proxy_count}</td>
                <td>${c.avg_speed_ms}ms</td>
                <td>${c.avg_uptime_pct}%</td>
                <td><strong>${c.avg_reliability}</strong></td>
            </tr>`;
        });
        ctbody.innerHTML = html;
    }
}

// ══════════════════════════════════════════════
// Settings Tooltips / Modals
// ══════════════════════════════════════════════
const SETTING_INFO = {
    'LOCAL_PORT': {
        title: "SOCKS5 Port",
        desc: "The port on which the main SOCKS5 server will run. Used to connect desktop applications and web browsers that support the SOCKS5 protocol."
    },
    'HTTP_PROXY_PORT': {
        title: "HTTP Proxy Port",
        desc: "The port on which the HTTP proxy server will run. Primarily designed for mobile devices (like iOS/Android Wi-Fi proxy settings) and older apps that don't support SOCKS5."
    },
    'LOCAL_HOST': {
        title: "Listen Address",
        desc: "The network bind address. Using `0.0.0.0` makes the proxy available to all devices on your local Wi-Fi network. Using `127.0.0.1` restricts access strictly to this computer only."
    },
    'AUTH_ENABLED': {
        title: "Authentication",
        desc: "Enables username/password protection. Highly recommended if you bind to `0.0.0.0` to prevent unauthorized users on your local network from leeching your proxy."
    },
    'AUTH_USERNAME': { title: "Username", desc: "The username required to connect when Authentication is enabled." },
    'AUTH_PASSWORD': { title: "Password", desc: "The password required to connect when Authentication is enabled." },
    'START_WITH_GUI': {
        title: "Start GUI Automatically",
        desc: "When running the python script normally (`python main.py`), this automatically launches the graphical dashboard interface instead of running entirely silently in the background."
    },
    'HIDE_CONSOLE': {
        title: "Hide Console (Windows)",
        desc: "A neat aesthetic feature for Windows users. Once the GUI successfully launches, the black terminal/CMD window will automatically hide itself to keep your taskbar clean."
    },
    'COUNTRY_FILTER': {
        title: "Target Country",
        desc: "The Geographical Filter. If you select a specific country (e.g., US), the engine will instantly drop all other proxies and exclusively scan, heal, and connect through proxies located in that country."
    },
    'MIN_ALIVE_POOL': {
        title: "Min Alive Pool",
        desc: "The absolute minimum number of working, healthy proxies the engine tries to maintain at all times. If the count drops below this, background maintenance kicks in to find new ones."
    },
    'BATCH_SIZE': {
        title: "Batch Size",
        desc: "How many raw, unchecked proxies the engine grabs from your source list to test simultaneously during a maintenance run. Higher values find working proxies faster but use more bandwidth."
    },
    'RECHECK_INTERVAL_SECONDS': {
        title: "Recheck Interval",
        desc: "The time (in seconds) between periodic health audits. The system will inventory the active pool and ensure they are still alive, replacing any dead ones."
    },
    'CHECK_TIMEOUT_SECONDS': {
        title: "Check Timeout (sec)",
        desc: "The maximum time to wait for a proxy to respond during testing. A lower value ensures you only pick up snappy proxies, while a high value is forgiving to long-distance hops."
    },
    'MAX_CONCURRENT_CHECKS': {
        title: "Max Concurrent Checks",
        desc: "The maximum number of simultaneous network connections the proxy checker can spawn. Keep this reasonable (e.g. 50-100) to avoid locally exhausting your network adapter ports."
    },
    'MAX_SPEED_MS': {
        title: "Max Speed Threshold (ms)",
        desc: "Strict Speed Rejection Threshold. If set to 200, any proxy taking longer than 200ms to respond is instantly rejected and marked as 'Dead', even if it technically works. Set to 0 to disable."
    },
    'ANONYMITY_CHECK': {
        title: "Anonymity Check",
        desc: "The Stealth Shield. When enabled, the engine double-checks that the proxy actually hides your real IP address. Transparent proxies that leak your real IP will be instantly blocked."
    },
    'FAILOVER_MAX_RETRIES': {
        title: "Max Retries",
        desc: "The Failover limit. If an active proxy fails globally during browsing, the engine will swiftly switch to the next best proxy. This restricts how many times it can jump before halting."
    },
    'FAILOVER_RETRY_DELAY': {
        title: "Retry Delay (sec)",
        desc: "A modest breathing room (delay) before jumping to a new proxy after a previous failure during active failover hopping."
    },
    'DEAD_RETRY_AFTER_SECONDS': {
        title: "Dead Retry After",
        desc: "The Second Chance mechanic. Proxies marked as 'Dead' aren't always gone forever. This defines how many seconds they rest in the graveyard before being pulled out for another test."
    },
    'BLACKLIST_AFTER_FAILURES': {
        title: "Blacklist After Failures",
        desc: "The Final Strikeout. If a proxy receives a second chance and fails consecutively this many times, it is permanently deleted from the pool and never tried again."
    },
    'ADBLOCK_ENABLED': {
        title: "Ad Blocker Enabled",
        desc: "The smart DNS-level blocker toggle. Intercepts all SOCKS5/HTTP requests and drops connections to known trackers, ads, and malware domains listed in your adblock database."
    }
};

function initHelpTooltips() {
    document.querySelectorAll('.setting-row').forEach(row => {
        const input = row.querySelector('.cfg-input');
        const label = row.querySelector('label');
        if (!input || !label) return;
        
        const key = input.id.replace('cfg-', '');
        const info = SETTING_INFO[key];
        
        if (info) {
            // Native HTML hover tooltip
            label.title = info.title + " — " + info.desc;
            label.style.cursor = 'help';
            
            // Optional: Also put the title on the input itself
            input.title = info.desc;
        }
    });
}

// ── Window Controls ──
function minimize() { if (window.pywebview) pywebview.api.minimize(); }
function toggle_maximize() { if (window.pywebview) pywebview.api.toggle_maximize(); }
function close_app() { if (window.pywebview) pywebview.api.close(); }

// ══════════════════════════════════════════════
// Table Sorting Logic
// ══════════════════════════════════════════════
function initSorting() {
    document.querySelectorAll('th.sortable').forEach(th => {
        th.title = 'انقر لترتيب الجدول عبر هذا العامود';
        th.addEventListener('click', () => {
            const sortKey = th.getAttribute('data-sort');
            const tbody = th.closest('table').querySelector('tbody');
            if (!sortKey || !tbody) return;
            
            const tableId = tbody.id;
            if (!_sortState[tableId]) _sortState[tableId] = { col: null, asc: true };
            
            if (_sortState[tableId].col === sortKey) {
                _sortState[tableId].asc = !_sortState[tableId].asc;
            } else {
                _sortState[tableId].col = sortKey;
                _sortState[tableId].asc = true; // default asc
            }
            
            th.closest('tr').querySelectorAll('th').forEach(h => h.classList.remove('asc', 'desc'));
            th.classList.add(_sortState[tableId].asc ? 'asc' : 'desc');
            
            reRenderTable(tableId);
        });
    });
}

function sortArray(arr, state) {
    if (!state || !state.col) return arr;
    return arr.slice().sort((a, b) => {
        let valA = a[state.col];
        let valB = b[state.col];
        
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();
        
        if (valA === undefined || valA === null) valA = '';
        if (valB === undefined || valB === null) valB = '';
        
        if (valA < valB) return state.asc ? -1 : 1;
        if (valA > valB) return state.asc ? 1 : -1;
        return 0;
    });
}

function reRenderTable(tableId) {
    switch(tableId) {
        case 'clients-table-body': renderClients(_clientsCache); break;
        case 'proxy-table-body': renderProxyTable(_proxiesCache); break;
        case 'traffic-table-body': renderTrafficTable(_trafficCache); break;
        case 'top-proxies-body': renderAnalyticsTop(_analyticsTopCache); break;
        case 'country-stats-body': renderAnalyticsCountries(_analyticsCountriesCache); break;
    }
}

// ── Init ──
window.addEventListener('pywebviewready', () => {
    initHelpTooltips();
    initSorting();
    initQuickSettings();
    updateDashboard();
    updateInterval = setInterval(updateDashboard, 2000);
});

// Fallback for browser
if (!window.pywebview) {
    document.addEventListener('DOMContentLoaded', () => {
        initHelpTooltips();
        initSorting();
        initQuickSettings();
    });
    updateDashboard();
    updateInterval = setInterval(updateDashboard, 2000);
}
