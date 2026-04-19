import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove malformed thead
html = re.sub(r'<thead data-sort="[^"]+" class="sortable">', '<thead>', html)

# Fix proxy table headers
html = html.replace('<th data-sort="ipport" class="sortable">IP:Port</th>', '<th data-sort="ip" class="sortable">IP:Port</th>')
html = html.replace('<th data-sort="status" class="sortable">Status</th>', '<th data-sort="alive" class="sortable">Status</th>')

# Fix client IP header
html = html.replace('<th>Client IP</th>', '<th data-sort="ip" class="sortable">Client IP</th>')

# Fix traffic Time header
html = html.replace('<th style="width:75px">Time</th>', '<th style="width:75px" data-sort="time" class="sortable">Time</th>')

# Fix block Rules domain header
html = html.replace('<th>Domain / Pattern</th>', '<th data-sort="domain" class="sortable">Domain / Pattern</th>')

# Fix top proxies ID header
html = html.replace('<th>Proxy ID (IP:Port)</th>', '<th data-sort="id" class="sortable">Proxy ID (IP:Port)</th>')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML fixed")
