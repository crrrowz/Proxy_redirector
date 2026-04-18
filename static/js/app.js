let updateInterval = null;

async function fetchJSON(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) return null;
        return await res.json();
    } catch {
        return null;
    }
}

async function startEngine() {
    await fetch('/api/start', { method: 'POST' });
    updateDashboard();
}

async function stopEngine() {
    await fetch('/api/stop', { method: 'POST' });
    updateDashboard();
}

async function clearTraffic() {
    await fetch('/api/traffic/clear', { method: 'POST' });
    updateDashboard();
}

function renderServerInfo(status) {
    const srvHtml = `
        <div class="info-row">
            <span class="info-label">SOCKS5 Server</span>
            <span class="badge ${status.socks5_ok ? 'on' : 'off'}">
                0.0.0.0:${status.socks5_port}
            </span>
        </div>
        <div class="info-row">
            <span class="info-label">HTTP Server (Phones)</span>
            <span class="badge ${status.http_ok ? 'on' : 'off'}">
                0.0.0.0:${status.http_port}
            </span>
        </div>
        <div class="info-row">
            <span class="info-label">Auth Status</span>
            <span style="color: ${status.auth_enabled ? 'var(--warning)' : 'var(--text-muted)'}">
                ${status.auth_enabled ? `${status.auth_user} / ${status.auth_pass}` : 'Disabled'}
            </span>
        </div>
    `;
    document.getElementById('server-info').innerHTML = srvHtml;

    let ipsHtml = '';
    if (status.local_ips && status.local_ips.length > 0) {
        status.local_ips.forEach(ip => {
            ipsHtml += `<div class="code-block">${ip}:${status.http_port} (HTTP)</div>`;
            ipsHtml += `<div class="code-block">${ip}:${status.socks5_port} (SOCKS5)</div>`;
        });
    } else {
        ipsHtml = `<div class="info-label">No local IP found</div>`;
    }
    document.getElementById('network-ips').innerHTML = ipsHtml;

    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    if (status.running) {
        btnStart.style.display = 'none';
        btnStop.style.display = 'block';
        document.getElementById('engine-status-text').innerText = 'Engine Running';
        document.getElementById('engine-status-text').style.color = 'var(--success)';
    } else {
        btnStart.style.display = 'block';
        btnStop.style.display = 'none';
        document.getElementById('engine-status-text').innerText = 'Engine Stopped';
        document.getElementById('engine-status-text').style.color = 'var(--danger)';
    }
}

function renderProxyPool(status, proxies) {
    const pool = status.pool || {};
    document.getElementById('pool-stats').innerText = 
        `${pool.alive || 0} alive | ${pool.dead_retryable || 0} retry | ${pool.blacklisted || 0} blocked | ${pool.unchecked || 0} max`;

    if (status.active_proxy) {
        const ap = status.active_proxy;
        document.getElementById('active-proxy').innerHTML = 
            `<strong>${ap.ip}:${ap.port}</strong> <span class="badge on">${ap.type}</span> | ${ap.speed_ms || '--'}ms | Switches: ${ap.switches || 0}`;
    } else {
        document.getElementById('active-proxy').innerText = '-- searching...';
    }

    const tbody = document.getElementById('proxy-table-body');
    if (!proxies || proxies.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center">No proxies loaded</td></tr>`;
        return;
    }

    let html = '';
    proxies.forEach((p, i) => {
        const marker = p.active ? '► ' : '';
        const statusBadge = p.alive ? '<span class="badge on">UP</span>' : '<span class="badge off">DN</span>';
        const spd = p.speed_ms ? Math.round(p.speed_ms)+'ms' : '--';
        html += `
            <tr style="${p.active ? 'background: rgba(59, 130, 246, 0.1)' : ''}">
                <td>${marker}${i+1}</td>
                <td>${p.ip}:${p.port}</td>
                <td>${p.type}</td>
                <td>${statusBadge}</td>
                <td>${spd}</td>
                <td>${p.score.toFixed(1)}</td>
                <td>${p.failures}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderClients(clients) {
    const tbody = document.getElementById('clients-table-body');
    document.getElementById('clients-count').innerText = clients ? clients.length : 0;

    if (!clients || clients.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align:center">No active connections</td></tr>`;
        return;
    }

    let html = '';
    clients.forEach(c => {
        const pClass = c.protocol === 'HTTP' ? 'http' : 'socks5';
        let target = c.target;
        if (target.length > 40) target = target.substring(0, 37) + '...';
        html += `
            <tr>
                <td style="font-family: monospace">${c.ip}</td>
                <td><span class="badge ${pClass}">${c.protocol}</span></td>
                <td>${target}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderTraffic(traffic) {
    if (!traffic) return;

    const stats = traffic.stats || {};
    document.getElementById('traffic-stats').innerText = 
        `${stats.total_requests || 0} req | ${stats.total_bytes_human || '0 B'} | ${stats.unique_clients || 0} clients`;

    const tbody = document.getElementById('traffic-table-body');
    const recent = traffic.recent || [];
    
    if (recent.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center">No traffic recorded</td></tr>`;
        return;
    }

    let html = '';
    recent.slice().reverse().forEach(r => {
        const icon = r.status === 'success' ? '✓' : '✗';
        const color = r.status === 'success' ? 'var(--success)' : 'var(--danger)';
        const pClass = r.protocol === 'HTTP' ? 'http' : 'socks5';
        let target = r.target;
        if (target.length > 35) target = target.substring(0, 32) + '...';
        
        html += `
            <tr>
                <td style="color:var(--text-muted)">${r.time}</td>
                <td style="color:${color}; font-weight:bold">${icon}</td>
                <td style="font-family: monospace">${r.client_ip}</td>
                <td><span class="badge ${pClass}">${r.protocol}</span></td>
                <td>${r.method}</td>
                <td>${target}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

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
}

// Controls
function minimize() { if(window.pywebview) pywebview.api.minimize(); }
function toggle_maximize() { if(window.pywebview) pywebview.api.toggle_maximize(); }
function close_app() { if(window.pywebview) pywebview.api.close(); }

// Init
window.addEventListener('pywebviewready', () => {
    updateDashboard();
    updateInterval = setInterval(updateDashboard, 2000);
});

// Fallback for browser testing
if (!window.pywebview) {
    updateDashboard();
    updateInterval = setInterval(updateDashboard, 2000);
}
