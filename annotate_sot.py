"""Stamp every quote row with an explicit source-of-truth (`sot`) field and write SOURCES.md.

`sot.cls` is the class of source the ₹/sq ft figure was read from, `sot.domain` the site, `sot.what` what the
number means on that site. Run after any edit to agent_*.json; idempotent.
"""
import json, glob, re, os, collections
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))

# what each source's number actually is — this is the part a reader needs to judge it
CLASSES = {
    'squareyards.com':      ('portal', 'Square Yards', "project page 'current asking price' — listing asks blended with registered-transaction data, updated quarterly"),
    '99acres.com':          ('portal', '99acres', 'listing-based project/locality average asking price'),
    'magicbricks.com':      ('portal', 'MagicBricks', 'listing-based project average asking price'),
    'housing.com':          ('portal', 'Housing.com', 'listing-based project average asking price'),
    'nobroker.in':          ('portal', 'NoBroker', 'listing-based locality average'),
    'business-standard.com': ('news', 'Business Standard', 'reported sale / developer-stated price'),
    'm3mproperties.com':    ('developer', 'M3M (developer site)', "developer's own published price"),
    'atsgrandstandgurgaon.in': ('project-site', 'ATS Grandstand project site', 'quoted unit price ÷ super area (project marketing site; not the atshomekraft.com corporate domain)'),
    'prestigesector92gurgaon.com': ('project-site', 'Prestige Sector 92 project site', 'quoted unit price ÷ super area (project marketing site)'),
}
BROKER = ('megarealtymax.com', 'bigestate.io', 'opulnzabode.com', 'superluxere.com', 'samagrarealty.in', 'premiumrealtyinfra.com')

def domain(u):
    try: d = urlparse(u).netloc.lower()
    except Exception: return ''
    return re.sub(r'^(www|m)\.', '', d)

def sot_for(q):
    d = domain(q.get('source_url', ''))
    if d in CLASSES:
        cls, label, what = CLASSES[d]
    elif d in BROKER or q.get('source_type') in ('broker', 'broker microsite', 'blog'):
        cls, label, what = 'broker', d, 'broker/channel-partner quote — quoted unit price ÷ super area'
    elif q.get('source_type') == 'developer':
        cls, label, what = 'developer', f"{q.get('developer') or d} (developer site)", "developer's own published price (usually a 'from' price divided by the stated unit size)"
    elif q.get('source_type') == 'project-site':
        cls, label, what = 'project-site', f"{q.get('project', '')[:28]} project site", 'quoted unit price ÷ stated super area on the project marketing site'
    elif q.get('source_type') == 'news':
        cls, label, what = 'news', q.get('publisher') or d, 'figure stated in a press report (developer quote, reported deal or market data)'
    else:
        cls, label, what = 'other', d, q.get('source_type', '')
    return {'cls': cls, 'label': label, 'domain': d, 'what': what}

rows = []
for f in sorted(glob.glob(f'{BASE}/agent_*.json')):
    data = json.load(open(f))
    for q in data:
        q['sot'] = sot_for(q); q['_f'] = os.path.basename(f)
    rows += data
    json.dump([{k: v for k, v in q.items() if k != '_f'} for q in data], open(f, 'w'), indent=1, ensure_ascii=False)

GENERIC = re.compile(r'\b(avg|average|builder floors?|apartments?/floors|flats avg|apartments avg|floors / apartments|price band|mixed apartments)\b', re.I)
def is_generic(q): return (q.get('developer') or '').strip().lower() in ('', 'various', 'multiple', 'n/a') and bool(GENERIC.search(q.get('project', '')))
premium, _seen = [], set()
for q in rows:
    k = (q['sector'].strip().upper().replace('SECTOR', '').replace(' ', '').lstrip('-'), q['project'].lower())
    if is_generic(q) or k in _seen: continue
    _seen.add(k); premium.append(q)
by_label = collections.Counter(q['sot']['label'] for q in premium)
by_cls = collections.Counter(q['sot']['cls'] for q in premium)
n = len(premium)

def pct(x): return f'{100 * x / n:.1f}%'
lines = ['# Source of truth for every price on the map', '',
         f'{n} premium-project quotes (locality-average rows excluded). Each row in `agent_*.json` carries a `sot` field with the same information; the map shows the source label on every quote and links the page it was read from.', '',
         '## Where the numbers come from', '', '| Source | Quotes | Share | What the figure is |', '|---|---:|---:|---|']
for label, c in by_label.most_common():
    what = next(q['sot']['what'] for q in premium if q['sot']['label'] == label)
    lines.append(f'| {label} | {c} | {pct(c)} | {what} |')
lines += ['', '| Class | Quotes | Share |', '|---|---:|---:|'] + [f'| {k} | {c} | {pct(c)} |' for k, c in by_cls.most_common()]
lines += ['', f'Rows with a second, independent source recorded: {sum(1 for q in premium if q.get("second_source_url"))} ({pct(sum(1 for q in premium if q.get("second_source_url")))}).',
          f'Confidence grades among audited rows: ' + ', '.join(f'{g} {c}' for g, c in sorted(collections.Counter(q.get("confidence") for q in premium if q.get("confidence")).items())) + '.', '',
          '## Caveats you should know', '',
          '- Square Yards dominates because it is the only major portal whose project pages could be fetched programmatically during the build (99acres, MagicBricks and Housing block automated access). Its "current asking price" blends listing asks with government-registered transaction data, so it is usually closer to achieved prices than a pure listing average — but it is still one vendor\'s model.',
          '- 99acres figures are pure listing averages (what sellers ask, not what buyers pay).',
          '- Developer and project-site quotes are the developer\'s own asking price for a specific configuration (unit price ÷ super area). They are exact for that unit but represent the launch/primary market, not resale.',
          '- Broker microsites are channel-partner pages; the arithmetic was verified but the price is whatever the broker chose to advertise.',
          '- Audit notes and second-source links on individual quotes are in the map\'s inspector and in the `audit` / `second_source_url` fields.', '',
          '## Every quote', '', '| Sector | Project | ₹/sq ft | Source | Grade | As of | Link |', '|---|---|---:|---|:-:|---|---|']
def sk(q):
    m = re.match(r'(\D*)(\d+)(.*)', q['sector']); return (m.group(1), int(m.group(2)), m.group(3)) if m else (q['sector'], 0, '')
for q in sorted(premium, key=lambda q: (sk(q), q['project'])):
    p = f"{q['price_psf_min']:,}" + (f"–{q['price_psf_max']:,}" if q['price_psf_max'] != q['price_psf_min'] else '')
    lines.append(f"| {q['sector']} | {q['project']} | {p} | {q['sot']['label']} | {q.get('confidence', '–')} | {q.get('as_of', '')} | [{q['sot']['domain']}]({q['source_url']}) |")
open(f'{BASE}/SOURCES.md', 'w').write('\n'.join(lines) + '\n')
print('premium rows', n, '|', dict(by_label.most_common()), '|', dict(by_cls))
