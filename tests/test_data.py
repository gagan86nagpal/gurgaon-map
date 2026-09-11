"""Data invariants for every quote row and the built page. Pure Python, runs in well under a second."""
import json, glob, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
def check(cond, msg):
    if not cond: fails.append(msg)

rows = []
for f in sorted(glob.glob(f'{BASE}/agent_*.json')):
    data = json.load(open(f))
    check(isinstance(data, list), f'{f}: not a list')
    for q in data:
        tag = f"{os.path.basename(f)} [{q.get('sector')}] {str(q.get('project'))[:40]}"
        check(q.get('project') and q['project'] not in ('Project Name', 'project name'), f'{tag}: placeholder project name')
        check(re.match(r'https?://[^/]+\.[a-z]+/?', str(q.get('source_url', ''))) and '...' not in q.get('source_url', ''), f'{tag}: bad source_url {q.get("source_url")!r}')
        try:
            lo, hi = int(q['price_psf_min']), int(q['price_psf_max'])
            check(0 < lo <= hi, f'{tag}: price range {lo}-{hi}')
            check(2000 <= lo and hi <= 250000, f'{tag}: implausible ₹/sq ft {lo}-{hi}')
        except Exception:
            fails.append(f'{tag}: non-integer price')
        check(isinstance(q.get('sot'), dict) and q['sot'].get('label') and q['sot'].get('cls'), f'{tag}: missing sot annotation (run annotate_sot.py)')
        for c in q.get('configs') or []:
            check(isinstance(c.get('area'), int) and c['area'] >= 200 and float(c.get('price_cr', 0)) > 0, f'{tag}: bad config {c}')
            if isinstance(c.get('area'), int) and c['area'] >= 200 and float(c.get('price_cr', 0)) > 0:
                psf = c['price_cr'] * 1e7 / c['area']
                check(2000 <= psf <= 300000, f'{tag}: config implies ₹{psf:,.0f}/sq ft {c}')
        rows.append(q)
check(len(rows) >= 200, f'only {len(rows)} rows')

# built page carries the same rows and every quote's link
html_path = f'{BASE}/gurgaon-price-map-standalone.html'
check(os.path.exists(html_path), 'standalone html missing')
if os.path.exists(html_path):
    html = open(html_path).read()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    check(bool(m), 'embedded data block missing')
    if m:
        D = json.loads(m.group(1))
        check(len(D['quotes']) >= 200, f"page has only {len(D['quotes'])} quotes")
        for q in D['quotes']:
            check(q['source_url'].startswith('http'), f"page quote without link: {q['project']}")
            check(q['sector'] in D['sectors'], f"page quote in unmapped sector {q['sector']}: {q['project']}")
        for k, v in D['nostock'].items():
            check(k in D['sectors'], f'no-stock verdict for unmapped sector {k}')
    check('gtag/js?id=G-BQT0Z05NDL' in html, 'GA snippet missing')
    check('data-url=' in html and 'source_open' in html, 'project card click-through not wired')
    idx = f'{BASE}/index.html'
    if os.path.exists(idx):
        check(open(idx).read() == html, 'index.html differs from the standalone build — copy it before committing')

if fails:
    print(f'FAIL {len(fails)} problem(s):'); [print('  -', x) for x in fails[:40]]; sys.exit(1)
print(f'ok: {len(rows)} rows, page consistent')
