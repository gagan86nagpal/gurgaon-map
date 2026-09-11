import json, glob, math, re, html, sys, os

BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
OSM = f'{BASE}/osm'
geo = json.load(open(f'{BASE}/sectors.json'))

# canvas: Gurugram plus the Delhi strip that matters to it (IGI, Aerocity, Dwarka) — nothing further
LAT_TOP, LON_LEFT, LAT_BOT, LON_RIGHT = 28.615, 76.88, 28.36, 77.15
KX = math.cos(math.radians(28.45))
def proj(lon, lat):
    return ((lon - LON_LEFT) * KX * 4000, (LAT_TOP - lat) * 4000)
CW, CH = proj(LON_RIGHT, LAT_BOT)
CANVAS = [0, 0, math.ceil(CW), math.ceil(max(CH, geo['bbox'][1] + geo['bbox'][3]))]
MARGIN = 60
def inside(x, y, m=MARGIN):
    return -m <= x <= CANVAS[2] + m and -m <= y <= CANVAS[3] + m

def load(name):
    try:
        return json.load(open(f'{OSM}/{name}'))['elements']
    except Exception:
        return []

def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-12
    idx, dmax = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > dmax:
            idx, dmax = i, d
    if dmax > tol:
        return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)
    return [pts[0], pts[-1]]

def simplify_ring(ring, tol):
    # closed ring: split at the vertex farthest from the start so neither half is degenerate
    if len(ring) < 5:
        return ring
    x0, y0 = ring[0]
    far = max(range(1, len(ring) - 1), key=lambda i: math.hypot(ring[i][0] - x0, ring[i][1] - y0))
    return simplify(ring[:far + 1], tol)[:-1] + simplify(ring[far:], tol)

def path_of(pts, close=False):
    return 'M' + 'L'.join(f'{x:.0f},{y:.0f}' for x, y in pts) + ('Z' if close else '')

def runs_inside(pts):
    """Split a projected polyline into the pieces that lie on the canvas."""
    out, cur = [], []
    for p in pts:
        if inside(*p):
            cur.append(p)
        else:
            if cur: cur.append(p)          # keep one point past the edge so the line exits cleanly
            if len(cur) > 1: out.append(cur)
            cur = [p] if cur else []
            if not inside(*p): cur = [p]
    if len(cur) > 1: out.append(cur)
    return [r for r in out if any(inside(*p) for p in r)]

def rings_of(e):
    if e['type'] == 'way':
        pts = [(p['lon'], p['lat']) for p in e.get('geometry', [])]
        return [pts] if len(pts) >= 4 else []
    segs = []
    for m in e.get('members', []):
        if m['type'] == 'way' and m.get('role') in ('outer', ''):
            pts = [(p['lon'], p['lat']) for p in m.get('geometry', [])]
            if len(pts) >= 2: segs.append(pts)
    rings = []
    while segs:
        ring = segs.pop(0); changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]: ring += s[1:]; segs.pop(i); changed = True; break
                if s[-1] == ring[-1]: ring += s[-2::-1]; segs.pop(i); changed = True; break
                if s[-1] == ring[0]: ring = s[:-1] + ring; segs.pop(i); changed = True; break
                if s[0] == ring[0]: ring = s[::-1][:-1] + ring; segs.pop(i); changed = True; break
        if len(ring) >= 4: rings.append(ring)
    return rings

# ---- quotes -------------------------------------------------------------
quotes = []
for f in sorted(glob.glob(f'{BASE}/agent_*.json')):
    for q in json.load(open(f)):
        s = str(q.get('sector', '')).strip().upper().replace('SECTOR', '').replace(' ', '')
        s = re.sub(r'^-', '', s)
        q['sector'] = s
        try:
            q['price_psf_min'] = int(q['price_psf_min']); q['price_psf_max'] = int(q['price_psf_max'])
        except Exception:
            continue
        if q['price_psf_min'] <= 0:
            continue
        quotes.append(q)
# data-source class, in order of directness (rank 0 = closest to the developer's own price)
SRC = [('developer', 'Developer & project sites'), ('news', 'Press reports'), ('squareyards', 'Square Yards'),
       ('acres99', '99acres'), ('mbh', 'MagicBricks / Housing / NoBroker'), ('broker', 'Broker microsites'), ('other', 'Other')]
def src_class(q):
    sot = q.get('sot') or {}; cls, dom = sot.get('cls', ''), sot.get('domain', '')
    if cls in ('developer', 'project-site') or q.get('source_type') in ('developer', 'project-site'): return 'developer'
    if cls == 'news' or q.get('source_type') == 'news': return 'news'
    if 'squareyards' in dom: return 'squareyards'
    if '99acres' in dom: return 'acres99'
    if any(d in dom for d in ('magicbricks', 'housing.com', 'nobroker')): return 'mbh'
    if cls == 'broker': return 'broker'
    return 'other'
seen = set(); dedup = []
for q in quotes:
    q['src'] = src_class(q)
    k = (q['sector'], q['project'].lower(), q['src'])   # one quote per project per source class; classes stack in the panel
    if k in seen: continue
    seen.add(k); dedup.append(q)
quotes = dedup

def bucket(status):
    s = (status or '').lower()
    if 'resale' in s: return 'resale'
    if 'launch' in s or 'pre' in s: return 'launch'
    if 'under' in s or 'construction' in s: return 'uc'
    if 'ready' in s or 'complete' in s or 'deliver' in s or 'possession' in s: return 'ready'
    return 'uc'
for q in quotes:
    q['bucket'] = bucket(q.get('status'))

# Locality-wide "Sector N apartments avg / builder floors" rows are not premium projects. They are kept only as
# context for sectors that have no branded project, where the sector is shown as no-premium-stock instead.
GENERIC = re.compile(r'\b(avg|average|builder floors?|apartments?/floors|flats avg|apartments avg|floors / apartments|price band|mixed apartments)\b', re.I)
for q in quotes:
    q['generic'] = bool((q.get('developer') or '').strip().lower() in ('', 'various', 'multiple', 'n/a') and GENERIC.search(q.get('project', '')))
generic_only = {}
for q in quotes:
    if q['generic']: generic_only.setdefault(q['sector'], []).append(q)
for s in list(generic_only):
    if any(not q['generic'] for q in quotes if q['sector'] == s): del generic_only[s]
quotes = [q for q in quotes if not q['generic']]

# ---- roads --------------------------------------------------------------
GOLF = re.compile(r'golf course', re.I)
roads = []
def road_class(hw, nm):
    if GOLF.search(nm): return 'gc'
    if 'Dwarka' in nm and 'Express' in nm: return 'mw'
    return {'motorway': 'mw', 'trunk': 'tr', 'primary': 'pr', 'secondary': 'sc'}.get(hw, 'tt')
for fname, tol in (('roads_ext.json', 0.6), ('roads_minor.json', 1.0)):
    for e in load(fname):
        nm = e['tags'].get('name') or ''
        cls = road_class(e['tags'].get('highway', ''), nm)
        pts = [proj(p['lon'], p['lat']) for p in e.get('geometry', [])]
        for run in runs_inside(pts):
            run = simplify(run, tol)
            if len(run) >= 2:
                roads.append({'c': cls, 'n': nm, 'd': path_of(run)})
ORDER = {'tt': 0, 'sc': 1, 'pr': 2, 'tr': 3, 'mw': 4, 'gc': 5}
roads.sort(key=lambda r: ORDER[r['c']])

# clickable corridors: merge OSM segment names into the names people use
DISPLAY = {
    'Delhi-Gurugram Expressway': 'NH-48 · Delhi–Gurugram Expressway', 'Mahipalpur Flyover': 'NH-48 · Delhi–Gurugram Expressway',
    'Dwarka Expressway': 'Dwarka Expressway', 'Golf Course Road': 'Golf Course Road', 'Golf Course Road Underpass': 'Golf Course Road',
    'Golf Course Extension Road': 'Golf Course Extension Road / SPR', 'Urban Extension Road-II': 'Urban Extension Road-II (Delhi, NH-344M)',
    'Sohna Road': 'Sohna Road (NH-248A)', 'Shubhash Chowk Underpass': 'Sohna Road (NH-248A)', 'Vatika Flyover': 'NH-48 · Delhi–Gurugram Expressway',
    'Gurgaon Rewari Narnaul Singhana Road': 'Pataudi Road (Gurgaon–Rewari)', 'Mehrauli Gurgaon Road': 'MG Road (Mehrauli–Gurgaon)',
    'Mehrauli-Gurgaon Road': 'MG Road (Mehrauli–Gurgaon)', 'Acharya Shri Tulsi Marg': 'MG Road (Mehrauli–Gurgaon)',
    'Faridabad-Gurgaon Road': 'Faridabad Road', 'Link to Faridabad Road': 'Faridabad Road', 'Old Delhi Gurgaon Road': 'Old Delhi–Gurgaon Road',
    'Rajiv Chowk Underpass': 'NH-48 · Delhi–Gurugram Expressway', 'Rao Tula Ram Flyover': 'NH-48 · Delhi–Gurugram Expressway',
    'Gurugram New Sector Road Flyover': 'Dwarka Expressway', 'Najafgarh Daurala Road': 'Najafgarh Road', 'Nelson Mandela Marg': 'Nelson Mandela Marg',
    'Palam Marg': 'Palam Marg', 'Dwarka-Palam Road': 'Dwarka–Palam Road', 'Bajghera Road': 'Bajghera Road', 'Carterpuri Road': 'Carterpuri Road',
    'Basai Road': 'Basai Road', 'Hero Honda Chowk': 'NH-48 · Delhi–Gurugram Expressway',
}
for r in roads:
    if r['c'] in ('mw', 'tr', 'pr', 'gc') or r['n'] in DISPLAY:
        dn = DISPLAY.get(r['n'])
        if not dn and r['n'] and not re.search(r'flyover|underpass|^road\b|link', r['n'], re.I): dn = r['n']
        r['k'] = dn or ''
    else:
        r['k'] = ''


ROAD_LABELS = [
    ('Faridabad Rd', 77.128, 28.448, 62),
    ('Dwarka Expressway', 76.975, 28.500, -52),
    ('Dwarka Expressway', 77.035, 28.532, -30),
    ('NH-48 · Delhi–Jaipur', 77.045, 28.462, -38),
    ('NH-48 → Delhi', 77.113, 28.523, -48),
    ('Sohna Road', 77.045, 28.418, 48),
    ('Golf Course Rd', 77.098, 28.455, 62),
    ('Golf Course Ext. Rd', 77.085, 28.405, 40),
    ('Southern Peripheral Rd', 77.020, 28.3935, 8),
    ('Pataudi Road', 76.960, 28.440, 20),
    ('Old Delhi Rd', 77.052, 28.495, -30),
    ('MG Road', 77.093, 28.478, 24),
]
road_labels = [{'t': t, 'x': round(proj(lon, lat)[0]), 'y': round(proj(lon, lat)[1]), 'r': r} for t, lon, lat, r in ROAD_LABELS]

# ---- Delhi border, airport, green ---------------------------------------
ctx = load('ctx.json')
border = []
for e in ctx:
    if e['type'] == 'relation' and e['tags'].get('name') == 'Delhi':
        for m in e.get('members', []):
            if m['type'] != 'way': continue
            pts = [proj(p['lon'], p['lat']) for p in m.get('geometry', [])]
            for run in runs_inside(pts):
                run = simplify(run, 0.8)
                if len(run) >= 2: border.append({'d': path_of(run), 'pts': run})
airport = {'rings': [], 'runways': [], 'terminals': []}
for e in ctx:
    t = e['tags']
    if t.get('aeroway') == 'aerodrome' and 'Indira' in (t.get('name') or ''):
        for r in rings_of(e):
            pr = simplify_ring([proj(*p) for p in r], 1.0)
            if len(pr) >= 4: airport['rings'].append(path_of(pr, True))
    elif t.get('aeroway') == 'runway':
        pts = [proj(p['lon'], p['lat']) for p in e.get('geometry', [])]
        if len(pts) >= 2 and any(inside(*p) for p in pts): airport['runways'].append(path_of(pts))
    elif t.get('aeroway') == 'terminal' and 'Freight' not in (t.get('name') or ''):
        pts = [proj(p['lon'], p['lat']) for p in e.get('geometry', [])]
        if len(pts) >= 4: airport['terminals'].append(path_of(pts, True))
green = []
for e in load('green.json'):
    kind = 'golf' if e['tags'].get('leisure') == 'golf_course' else 'park'
    for r in rings_of(e):
        pr = simplify_ring([proj(*p) for p in r], 0.8)
        if len(pr) >= 4 and any(inside(*p) for p in pr):
            green.append({'k': kind, 'n': e['tags'].get('name') or '', 'd': path_of(pr, True)})

# ---- metro ---------------------------------------------------------------
METRO_LINES = {  # one direction per line; official colours
    447210: ('Yellow Line', '#f2c200'),
    447209: ('Blue Line', '#3b6fd9'),
    2535798: ('Airport Express', '#f07d1a'),
    4481323: ('Rapid Metro', '#2a9d8f'),
}
KEY_STATIONS = {'Millennium City Centre Gurugram', 'Sikanderpur', 'IGI Airport', 'Dwarka Sector 21', 'IFFCO Chowk', 'M G Road',
                'Delhi Aerocity', 'Sector 53-54', 'Sector 55–56', 'Terminal 1 IGI Airport', 'Guru Dronacharya', 'Dwarka'}
metro, stations, seen_st = [], [], set()
for e in load('metro.json'):
    if e['id'] not in METRO_LINES: continue
    name, colour = METRO_LINES[e['id']]
    for m in e.get('members', []):
        if m['type'] == 'way':
            pts = [proj(p['lon'], p['lat']) for p in m.get('geometry', [])]
            for run in runs_inside(pts):
                run = simplify(run, 0.6)
                if len(run) >= 2: metro.append({'l': name, 'c': colour, 'd': path_of(run)})
        elif m['type'] == 'node' and m.get('role', '').startswith('stop'):
            pass
# stations: from the POI pull (railway=station, subway), deduped by name
for e in load('poi_raw.json'):
    t = e['tags']
    if t.get('railway') != 'station' or t.get('station') != 'subway': continue
    nm = (t.get('name') or '').replace(' (Blue Line)', '').replace(' (Grey Line)', '').replace(' RMRG Station', '').replace(' Metro Station', '').replace(' Station', '')
    if nm in seen_st or not nm: continue
    lat = e.get('lat') or e.get('center', {}).get('lat'); lon = e.get('lon') or e.get('center', {}).get('lon')
    x, y = proj(lon, lat)
    if not inside(x, y, 0): continue
    # skip lines we do not draw (Grey/Magenta/Pink) by geography: stations west of Dwarka Sec 21 on the Grey line, T1/Vasant Vihar on Magenta
    if nm in ('Najafgarh', 'Dhansa Bus Stand', 'Nangli', 'Vasant Vihar', 'Shankar Vihar', 'Sadar Bazar Cantonment', 'Palam', 'Dashrath Puri', 'Dabri Mor - Janakpuri South', 'Terminal 1 IGI Airport', 'Ghitorni', 'Arjan Garh', 'Sultanpur', 'Dwarka Mor', 'Nawada', 'Uttam Nagar East', 'Uttam Nagar West', 'Janakpuri West', 'Naraina Vihar', 'Delhi Cantt', 'Sector 53/54 Metro Station'):
        if nm not in ('Ghitorni', 'Arjan Garh', 'Sultanpur', 'Terminal 1 IGI Airport'): continue
    seen_st.add(nm)
    stations.append({'n': nm.replace('Millennium City Centre Gurugram', 'Millennium City Centre (HUDA CC)'), 'x': round(x), 'y': round(y), 'k': 1 if nm in KEY_STATIONS else 2})

# ---- landmarks -----------------------------------------------------------
# (name, lat, lon, category, tier) — tier 1 always visible, 2 from ~1.6x zoom, 3 from ~2.8x
LANDMARKS = [
    ('IGI Airport · Terminal 3', 28.5557, 77.0844, 'air', 1),
    ('Terminal 1', 28.5640, 77.1176, 'air', 1),
    ('Aerocity', 28.5488, 77.1208, 'office', 2),
    ('Yashobhoomi convention centre', 28.5525, 77.0429, 'civic', 2),
    ('Ambience Mall', 28.5042, 77.0968, 'mall', 1),
    ('DLF Cyber City', 28.4942, 77.0921, 'office', 1),
    ('DLF Cyber Hub', 28.4963, 77.0892, 'mall', 2),
    ('DLF Downtown', 28.5036, 77.0952, 'office', 3),
    ('One Horizon Center', 28.4515, 77.0973, 'office', 1),
    ('Medanta', 28.4635, 77.0945, 'hosp', 1),
    ('Fortis Memorial', 28.4568, 77.0729, 'hosp', 1),
    ('Artemis Hospital', 28.4312, 77.0722, 'hosp', 1),
    ('Paras Hospital', 28.4510, 77.0876, 'hosp', 1),
    ('Max Hospital', 28.4613, 77.0747, 'hosp', 2),
    ('CK Birla Hospital', 28.4237, 77.0614, 'hosp', 2),
    ('Park Hospital', 28.4201, 77.0487, 'hosp', 2),
    ('Manipal (Columbia Asia) Palam Vihar', 28.5092, 77.0414, 'hosp', 2),
    ('Manipal Hospital Dwarka', 28.5929, 77.0638, 'hosp', 2),
    ('Kingdom of Dreams', 28.4681, 77.0691, 'civic', 1),
    ('Signature Tower', 28.4665, 77.0581, 'office', 2),
    ('Unitech Cyber Park', 28.4431, 77.0561, 'office', 2),
    ('Candor TechSpace', 28.4253, 77.0313, 'office', 2),
    ('Vatika Business Park', 28.4060, 77.0446, 'office', 2),
    ('Omaxe Celebration Mall', 28.4274, 77.0361, 'mall', 2),
    ('Reach Airia Mall', 28.3831, 77.0526, 'mall', 2),
    ('AIPL Joy Street', 28.3921, 77.0594, 'mall', 3),
    ('M3M Corner Walk', 28.4015, 77.0076, 'mall', 3),
    ('South Point Mall', 28.4480, 77.0992, 'mall', 3),
    ('Global Foyer', 28.4605, 77.0950, 'mall', 3),
    ('DLF Galleria Market', 28.4673, 77.0816, 'mall', 2),
    ('MG Road malls (Metropolitan · Sahara · Mega)', 28.4790, 77.0850, 'mall', 2),
    ('DLF Golf & Country Club', 28.4555, 77.1070, 'golf', 1),
    ('Kherki Daula toll', 28.3954, 76.9820, 'toll', 1),
    ('IFFCO Chowk', 28.4792, 77.0705, 'junction', 1),
    ('Rajiv Chowk', 28.4475, 77.0330, 'junction', 1),
    ('Hero Honda Chowk', 28.4360, 77.0103, 'junction', 1),
    ('Subhash Chowk', 28.4277, 77.0371, 'junction', 2),
    ('Gurgaon railway station', 28.4855, 77.0087, 'rail', 2),
    ('Garhi Harsaru Jn', 28.4383, 76.9307, 'rail', 3),
    ('Bijwasan station', 28.5370, 77.0513, 'rail', 3),
]
landmarks = []
for n, lat, lon, cat, tier in LANDMARKS:
    x, y = proj(lon, lat)
    landmarks.append({'n': n, 'x': round(x), 'y': round(y), 'c': cat, 't': tier})

# "Entry to Delhi": where a major road crosses the state line
def seg_intersect(p1, p2, p3, p4):
    d = (p2[0]-p1[0])*(p4[1]-p3[1]) - (p2[1]-p1[1])*(p4[0]-p3[0])
    if abs(d) < 1e-9: return None
    t = ((p3[0]-p1[0])*(p4[1]-p3[1]) - (p3[1]-p1[1])*(p4[0]-p3[0])) / d
    u = ((p3[0]-p1[0])*(p2[1]-p1[1]) - (p3[1]-p1[1])*(p2[0]-p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))
ENTRY_NAMES = {'NH-48': 'Sirhaul (NH-48)', 'Delhi-Gurugram Expressway': 'Sirhaul (NH-48)', 'Dwarka Expressway': 'Bijwasan (Dwarka Expwy)', 'Old Delhi': 'Kapashera border', 'MG Road': 'Aya Nagar (MG Road)', 'Mehrauli': 'Aya Nagar (MG Road)', 'Tulsi Marg': 'Aya Nagar (MG Road)'}
entries = []
border_segs = [(r['pts'][i], r['pts'][i+1]) for r in border for i in range(len(r['pts'])-1)]
for fname in ('roads_ext.json',):
    for e in load(fname):
        hw = e['tags'].get('highway', '')
        nm = e['tags'].get('name') or e['tags'].get('ref') or ''
        if hw not in ('motorway', 'trunk', 'primary'): continue
        pts = [proj(p['lon'], p['lat']) for p in e.get('geometry', [])]
        for i in range(len(pts)-1):
            for s in border_segs:
                X = seg_intersect(pts[i], pts[i+1], *s)
                if X and inside(*X, 0):
                    label = next((v for k, v in ENTRY_NAMES.items() if k.lower() in nm.lower()), None)
                    if not label and 'NH 48' in nm.replace('-', ' '): label = 'Sirhaul'
                    if not label and not nm: continue
                    entries.append({'x': round(X[0]), 'y': round(X[1]), 'n': label or nm, 'major': hw == 'motorway' or bool(label)})
# Old Delhi Road is only a secondary road where it crosses the line, so the Kapashera crossing is placed by hand (toll booth position)
kx, ky = proj(77.0811, 28.5193)
entries.append({'x': round(kx), 'y': round(ky), 'n': 'Kapashera border (Old Delhi Rd)', 'major': True})
# collapse near-duplicate crossings (dual carriageways cross twice)
ded = []
for en in sorted(entries, key=lambda e: (not e['major'], e['n'])):
    if any(math.hypot(en['x']-d['x'], en['y']-d['y']) < 30 for d in ded): continue
    ded.append(en)
entries = ded

AREAS = [  # named neighbourhoods and Delhi-side places, drawn as quiet italic labels
    ('Dwarka (Delhi)', 28.5990, 77.0430, 1), ('Delhi Cantt', 28.5980, 77.1240, 1), ('Palam', 28.5920, 77.0830, 2), ('Vasant Kunj', 28.5290, 77.1490, 1),
    ('Kapashera', 28.5300, 77.0870, 2), ('Bijwasan', 28.5330, 77.0430, 2), ('Samalkha', 28.5346, 77.0895, 3), ('Mahipalpur', 28.5440, 77.1250, 2),
    ('DLF Phase 1', 28.4745, 77.0985, 2), ('DLF Phase 2', 28.4890, 77.0870, 2), ('DLF Phase 3', 28.4930, 77.1000, 2), ('DLF Phase 4', 28.4625, 77.0900, 2), ('DLF Phase 5', 28.4470, 77.1030, 2),
    ('Sushant Lok I', 28.4634, 77.0785, 2), ('Sushant Lok III', 28.4208, 77.0811, 3), ('South City I', 28.4570, 77.0649, 2), ('South City II', 28.4184, 77.0480, 2),
    ('Palam Vihar', 28.5062, 77.0387, 2), ('Nirvana Country', 28.4150, 77.0654, 2), ('Mayfield Garden', 28.4265, 77.0620, 3), ('Wazirabad', 28.4338, 77.0878, 3),
    ('Badshahpur', 28.3933, 77.0484, 3), ('Sikanderpur', 28.4812, 77.0976, 3), ('Nathupur', 28.4884, 77.0997, 3), ('Chakkarpur', 28.4715, 77.0889, 3),
    ('Old Gurugram', 28.4646, 77.0299, 1), ('Manesar →', 28.3700, 76.9450, 1),
]
areas = [{'n': n, 'x': round(proj(lon, lat)[0]), 'y': round(proj(lon, lat)[1]), 't': t} for n, lat, lon, t in AREAS]

# ---- sectors -------------------------------------------------------------
for q in list(quotes):
    if q['sector'] == '15':
        q['sector'] = '15I'
        q2 = dict(q); q2['sector'] = '15II'; quotes.append(q2)
sectors = geo['sectors']
EXTRA_POINTS = {'63A': (28.3885, 77.0905), '79': (28.3745, 76.9840), '79B': (28.3680, 76.9905),
                '89A': (28.4115, 76.9405), '95A': (28.4085, 76.9040)}
for k, (lat, lon) in EXTRA_POINTS.items():
    if k not in sectors:
        px, py = proj(lon, lat)
        sectors[k] = {"name": k, "rings": [], "cx": round(px, 1), "cy": round(py, 1), "boundary": False}
for q in quotes:
    if q['sector'].upper().startswith('SOHNA'): q['sector'] = q['sector'].upper()
    if q['sector'].upper().startswith('MANESAR'): q['sector'] = 'MANESAR'
sohna_keys = sorted({q['sector'] for q in quotes if q['sector'].startswith('SOHNA')} | {'SOHNA-2', 'SOHNA-33', 'SOHNA-35', 'SOHNA-36'}, key=lambda k: int(re.search(r'\d+', k).group())) + ['MANESAR']
bbox = list(CANVAS)
strip_y = bbox[1] + bbox[3] + 40
x0 = bbox[0] + bbox[2] - 60 - 46 * (len(sohna_keys) - 1)
for i, k in enumerate(sohna_keys):
    sectors[k] = {"name": k, "rings": [], "cx": x0 + 46 * i, "cy": strip_y, "boundary": False, "inset": True}
bbox[3] += 80
for k, s in sectors.items():
    if k in ('15I', '15II'): s['label'] = k.replace('I', '-I', 1)
    elif k.startswith('SOHNA'): s['label'] = k.split('-')[1]
    elif k == 'MANESAR': s['label'] = 'M'
    if s['rings']:
        xs = [p[0] for r in s['rings'] for p in r]; ys = [p[1] for r in s['rings'] for p in r]
        s['bb'] = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]

# ---- societies (search index) --------------------------------------------
def pip(x, y, ring):
    n = len(ring); j = n - 1; c = False
    for i in range(n):
        xi, yi = ring[i]; xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            c = not c
        j = i
    return c
poly_sectors = [(k, s) for k, s in sectors.items() if s.get('rings')]
point_sectors = [(k, s) for k, s in sectors.items() if not s.get('rings') and not s.get('inset')]
def sector_at(x, y):
    for k, s in poly_sectors:
        bb = s['bb']
        if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and any(pip(x, y, r) for r in s['rings']):
            return k, 'in'
    best, bd = None, 40  # ~1.1 km
    for k, s in point_sectors:
        d = math.hypot(s['cx'] - x, s['cy'] - y)
        if d < bd: best, bd = k, d
    return (best, 'near') if best else (None, None)

def normname(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
SKIP = re.compile(r'^(sector\s*\d+|block|phase|pocket|[a-z]\s*block.*|.*\bsubstation\b.*|.*\bvillage\b|.*\bcolony\b)$', re.I)
societies, seen_soc = [], {}
for e in load('societies_raw.json'):
    t = e['tags']; nm = (t.get('name') or '').strip()
    if len(nm) < 4 or SKIP.match(nm) or re.match(r'^sector\s*\d+', nm, re.I): continue
    if t.get('landuse') == 'construction' and not t.get('name'): continue
    lat = e.get('lat') or e.get('center', {}).get('lat'); lon = e.get('lon') or e.get('center', {}).get('lon')
    if lat is None: continue
    x, y = proj(lon, lat)
    if not inside(x, y, 0) or lat > 28.55: continue
    key = normname(nm)
    if key in seen_soc and math.hypot(seen_soc[key][0]-x, seen_soc[key][1]-y) < 60: continue
    seen_soc[key] = (x, y)
    k, how = sector_at(x, y)
    kind = t.get('place') or ('condominium' if t.get('building') in ('apartments', 'residential') else 'residential area')
    societies.append({'n': nm, 'x': round(x), 'y': round(y), 'k': k, 'h': how, 'kind': kind})
societies.sort(key=lambda s: s['n'].lower())

# give quoted projects a map position when a society of the same name exists
soc_by = {}
for s in societies: soc_by.setdefault(normname(s['n']), s)
def find_soc(project):
    p = normname(re.sub(r'\(.*?\)', '', project))
    if p in soc_by: return soc_by[p]
    toks = [t for t in p.split() if len(t) > 2 and t not in ('the', 'phase', 'tower', 'towers', 'residences', 'resale')]
    for key, s in soc_by.items():
        if len(toks) >= 2 and all(t in key.split() for t in toks): return s
    return None
for q in quotes:
    s = find_soc(q['project'])
    if s and (s['k'] == q['sector'] or s['k'] is None):
        q['x'], q['y'] = s['x'], s['y']

# what each corridor passes through: sample the drawn geometry every ~250 m and look up the sector
UNIT_KM = 0.0278  # 1 map unit = 1/4000 degree of latitude
road_info = {}
for r in roads:
    if not r.get('k'): continue
    pts = [tuple(map(float, xy.split(','))) for xy in r['d'][1:].split('L')]
    info = road_info.setdefault(r['k'], {'c': r['c'], 'km': 0.0, 'secs': set(), 'bb': [1e9, 1e9, -1e9, -1e9]})
    if ORDER[r['c']] > ORDER[info['c']]: info['c'] = r['c']
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1); info['km'] += L * UNIT_KM
        n = max(1, int(L / 9))
        for i in range(n + 1):
            x, y = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
            k, how = sector_at(x, y)
            if k and (how == 'in' or math.hypot(sectors[k]['cx'] - x, sectors[k]['cy'] - y) < 22): info['secs'].add(k)
        for x, y in ((x1, y1), (x2, y2)):
            bb = info['bb']; bb[0] = min(bb[0], x); bb[1] = min(bb[1], y); bb[2] = max(bb[2], x); bb[3] = max(bb[3], y)
for k, v in road_info.items():
    v['km'] = round(v['km'] / 2 if v['c'] in ('mw', 'tr') else v['km'], 1)  # dual carriageways are mapped as two ways
    v['secs'] = sorted(v['secs'], key=lambda s: (int(re.match(r'\d+', s).group()) if re.match(r'\d+', s) else 999, s))
    v['bb'] = [round(x) for x in v['bb']]
road_info = {k: v for k, v in road_info.items() if v['km'] >= 0.8 or v['secs']}
for r in roads:
    if r.get('k') and r['k'] not in road_info: r['k'] = ''

def load_opt(name, default):
    try: return json.load(open(f'{BASE}/{name}'))
    except Exception: return default
bench = load_opt('benchmarks.json', {})
nostock = load_opt('nostock.json', {})
for k in list(nostock):
    if any(q['sector'] == k for q in quotes): del nostock[k]   # a real quote beats a no-stock verdict
for s, gs in generic_only.items():
    if s in nostock: continue
    g = min(gs, key=lambda q: q['price_psf_min'])
    lo = min(q['price_psf_min'] for q in gs); hi = max(q['price_psf_max'] for q in gs)
    rng = f'₹{lo:,}' + (f'–{hi:,}' if hi != lo else '')
    nostock[s] = {'reason': f'no branded premium project found; locality-wide resale asking average is {rng}/sq ft ({g.get("as_of", "")})'.replace(' ()', ''),
                  'source_url': g.get('source_url', ''), 'locality_avg': [lo, hi]}
if '15' in nostock:   # OSM splits Sector 15 into parts I and II; a whole-sector verdict applies to whichever part has no quote
    for part in ('15I', '15II'):
        if not any(q['sector'] == part for q in quotes): nostock[part] = nostock['15']
    del nostock['15']

data = {
    'bench': bench, 'nostock': nostock, 'src': SRC, 'sectorNews': load_opt('sector_news.json', {}),
    'roadInfo': road_info,
    'bbox': bbox, 'canvas': CANVAS, 'sectors': sectors, 'sohnaStrip': {'x': x0 - 60, 'y': strip_y},
    'quotes': quotes, 'roads': roads, 'roadLabels': road_labels,
    'border': [{'d': b['d']} for b in border], 'airport': airport, 'green': green,
    'metro': metro, 'stations': stations, 'landmarks': landmarks, 'entries': entries, 'areas': areas, 'societies': societies,
}
n_sectors_with_data = len({q['sector'] for q in quotes})
_src = {}
for q in quotes: _src[q.get('sot', {}).get('label', q.get('source_type', 'other'))] = _src.get(q.get('sot', {}).get('label', q.get('source_type', 'other')), 0) + 1
_cls = {}
for q in quotes: c = q.get('sot', {}).get('cls', 'other'); _cls[c] = _cls.get(c, 0) + 1
def _pct(n): return f'{100 * n / len(quotes):.0f}%' if 100 * n / len(quotes) >= 1 else f'{100 * n / len(quotes):.1f}%'
SOURCE_NOTE = ('<div class="note"><h3>Where the numbers come from</h3>Of the ' + str(len(quotes)) + ' project quotes, ' +
    ', '.join(f'<b>{_pct(n)}</b> {html.escape(k)}' for k, n in [kv for kv in sorted(_src.items(), key=lambda kv: -kv[1]) if kv[1] >= 3]) +
    f'; the rest are broker microsites, developer/project sites and press reports ({_pct(_cls.get("broker", 0))} broker, {_pct(_cls.get("developer", 0) + _cls.get("project-site", 0))} developer or project site, {_pct(_cls.get("news", 0))} news). '
    'Square Yards dominates because it is the one major portal whose project pages could be read programmatically; its "current asking price" blends listing asks with registered-transaction data, so it usually sits closer to achieved prices than a pure listing average — but it is one vendor\'s model, and 99acres figures are pure listing asks. Every quote shows its source label; hover it for what that number means on that site, and the full register is in '
    '<a href="https://github.com/gagan86nagpal/gurgaon-map/blob/main/SOURCES.md" target="_blank" rel="noopener">SOURCES.md</a>.</div>')
generated = '10 Sep 2026'

PAGE = r'''<title>Gurugram Sector Price Map</title>
<script>try{const t=localStorage.getItem('ggn-theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}catch(e){}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,400..800&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --bg:#eef0f2; --panel:#ffffff; --panel-2:#f6f7f8; --ink:#1a222c; --ink-2:#4b5563; --muted:#7a8590;
  --line:#d5dade; --line-2:#e6e9ec; --accent:#8a1c1f; --accent-ink:#fff; --focus:#2563eb;
  --nodata:#dfe3e7; --nodata-hatch:#c6ccd2; --delhi:#e4e6e9;
  --road:#ffffff; --road-edge:#9ea7b1; --road-edge-mw:#7e8894; --road-minor:#f7f8f9; --road-minor-edge:#d3d8dd; --gc:#c99a2e; --gc-edge:#8a6a1a;
  --green:#cfe3cf; --green-edge:#9fbf9f; --golf:#bfdcb9; --golf-edge:#79a872; --air:#d8dce6; --air-edge:#9aa3b8; --runway:#8b93a8;
  --border:#6b5b95; --metro-case:#ffffff; --lm:#1a222c; --lm-ink:#ffffff;
  --b1:#f9e0da; --b2:#f2bdb2; --b3:#e89787; --b4:#da6e5f; --b5:#c2463f; --b6:#96262a; --b7:#5b0f14;
  --shadow:0 10px 30px rgba(20,30,40,.12);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#15191e; --panel:#1d2229; --panel-2:#232930; --ink:#eef1f4; --ink-2:#c3cad2; --muted:#8e98a3;
    --line:#333b45; --line-2:#2a313a; --accent:#f08a7c; --accent-ink:#1a0a0a; --focus:#7db1ff;
    --nodata:#262c33; --nodata-hatch:#343c45; --delhi:#1b2026;
    --road:#0f1216; --road-edge:#5a6470; --road-edge-mw:#7c8894; --road-minor:#1a1f25; --road-minor-edge:#2e353d; --gc:#d9a93a; --gc-edge:#3a2c08;
    --green:#1f2f22; --green-edge:#33503a; --golf:#22392a; --golf-edge:#3f6a48; --air:#1e232d; --air-edge:#3b445a; --runway:#6a7390;
    --border:#a493d6; --metro-case:#0f1216; --lm:#eef1f4; --lm-ink:#15191e;
    --b1:#f6d3cb; --b2:#eea698; --b3:#e17c6a; --b4:#c95445; --b5:#a83530; --b6:#7f1f20; --b7:#561014;
    --shadow:0 10px 30px rgba(0,0,0,.45);
  }
}
:root[data-theme="dark"]{
  --bg:#15191e; --panel:#1d2229; --panel-2:#232930; --ink:#eef1f4; --ink-2:#c3cad2; --muted:#8e98a3;
  --line:#333b45; --line-2:#2a313a; --accent:#f08a7c; --accent-ink:#1a0a0a; --focus:#7db1ff;
  --nodata:#262c33; --nodata-hatch:#343c45; --delhi:#1b2026;
  --road:#0f1216; --road-edge:#5a6470; --road-edge-mw:#7c8894; --road-minor:#1a1f25; --road-minor-edge:#2e353d; --gc:#d9a93a; --gc-edge:#3a2c08;
  --green:#1f2f22; --green-edge:#33503a; --golf:#22392a; --golf-edge:#3f6a48; --air:#1e232d; --air-edge:#3b445a; --runway:#6a7390;
  --border:#a493d6; --metro-case:#0f1216; --lm:#eef1f4; --lm-ink:#15191e;
  --b1:#f6d3cb; --b2:#eea698; --b3:#e17c6a; --b4:#c95445; --b5:#a83530; --b6:#7f1f20; --b7:#561014;
  --shadow:0 10px 30px rgba(0,0,0,.45);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
h1,h2,h3{font-family:"Bricolage Grotesque","IBM Plex Sans",system-ui,sans-serif;text-wrap:balance;margin:0}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}
.eyebrow{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600}
button{font:inherit;color:inherit}

header{padding:14px clamp(16px,3vw,40px) 12px;border-bottom:1px solid var(--line-2);display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
#theme{width:38px;height:38px;flex:none;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--ink);cursor:pointer;display:grid;place-items:center;margin-top:2px}
#theme:hover{background:var(--panel-2)}
#theme svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round}
header h1{font-size:clamp(24px,3vw,34px);font-weight:700;letter-spacing:-.02em;line-height:1.05;font-variation-settings:"opsz" 96,"wdth" 92}
header p{margin:6px 0 0;color:var(--ink-2);max-width:70ch;font-size:14px}
.stats{display:flex;gap:24px;flex-wrap:wrap}
.stat b{display:block;font-family:"Bricolage Grotesque",sans-serif;font-size:24px;font-weight:700;letter-spacing:-.01em;line-height:1}
.stat span{font-size:12px;color:var(--muted)}

.toolbar{display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center;padding:10px clamp(16px,3vw,40px);border-bottom:1px solid var(--line-2);background:var(--panel);position:relative;z-index:6}
.legend{display:flex;align-items:center;gap:0;flex-wrap:wrap}
.legend .sw{display:flex;flex-direction:column;align-items:flex-start;min-width:52px;border:0;background:none;padding:2px 0;cursor:pointer;border-radius:4px}
.legend .sw:hover i{outline:2px solid var(--ink-2);outline-offset:1px}
.legend .sw[aria-pressed="true"] i{outline:2px solid var(--ink);outline-offset:1px}
.legend .sw[aria-pressed="true"] small{color:var(--ink);font-weight:600}
.legend.filtering .sw[aria-pressed="false"] i{opacity:.3}
.legend .clear{border:0;background:none;color:var(--accent);font:600 11px "IBM Plex Sans",sans-serif;cursor:pointer;margin-left:6px;text-decoration:underline;display:none}
.legend.filtering .clear{display:inline}
.legend .sw i{display:block;width:100%;height:11px;border-radius:2px}
.legend .sw:first-child i{border-radius:6px 2px 2px 6px}
.legend .sw:nth-last-child(2) i{border-radius:2px 6px 6px 2px}
.legend .sw small{font-size:11px;color:var(--muted);margin-top:3px;white-space:nowrap}
.legend .key{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-2);margin-left:16px}
.legend .key i{width:16px;height:12px;border-radius:2px;display:inline-block}
.legend .dir{font-size:11px;color:var(--muted);margin-right:8px;white-space:nowrap}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--ink-2);border-radius:999px;padding:4px 11px;font:500 12px/1.4 "IBM Plex Sans",sans-serif;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.chip.layer[aria-pressed="true"]{background:var(--panel-2);color:var(--ink);border-color:var(--ink-2)}
.chip:focus-visible,button:focus-visible,a:focus-visible,tr[tabindex]:focus-visible,input:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.chip .n{font-family:"IBM Plex Mono",monospace;font-size:11px;opacity:.75}
.srchint{font-size:11px;color:var(--muted);margin-top:4px;max-width:720px;line-height:1.4}
.chip.src[data-rank="0"],.chip.src[data-rank="1"]{border-style:solid;font-weight:600}
.proj .alts{font-size:12px;color:var(--ink-2);margin-top:6px}
.proj .alts a{color:var(--ink);border-bottom:1px solid var(--line);text-decoration:none}
.proj .alts b{font-family:"IBM Plex Mono",monospace;font-weight:500}
.grp{display:flex;align-items:center;gap:8px}
.grp .eyebrow{font-size:10px}

/* search */
.search{position:relative;flex:1 1 320px;max-width:520px;margin-left:auto}
.search input{width:100%;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:8px;padding:9px 12px 9px 36px;font:15px "IBM Plex Sans",sans-serif}
.search input::placeholder{color:var(--muted)}
.search svg.ico{position:absolute;left:11px;top:11px;width:17px;height:17px;fill:none;stroke:var(--muted);stroke-width:2;pointer-events:none}
.results{position:absolute;left:0;right:0;top:calc(100% + 6px);background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);overflow:hidden;display:none;max-height:min(60vh,480px);overflow-y:auto}
.results.on{display:block}
.res{display:grid;grid-template-columns:1fr auto;gap:2px 12px;width:100%;text-align:left;border:0;background:none;padding:9px 14px;cursor:pointer;border-bottom:1px solid var(--line-2)}
.res:last-child{border-bottom:0}
.res:hover,.res.sel{background:var(--panel-2)}
.res b{font-weight:600;font-size:14px}
.res b mark{background:none;color:var(--accent);font-weight:700}
.res .kind{font-size:12px;color:var(--muted);grid-column:1}
.res .price{grid-column:2;grid-row:1/3;align-self:center;font-family:"IBM Plex Mono",monospace;font-size:13px;white-space:nowrap;text-align:right}
.res .price small{display:block;font:11px "IBM Plex Sans",sans-serif;color:var(--muted)}
.res .none{color:var(--muted);font-size:12px;font-family:"IBM Plex Sans",sans-serif}
.results .empty{padding:12px 14px;color:var(--muted);font-size:13px}

/* stage */
.stage{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:0;align-items:stretch}
@media (max-width:980px){.stage{grid-template-columns:1fr}.inspector{border-left:0;border-top:1px solid var(--line-2);max-height:none;position:static}.mapwrap{height:78vh}}
.mapwrap{position:relative;height:calc(100vh - 60px);min-height:560px;overflow:hidden;background:var(--bg)}
svg.map{width:100%;height:100%;display:block;touch-action:none;cursor:grab;--z:1;--zf:1;user-select:none}
#theme .sun{display:none}
:root[data-theme="dark"] #theme .sun{display:block} :root[data-theme="dark"] #theme .moon{display:none}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]) #theme .sun{display:block} :root:not([data-theme="light"]) #theme .moon{display:none} }
svg.map.dragging{cursor:grabbing}
.ctrls{position:absolute;right:14px;bottom:44px;display:flex;flex-direction:column;gap:6px;z-index:4}
.ctrls button{width:36px;height:36px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--ink);cursor:pointer;font:600 18px/1 "IBM Plex Sans",sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.08);display:grid;place-items:center}
.ctrls button:hover{background:var(--panel-2)}
.ctrls button svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.hint{position:absolute;left:14px;bottom:12px;font-size:11px;color:var(--muted);background:color-mix(in srgb,var(--bg) 80%,transparent);padding:3px 8px;border-radius:6px;pointer-events:none;z-index:4}
.attrib{position:absolute;right:14px;bottom:12px;font-size:11px;color:var(--muted);z-index:4}
.attrib a{color:var(--muted)}
.mlegend{position:absolute;left:14px;top:12px;z-index:4;background:color-mix(in srgb,var(--panel) 88%,transparent);border:1px solid var(--line-2);border-radius:10px;padding:8px 12px;font-size:11px;color:var(--ink-2);display:grid;grid-template-columns:auto auto;gap:4px 14px;backdrop-filter:blur(4px)}
.mlegend div{display:flex;align-items:center;gap:7px;white-space:nowrap}
.mlegend i{display:inline-block;width:18px;height:0;border-top:3px solid var(--road-edge);border-radius:2px}
.mlegend i.gc{border-top:4px solid var(--gc)}
.mlegend i.mw{border-top:4px solid var(--road-edge)}
.mlegend i.sc{border-top:1.5px solid var(--road-minor-edge)}
.mlegend i.metro{border-top:3px solid #f2c200;position:relative}
.mlegend i.bl{border-top-color:#3b6fd9}.mlegend i.ae{border-top-color:#f07d1a}.mlegend i.rm{border-top-color:#2a9d8f}
.mlegend i.border{border-top:2px dashed var(--border)}
.mlegend s{display:inline-grid;place-items:center;width:14px;height:14px;border-radius:50%;background:var(--lm);color:var(--lm-ink);font:700 9px/1 "IBM Plex Sans",sans-serif;text-decoration:none}
.mlegend s.tri{background:none;color:var(--ink);font-size:12px}
@media (max-width:640px){.mlegend{display:none}}

/* svg layers — widths and type scale with zoom via --z (constant on screen) and --zf (grows gently when zoomed in) */
.sector{stroke:var(--bg);stroke-width:calc(1.6px*var(--z));stroke-linejoin:round;cursor:pointer;transition:filter .12s}
.sector.nodata{fill:url(#hatch)}
.sector.nostock{fill:url(#dots)}
.pill.conf{font-family:"IBM Plex Mono",monospace;padding:1px 6px}
.pill.conf.A{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.pill.conf.B{color:var(--ink)}
.pill.conf.C{color:var(--muted);border-style:dashed}
.bench{margin-top:12px;font-size:12px;color:var(--ink-2);border:1px solid var(--line-2);border-radius:8px;padding:8px 12px;background:var(--panel-2)}
.bench b{font-family:"IBM Plex Mono",monospace;color:var(--ink)}
.bench .ok{color:var(--ink-2)}
.bench .warn{color:var(--accent);font-weight:600}
.bench a{color:var(--muted);text-decoration:none;border-bottom:1px solid var(--line)}
.sector.dim{fill-opacity:.12}.pt.dim circle{fill-opacity:.12;stroke-opacity:.3}.lbl.dim{opacity:.25}
.sector:hover,.sector.pinned{filter:brightness(.92);stroke:var(--ink);stroke-width:calc(2.2px*var(--z))}
:root[data-theme="dark"] .sector:hover,:root[data-theme="dark"] .sector.pinned{filter:brightness(1.15)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .sector:hover,:root:not([data-theme="light"]) .sector.pinned{filter:brightness(1.15)}}
.pt{cursor:pointer}
.pt circle{stroke-width:calc(1.8px*var(--z));stroke-dasharray:4 3;r:calc(14px*var(--z))}
.pt:hover circle,.pt.pinned circle{stroke:var(--ink);stroke-dasharray:none;stroke-width:calc(2.2px*var(--z))}
.lbl{font-family:"Bricolage Grotesque",sans-serif;font-variation-settings:"wdth" 78,"opsz" 12;font-weight:700;font-size:calc(12.5px*var(--zf));text-anchor:middle;dominant-baseline:central;pointer-events:none;paint-order:stroke;stroke-width:calc(2.5px*var(--zf));stroke-linejoin:round}
.lbl.small{font-size:calc(10.5px*var(--zf))}
.road{fill:none;stroke:var(--road);stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
.roadedge{fill:none;stroke:var(--road-edge);stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
.road.mw{stroke-width:calc(6.2px*var(--z))}.roadedge.mw{stroke-width:calc(9px*var(--z));stroke:var(--road-edge-mw)}
.road.tr{stroke-width:calc(4.6px*var(--z))}.roadedge.tr{stroke-width:calc(6.8px*var(--z))}
.road.pr{stroke-width:calc(3px*var(--z))}.roadedge.pr{stroke-width:calc(4.6px*var(--z))}
.roadhit{fill:none;stroke:transparent;stroke-width:calc(12px*var(--z));stroke-linecap:round;cursor:pointer;pointer-events:stroke}
.road.sel,.road.hov{stroke:var(--focus)!important}
.roadedge.sel{stroke:var(--bg)!important}
.road.sc{stroke:var(--road-minor);stroke-width:calc(1.3px*var(--z))}.roadedge.sc{stroke:var(--road-minor-edge);stroke-width:calc(2.1px*var(--z))}
.road.tt{stroke:var(--road-minor);stroke-width:calc(.8px*var(--z))}.roadedge.tt{stroke:var(--road-minor-edge);stroke-width:calc(1.4px*var(--z));opacity:.8}
.road.gc{stroke:var(--gc);stroke-width:calc(4.6px*var(--z))}.roadedge.gc{stroke:var(--gc-edge);stroke-width:calc(6.8px*var(--z))}
svg.map:not(.z2) .road.tt,svg.map:not(.z2) .roadedge.tt{display:none}
.rlbl{font:600 calc(11px*var(--zf)) "IBM Plex Sans",sans-serif;letter-spacing:.06em;text-transform:uppercase;fill:var(--muted);paint-order:stroke;stroke:var(--bg);stroke-width:calc(3px*var(--zf));pointer-events:none;text-anchor:middle}
.rlbl.gc{fill:var(--gc-edge);font-weight:700}
.delhi{fill:var(--delhi);stroke:none}
.border{fill:none;stroke:var(--border);stroke-width:calc(1.8px*var(--z));stroke-dasharray:calc(7px*var(--z)) calc(4px*var(--z));opacity:.85;pointer-events:none}
.blbl{font:italic 500 calc(12px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--border);letter-spacing:.14em;text-transform:uppercase;paint-order:stroke;stroke:var(--bg);stroke-width:calc(3px*var(--zf));pointer-events:none}
.apron{fill:var(--air);stroke:var(--air-edge);stroke-width:calc(1px*var(--z))}
.runway{fill:none;stroke:var(--runway);stroke-width:calc(4px*var(--z));stroke-linecap:butt}
.terminal{fill:var(--air-edge);stroke:none;opacity:.8}
.green{fill:var(--green);stroke:var(--green-edge);stroke-width:calc(.8px*var(--z));fill-opacity:.75;pointer-events:none}
.green.golf{fill:var(--golf);stroke:var(--golf-edge);fill-opacity:.9}
.metro{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:calc(3px*var(--z));pointer-events:none}
.metrocase{fill:none;stroke:var(--metro-case);stroke-linecap:round;stroke-linejoin:round;stroke-width:calc(5px*var(--z));pointer-events:none;opacity:.9}
.st circle{fill:var(--metro-case);stroke:var(--ink-2);stroke-width:calc(1.4px*var(--z));r:calc(2.8px*var(--z))}
.st text{font:500 calc(9.5px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--ink-2);paint-order:stroke;stroke:var(--bg);stroke-width:calc(2.5px*var(--zf));pointer-events:none}
.st[data-k="2"]{display:none} svg.map.z2 .st[data-k="2"]{display:block}
.lm{cursor:default}
.lm circle{fill:var(--lm);stroke:var(--bg);stroke-width:calc(1.5px*var(--z));r:calc(7px*var(--zf))}
.lm .g{font:700 calc(8.5px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--lm-ink);text-anchor:middle;dominant-baseline:central;pointer-events:none}
.lm .t{font:600 calc(10.5px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--ink);paint-order:stroke;stroke:var(--bg);stroke-width:calc(3px*var(--zf));pointer-events:none}
.lm[data-t="2"]{display:none} svg.map.z2 .lm[data-t="2"]{display:block}
.lm[data-t="3"]{display:none} svg.map.z3 .lm[data-t="3"]{display:block}
.lm.golf circle{fill:var(--golf-edge)}
.entry text{font:700 calc(10.5px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--border);paint-order:stroke;stroke:var(--bg);stroke-width:calc(3px*var(--zf));pointer-events:none}
.entry path{fill:var(--border);stroke:var(--bg);stroke-width:calc(1px*var(--z))}
.entry[data-major="0"]{display:none} svg.map.z2 .entry[data-major="0"]{display:block}
.area{font:italic 500 calc(11.5px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--ink-2);letter-spacing:.08em;text-transform:uppercase;text-anchor:middle;paint-order:stroke;stroke:var(--bg);stroke-width:calc(3px*var(--zf));pointer-events:none;opacity:.85}
.area[data-t="1"]{font-size:calc(13px*var(--zf));fill:var(--ink)}
.area[data-t="2"]{display:none} svg.map.z2 .area[data-t="2"]{display:block}
.area[data-t="3"]{display:none} svg.map.z3 .area[data-t="3"]{display:block}
.soc{display:none;font:400 calc(8.5px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--ink-2);text-anchor:middle;paint-order:stroke;stroke:var(--bg);stroke-width:calc(2px*var(--zf));pointer-events:none}
svg.map.z4 .soc{display:block}
.marker{pointer-events:none}
.marker circle{fill:none;stroke:var(--focus);stroke-width:calc(2.5px*var(--z));r:calc(11px*var(--z))}
.marker circle.dot{fill:var(--focus);stroke:var(--bg);stroke-width:calc(1.5px*var(--z));r:calc(4px*var(--z))}
.marker text{font:700 calc(11px*var(--zf)) "IBM Plex Sans",sans-serif;fill:var(--focus);paint-order:stroke;stroke:var(--bg);stroke-width:calc(3px*var(--zf))}
.hide{display:none!important}
svg.map.nonames .lm .t,svg.map.nonames .st text,svg.map.nonames .entry text,svg.map.nonames .area,svg.map.nonames .soc{display:none!important}

.tip{position:absolute;pointer-events:none;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:10px 12px;box-shadow:var(--shadow);min-width:200px;max-width:260px;font-size:13px;opacity:0;transform:translateY(4px);transition:opacity .1s,transform .1s;z-index:5}
.tip.on{opacity:1;transform:none}
.tip .t{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:15px;letter-spacing:-.01em}
.tip .r{font-family:"IBM Plex Mono",monospace;font-size:14px;margin:4px 0 2px}
.tip .m{color:var(--muted);font-size:12px}
.tip ul{margin:8px 0 0;padding:0;list-style:none;border-top:1px solid var(--line-2)}
.tip li{display:flex;justify-content:space-between;gap:10px;padding:4px 0;border-bottom:1px solid var(--line-2);font-size:12px}
.tip li span:last-child{font-family:"IBM Plex Mono",monospace;white-space:nowrap;color:var(--ink-2)}
.tip .hint2{margin-top:8px;font-size:11px;color:var(--muted)}

.inspector{border-left:1px solid var(--line-2);background:var(--panel);padding:18px 20px 28px;overflow:auto;max-height:calc(100vh - 60px);position:sticky;top:0}
.inspector .empty{color:var(--muted);font-size:14px;max-width:34ch}
.inspector h2{font-size:26px;font-weight:700;letter-spacing:-.02em;line-height:1.05}
.inspector .range{font-family:"IBM Plex Mono",monospace;font-size:20px;margin-top:6px}
.inspector .sub{color:var(--muted);font-size:12px;margin-top:2px}
.bhk{margin-top:14px;border:1px solid var(--line-2);border-radius:8px;padding:10px 12px;background:var(--panel-2)}
.bhk table{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
.bhk td{padding:4px 0;border-bottom:1px solid var(--line-2)}
.bhk tr:last-child td{border-bottom:0}
.bhk td:first-child{font-weight:600;width:4.5em}
.bhk td.num{font-family:"IBM Plex Mono",monospace;text-align:right;white-space:nowrap}
.bhk input{width:5.2em;border:1px solid var(--line);border-radius:5px;background:var(--panel);color:var(--ink);font:13px "IBM Plex Mono",monospace;padding:2px 6px;text-align:right}
.bhk small{display:block;margin-top:6px;font-size:11px;color:var(--muted);line-height:1.4}
.projects{list-style:none;margin:16px 0 0;padding:0;display:flex;flex-direction:column;gap:10px}
.proj{border:1px solid var(--line-2);background:var(--panel-2);border-radius:8px;padding:10px 12px;cursor:pointer}
.proj:hover{border-color:var(--accent)}
.proj .go{display:block;text-align:right;font-size:11px;color:var(--muted);margin-top:6px}
.proj .cfgwrap{overflow-x:auto;max-width:100%}
.proj:hover .go{color:var(--accent)}
.proj .cfg{margin-top:6px;font-size:11.5px;border-collapse:collapse}
.proj .cfg td{padding:1px 10px 1px 0;color:var(--ink-2);white-space:nowrap}
.proj .cfg td.n{font-family:"IBM Plex Mono",monospace}
.proj .cfg th{font-weight:600;text-align:left;padding:0 10px 2px 0;color:var(--muted);font-size:11px;letter-spacing:.02em}
li.secrow{display:flex;justify-content:space-between;gap:10px;align-items:center;cursor:pointer}
li.secrow>span:first-child{white-space:nowrap;font-weight:600}
li.secrow:hover{border-color:var(--ink-2)}
li.secrow .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:8px;vertical-align:-1px;border:1px solid var(--line)}
li.secrow .num{font-family:"IBM Plex Mono",monospace;font-size:13px;white-space:nowrap;text-align:right}
li.secrow .num small{display:block;font:11px "IBM Plex Sans",sans-serif;color:var(--muted)}
li.secrow.nod{color:var(--muted)}
.proj.hl{border-color:var(--focus);box-shadow:0 0 0 2px color-mix(in srgb,var(--focus) 30%,transparent)}
.proj .row{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.proj .name{font-weight:600;line-height:1.3}
.proj .name a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line)}
.proj .name a:hover{color:var(--accent);border-color:var(--accent)}
.proj .dev{font-size:12px;color:var(--muted)}
.proj .psf{font-family:"IBM Plex Mono",monospace;font-size:14px;white-space:nowrap}
.proj .tix{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-2);margin-top:4px}
.proj .tix span{color:var(--muted);font-family:"IBM Plex Sans",sans-serif}
.proj .basis{font-size:12px;color:var(--ink-2);margin-top:6px}
.proj .meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center;font-size:11px;color:var(--muted)}
.pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:600;letter-spacing:.02em;border:1px solid var(--line)}
.pill.launch{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.pill.uc{background:transparent;color:var(--ink)}
.pill.ready{background:var(--panel);color:var(--ink-2)}
.pill.resale{background:transparent;color:var(--muted);border-style:dashed}
.pill.src{color:var(--muted)}
.inspector .how{margin-top:16px;font-size:12px;color:var(--muted);border-top:1px solid var(--line-2);padding-top:10px}
.inspector .how b{color:var(--ink-2)}
.inspector .locate{margin-top:10px;border:1px solid var(--line);background:var(--panel);border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer}

section.table{padding:28px clamp(16px,3vw,40px) 48px}
section.table h2{font-size:24px;font-weight:700;letter-spacing:-.02em}
section.table p{color:var(--ink-2);max-width:70ch}
.tablewrap{overflow-x:auto;border:1px solid var(--line-2);border-radius:10px;background:var(--panel);margin-top:14px}
table.tbl{border-collapse:collapse;width:100%;min-width:900px;font-size:13px}
.tbl th,.tbl td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line-2);vertical-align:top}
.tbl th{position:sticky;top:0;background:var(--panel-2);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);cursor:pointer;user-select:none;white-space:nowrap}
.tbl th[aria-sort="ascending"]::after{content:" ↑"}.tbl th[aria-sort="descending"]::after{content:" ↓"}
.tbl td.num{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl td .sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.tbl tr.sec td{background:var(--panel-2);font-weight:600}
.tbl tr.sec td .cnt{font-weight:400;color:var(--muted);font-size:12px;margin-left:6px}
.tbl tr.q td:first-child{padding-left:28px;color:var(--muted)}
.tbl td a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
.tbl td a:hover{border-color:var(--accent)}

.notes{padding:0 clamp(16px,3vw,40px) 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;max-width:1500px}
.note{border-top:2px solid var(--line);padding-top:10px;font-size:13px;color:var(--ink-2)}
.note h3{font-size:14px;font-weight:700;margin-bottom:4px;color:var(--ink)}
footer{padding:18px clamp(16px,3vw,40px) 36px;font-size:12px;color:var(--muted);border-top:1px solid var(--line-2)}
footer .stats{margin-bottom:12px}
footer p{max-width:90ch;margin:0}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<header>
  <div>
    <div class="eyebrow">Gurugram · premium-segment asking prices · ₹ per sq ft (super area)</div>
    <h1>Your introduction to Gurgaon real estate, sector-wise</h1>
  </div>
  <button id="theme" title="Switch light / dark" aria-label="Switch between light and dark mode"><svg viewBox="0 0 24 24" class="sun"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg><svg viewBox="0 0 24 24" class="moon"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></button>
</header>

<div class="toolbar">
  <div class="legend" id="legend" aria-label="Price bands, ₹ per sq ft"></div>
  <div class="grp"><span class="eyebrow">Include</span>
  <div class="chips" role="group" aria-label="Include quotes with status">
    <button class="chip" data-b="launch" aria-pressed="true">New launch <span class="n"></span></button>
    <button class="chip" data-b="uc" aria-pressed="true">Under construction <span class="n"></span></button>
    <button class="chip" data-b="ready" aria-pressed="true">Ready <span class="n"></span></button>
    <button class="chip" data-b="resale" aria-pressed="true">Resale <span class="n"></span></button>
  </div></div>
  <div class="grp"><span class="eyebrow">Data source</span>
  <div class="chips" role="group" aria-label="Include quotes from these sources" id="srcchips"></div>
  <div class="srchint">← more direct (the developer's own price, or a reporter's figure) … less direct (portal listing averages, broker pages) →. When a project has several sources, the most direct one enabled sets its price; the others are shown on its card.</div></div>
  <div class="grp"><span class="eyebrow">Layers</span>
  <div class="chips" role="group" aria-label="Map layers">
    <button class="chip layer" data-l="metro" aria-pressed="true">Metro</button>
    <button class="chip layer" data-l="landmarks" aria-pressed="false">Landmarks</button>
    <button class="chip layer" data-l="placenames" aria-pressed="false">Place names</button>
    <button class="chip layer" data-l="minor" aria-pressed="true">Minor roads</button>
    <button class="chip layer" data-l="societies" aria-pressed="true">Society names when zoomed</button>
  </div></div>
  <div class="search" role="search">
    <svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
    <input id="q" type="search" placeholder="Search a society, project or sector — e.g. DLF Camellias, Grandstand, Sector 57" autocomplete="off" spellcheck="false" aria-label="Search societies, projects and sectors" aria-expanded="false" aria-controls="results">
    <div class="results" id="results" role="listbox"></div>
  </div>
</div>

<div class="stage">
  <div class="mapwrap" id="mapwrap">
    <svg class="map" id="map" role="img" aria-labelledby="maptitle" preserveAspectRatio="xMidYMid meet" tabindex="0">
      <title id="maptitle">Map of Gurugram sectors coloured by median premium asking price per square foot, with roads, metro and landmarks</title>
      <defs>
        <pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="7" height="7" fill="var(--nodata)"/>
          <line x1="0" y1="0" x2="0" y2="7" stroke="var(--nodata-hatch)" stroke-width="2"/>
        </pattern>
        <pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse">
          <rect width="8" height="8" fill="var(--nodata)"/>
          <circle cx="4" cy="4" r="1.3" fill="var(--nodata-hatch)"/>
        </pattern>
      </defs>
      <g id="g-base"></g>
      <g id="g-sectors"></g>
      <g id="g-green"></g>
      <g id="g-air"></g>
      <g id="g-roads-minor"></g>
      <g id="g-roads"></g>
      <g id="g-roadhit"></g>
      <g id="g-border"></g>
      <g id="g-metro"></g>
      <g id="g-points"></g>
      <g id="g-labels"></g>
      <g id="g-areas"></g>
      <g id="g-roadlabels"></g>
      <g id="g-stations"></g>
      <g id="g-soc"></g>
      <g id="g-landmarks"></g>
      <g id="g-entries"></g>
      <g id="g-marker"></g>
    </svg>
    <div class="mlegend" aria-label="Map symbols">
      <div style="grid-column:1/-1;color:var(--muted)">Click a major road for the sectors along it</div>
      <div><i class="gc"></i>Golf Course Rd / Ext.</div><div><i class="metro"></i>Yellow Line</div>
      <div><i class="mw"></i>Expressway · NH</div><div><i class="metro bl"></i>Blue Line (Dwarka)</div>
      <div><i></i>Main road</div><div><i class="metro ae"></i>Airport Express</div>
      <div><i class="sc"></i>Minor road</div><div><i class="metro rm"></i>Rapid Metro</div>
      <div><i class="border"></i>Delhi–Haryana line</div><div><s>H</s>Hospital &nbsp;<s>S</s>Mall &nbsp;<s>B</s>Offices</div>
      <div><s class="tri">▲</s>Entry to Delhi</div><div><s>✈</s>Airport &nbsp;<s>⛳</s>Golf &nbsp;<s>T</s>Toll</div>
    </div>
    <div class="ctrls">
      <button id="zin" title="Zoom in" aria-label="Zoom in">+</button>
      <button id="zout" title="Zoom out" aria-label="Zoom out">−</button>
      <button id="zfit" title="Reset view" aria-label="Reset view"><svg viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg></button>
    </div>
    <div class="hint">Drag to pan · scroll or pinch to zoom · zoom in for minor roads, stations and society names</div>
    <div class="attrib">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors</div>
    <div class="tip" id="tip" role="status" aria-live="polite"></div>
  </div>
  <aside class="inspector" id="inspector">
    <div class="empty"><div class="eyebrow" style="margin-bottom:6px">Evidence</div>Hover a sector to see its range. Click to pin it here with every project, its quoted price, indicative 2/3/4 BHK ticket sizes in ₹ crore, what the quote is based on, and a link to where we saw it.</div>
  </aside>
</div>

<section class="table">
  <h2>All the numbers behind the map</h2>
  <p>Grouped by sector, sorted by median. Each project row is one quote; click the source to verify it yourself. Prices are asking prices on super/saleable area unless the basis says otherwise.</p>
  <div class="tablewrap"><table class="tbl" id="tbl">
    <thead><tr>
      <th data-k="sector">Sector</th><th data-k="project">Project</th><th data-k="developer">Developer</th>
      <th data-k="mid" class="num">₹ / sq ft</th><th data-k="bucket">Status</th><th data-k="basis">Basis</th><th data-k="as_of">As of</th><th>Source</th>
    </tr></thead><tbody></tbody>
  </table></div>
</section>

<div class="notes">
  <div class="note"><h3>How the range is built</h3>For each project we take the midpoint of its quoted ₹/sq ft. A sector's <b>range</b> is the lowest to highest project midpoint; its <b>colour</b> is the median. With 3–4 projects that is a ballpark, not a valuation — one ultra-luxury launch (Krisumi Waterside in 36A, DLF Dahlias in 54) can pull a sector's top end far above its typical stock.</div>
  <div class="note"><h3>Ticket sizes in ₹ crore</h3>Indicative only: the sector's ₹/sq ft range multiplied by a typical super area (2 BHK 1,350 · 3 BHK 1,900 · 4 BHK 2,800 sq ft by default — edit the boxes in the panel). Real units vary a lot in size, and PLC, parking, GST and club charges come on top.</div>
  <div class="note"><h3>What "same league" means here</h3>We kept quotes from established branded developers and their premium/luxury lines. In mature sectors with no new launch (Old Gurugram, Sushant Lok, Golf Course Road) the evidence is resale asking rates in well-known condominiums, flagged <i>resale</i>. Use the chips to include or exclude those.</div>
  __SOURCE_NOTE__
  <div class="note"><h3>Which source wins</h3>Sources are ranked by how close they are to the actual price: the developer's own site or the project's site, then a reporter's figure in the press, then Square Yards (listing asks blended with registered transactions), then 99acres, MagicBricks/Housing/NoBroker listing averages, and finally broker microsites. Each project can carry a quote from several classes; the most direct class you have enabled sets the project's price, the rest are listed on its card so you can compare them. Use the "Data source" chips to see the map through only the sources you trust.</div>
  <div class="note"><h3>How the numbers were checked</h3>Every quote carries a confidence grade: <b>A</b> two independent sources agree within 15%; <b>B</b> one solid portal or developer page; <b>C</b> aggregator/broker only or not re-verified. Outliers, broker-sourced and wide-spread rows were re-audited in September 2026 and corrected or dropped. Separately, each sector shows the portal-published <i>sector-wide</i> average (99acres, MagicBricks, Square Yards, Housing) as an independent check — a premium median that falls below it is flagged in the panel.</div>
  <div class="note"><h3>Search</h3>The search box knows every quoted project plus every named residential society, condominium and neighbourhood OpenStreetMap has in Gurugram. A society resolves to the sector its footprint sits in and shows that sector's range; societies OSM only has near a point-mapped sector are marked "near". Sector prices are not resolved for societies with no quote — you get the location and the sector's ballpark.</div>
  <div class="note"><h3>Map data</h3>Sector polygons, roads, metro lines, the IGI footprint, the Delhi–Haryana line, parks, golf courses and landmarks are from OpenStreetMap (© OpenStreetMap contributors, ODbL). Sectors OSM has only as a point — including 99, 99A, 76, 77, 95 — are dashed circles at their mapped location. "Entry to Delhi" markers are where NH-48, Dwarka Expressway, Old Delhi Road and MG Road cross the state line.</div>
</div>
<footer>
  <div class="stats">
    <div class="stat"><b id="st-sectors">–</b><span>sectors with price evidence</span></div>
    <div class="stat"><b id="st-quotes">–</b><span>project quotes</span></div>
    <div class="stat"><b id="st-soc">–</b><span>societies searchable</span></div>
    <div class="stat"><b>__GENERATED__</b><span>compiled</span></div>
  </div>
  <p>Sectors are coloured light-to-dark red as the median premium-developer quote rises. Hover a sector for its range and the projects behind it; click to pin the evidence. Search any society, project, road or sector; drag to pan, scroll to zoom. Compiled __GENERATED__ from public listings. Not investment advice; verify any quote against the project's RERA registration before relying on it.</p>
</footer>

<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const BANDS = [
  {max:8000,  v:'--b1', l:'< 8k'},
  {max:11000, v:'--b2', l:'8–11k'},
  {max:14000, v:'--b3', l:'11–14k'},
  {max:18000, v:'--b4', l:'14–18k'},
  {max:25000, v:'--b5', l:'18–25k'},
  {max:40000, v:'--b6', l:'25–40k'},
  {max:Infinity, v:'--b7', l:'40k +'},
];
const secName = k => k==='MANESAR' ? 'Manesar (IMT / M3M township)' : (D.sectors[k] && D.sectors[k].inset ? 'Sohna Sector '+(D.sectors[k].label||k) : 'Sector '+(D.sectors[k]&&D.sectors[k].label||k));
const BUCKET_LABEL = {launch:'New launch', uc:'Under construction', ready:'Ready', resale:'Resale'};
const active = new Set(['launch','uc','ready','resale']);
const fmtK = v => v>=100000 ? (v/100000).toFixed(1).replace(/\.0$/,'')+' L' : (v/1000).toFixed(v<10000?1:0).replace(/\.0$/,'')+'k';
const fmt = v => '₹'+v.toLocaleString('en-IN');
const cr = v => { const c = v/1e7; return c>=10 ? c.toFixed(0) : c>=3 ? c.toFixed(1) : c.toFixed(2); };
const median = a => {const s=[...a].sort((x,y)=>x-y), m=s.length>>1; return s.length%2? s[m] : (s[m-1]+s[m])/2;};
const bandOf = v => BANDS.find(b=>v<b.max);
const bandIdx = v => BANDS.findIndex(b=>v<b.max);
const esc = s => String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const mid = q => (q.price_psf_min+q.price_psf_max)/2;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const track = (name, params) => { try { if(typeof gtag === 'function') gtag('event', name, params||{}); } catch(e){} };

// typical super areas, editable; persisted locally
let SIZES = {2:1350, 3:1900, 4:2800};
try { const s = JSON.parse(localStorage.getItem('ggn-bhk-sizes')||'null'); if(s && s[2] && s[3] && s[4]) SIZES = s; } catch(e){}

// ---- aggregate ---------------------------------------------------------
const SRC_RANK = Object.fromEntries(D.src.map(([id],i)=>[id,i]));
const SRC_LABEL = Object.fromEntries(D.src);
const srcSel = new Set(D.src.map(([id])=>id));
function aggregate(){
  const by = {};
  for(const q of D.quotes){ if(!active.has(q.bucket) || !srcSel.has(q.src)) continue; (by[q.sector] ||= []).push(q); }
  const agg = {};
  for(const [s, all] of Object.entries(by)){
    // one row per project: the most direct enabled source is primary, the rest ride along as alternatives
    const byP = {};
    for(const q of all){ const k = q.project.toLowerCase().replace(/\s*\(resale\)$/,''); (byP[k] ||= []).push(q); }
    // single reported deals rank behind every regular quote: they appear on the card but only set the price when nothing else exists
    const rows = Object.values(byP).map(qs=>{ qs.sort((a,b)=>(SRC_RANK[a.src]+(a.deal?10:0))-(SRC_RANK[b.src]+(b.deal?10:0))); const p = Object.assign({}, qs[0]); p.alts = qs.slice(1);
      if(!(p.configs && p.configs.length)){ const w = p.alts.find(a=>a.configs && a.configs.length); if(w){ p.configs = w.configs; p.configs_as_of = w.configs_as_of; p.configs_stale = w.configs_stale; p.configs_from = w.sot ? w.sot.label : SRC_LABEL[w.src]; p.source_psf = w.source_psf; } }
      return p; });
    const mids = rows.map(mid);
    agg[s] = {rows: rows.sort((a,b)=>mid(b)-mid(a)), lo:Math.min(...mids), hi:Math.max(...mids), med:median(mids), n:rows.length};
  }
  return agg;
}
const srcChips = document.getElementById('srcchips');
srcChips.innerHTML = D.src.filter(([id])=>D.quotes.some(q=>q.src===id)).map(([id,label],i)=>`<button class="chip src" data-src="${id}" data-rank="${SRC_RANK[id]}" aria-pressed="true">${label} <span class="n">${D.quotes.filter(q=>q.src===id).length}</span></button>`).join('');
srcChips.addEventListener('click', ev=>{
  const c = ev.target.closest('.chip[data-src]'); if(!c) return;
  const id = c.dataset.src, on = c.getAttribute('aria-pressed')==='true';
  if(on && srcSel.size===1) return;
  c.setAttribute('aria-pressed', on?'false':'true'); on ? srcSel.delete(id) : srcSel.add(id);
  track('source_filter', {source: id, on: !on});
  AGG = aggregate(); paint(); renderInspector(); renderRoad(); renderTable();
});
let AGG = aggregate();
const bandSel = new Set();
const inBand = idx => !bandSel.size || bandSel.has(idx);

// ---- legend ------------------------------------------------------------
(function(){
  const L = document.getElementById('legend');
  L.innerHTML = `<span class="dir">cheaper →</span>` + BANDS.map((b,i)=>`<button class="sw" data-i="${i}" aria-pressed="false" title="Show only sectors in this band"><i style="background:var(${b.v})"></i><small>${b.l}</small></button>`).join('')
    + `<span class="dir" style="margin-left:8px">→ pricier</span><button class="clear" id="bandclear">clear filter</button>`
    + `<div class="key"><i style="background:repeating-linear-gradient(45deg,var(--nodata) 0 4px,var(--nodata-hatch) 4px 6px)"></i>no premium quotes</div>`
    + `<div class="key"><i style="background:radial-gradient(circle,var(--nodata-hatch) 1.2px,var(--nodata) 1.4px) 0 0/6px 6px"></i>no premium apartment stock</div>`
    + `<div class="key"><i style="border:1.5px dashed var(--muted);background:transparent"></i>approx. location</div>`;
})();

// ---- map build ---------------------------------------------------------
const svg = document.getElementById('map'), wrap = document.getElementById('mapwrap');
const NS = 'http://www.w3.org/2000/svg';
const el = (t,a={})=>{const e=document.createElementNS(NS,t); for(const k in a) e.setAttribute(k,a[k]); return e;};
const G = id => document.getElementById(id);
const gS=G('g-sectors'), gP=G('g-points'), gL=G('g-labels'), gRL=G('g-roadlabels');
const sectorEls = {};
const numOf = k => k==='MANESAR' ? 2000 : k.startsWith('SOHNA') ? 1000+parseInt(k.split('-')[1]) : parseInt(k);
const order = Object.keys(D.sectors).sort((a,b)=>numOf(a)-numOf(b)||a.localeCompare(b));

// Delhi side of the state line gets a quiet wash so the eye reads "not Gurugram" without a second colour scale
(function(){
  const [x,y,w,h] = D.canvas;
  G('g-base').appendChild(el('rect',{x:x-400,y:y-400,width:w+800,height:h+800,fill:'var(--bg)'}));
})();
for(const g of D.green){ G('g-green').appendChild(el('path',{d:g.d, class:'green '+g.k})); }
for(const k of order){
  const s = D.sectors[k];
  if(s.boundary){
    const d = s.rings.map(r=>'M'+r.map(p=>p.join(',')).join('L')+'Z').join('');
    const p = el('path',{d, class:'sector', 'data-s':k, tabindex:0, role:'button', 'aria-label':secName(k)});
    gS.appendChild(p); sectorEls[k]=p;
  }
}
for(const d of D.airport.rings) G('g-air').appendChild(el('path',{d, class:'apron'}));
for(const d of D.airport.runways) G('g-air').appendChild(el('path',{d, class:'runway'}));
for(const d of D.airport.terminals) G('g-air').appendChild(el('path',{d, class:'terminal'}));
for(const r of D.roads){ if(r.c==='sc'||r.c==='tt') G('g-roads-minor').appendChild(el('path',{d:r.d, class:'roadedge '+r.c})); }
for(const r of D.roads){ if(r.c==='sc'||r.c==='tt') G('g-roads-minor').appendChild(el('path',{d:r.d, class:'road '+r.c})); }
for(const r of D.roads){ if(r.c!=='sc'&&r.c!=='tt') G('g-roads').appendChild(el('path',{d:r.d, class:'roadedge '+r.c})); }
const roadEls = {};
for(const r of D.roads){ if(r.c!=='sc'&&r.c!=='tt'){ const p = el('path',{d:r.d, class:'road '+r.c}); if(r.k){ p.dataset.r = r.k; (roadEls[r.k] ||= []).push(p);} G('g-roads').appendChild(p);} }
for(const r of D.roads){ if(r.k) G('g-roadhit').appendChild(el('path',{d:r.d, class:'roadhit', 'data-r':r.k})); }
for(const b of D.border) G('g-border').appendChild(el('path',{d:b.d, class:'border'}));
for(const m of D.metro) G('g-metro').appendChild(el('path',{d:m.d, class:'metrocase'}));
for(const m of D.metro) G('g-metro').appendChild(el('path',{d:m.d, class:'metro', style:`stroke:${m.c}`}));
for(const k of order){
  const s = D.sectors[k];
  if(!s.boundary){
    const g = el('g',{class:'pt', 'data-s':k, tabindex:0, role:'button', 'aria-label':secName(k)+' (approximate location)'});
    g.appendChild(el('circle',{cx:s.cx, cy:s.cy, r:14}));
    gP.appendChild(g); sectorEls[k]=g;
  }
  const lab = s.label || k;
  const t = el('text',{x:s.cx, y:s.cy, class:'lbl'+(lab.length>2?' small':'')}); t.textContent = lab; gL.appendChild(t); s._lbl = t;
}
if(D.sohnaStrip){
  const c = el('text',{x:D.sohnaStrip.x, y:D.sohnaStrip.y, class:'rlbl', style:'text-anchor:end'}); c.textContent='Off-map: Sohna sectors (~20 km S) and Manesar (M) →'; gRL.appendChild(c);
}
for(const r of D.roadLabels){
  const t = el('text',{x:r.x, y:r.y, class:'rlbl'+(/Golf/.test(r.t)?' gc':''), transform:`rotate(${r.r} ${r.x} ${r.y})`}); t.textContent=r.t; gRL.appendChild(t);
}
for(const a of D.areas){ const t = el('text',{x:a.x, y:a.y, class:'area', 'data-t':a.t}); t.textContent=a.n; G('g-areas').appendChild(t); }
// Delhi / Haryana tags along the state line, near NH-48
(function(){
  const t1 = el('text',{x:790,y:355,class:'blbl'}); t1.textContent='Delhi'; G('g-border').appendChild(t1);
  const t2 = el('text',{x:700,y:395,class:'blbl'}); t2.textContent='Haryana'; G('g-border').appendChild(t2);
})();
for(const s of D.stations){
  const g = el('g',{class:'st','data-k':s.k}); g.appendChild(el('circle',{cx:s.x,cy:s.y,r:2.8}));
  const t = el('text',{x:s.x+5,y:s.y-4}); t.textContent=s.n; g.appendChild(t); G('g-stations').appendChild(g);
}
const GLYPH = {hosp:'H', mall:'S', office:'B', air:'✈', golf:'⛳', toll:'T', junction:'✕', civic:'★', rail:'≡'};
for(const l of D.landmarks){
  const g = el('g',{class:'lm '+l.c,'data-t':l.t}); g.appendChild(el('title')).textContent = l.n;
  g.appendChild(el('circle',{cx:l.x,cy:l.y,r:7}));
  const gl = el('text',{x:l.x,y:l.y,class:'g'}); gl.textContent = GLYPH[l.c]||'•'; g.appendChild(gl);
  const t = el('text',{x:l.x+10,y:l.y+4,class:'t'}); t.textContent = l.n; g.appendChild(t);
  G('g-landmarks').appendChild(g);
}
for(const e of D.entries){
  const g = el('g',{class:'entry','data-major':e.major?1:0});
  g.appendChild(el('path',{d:`M${e.x},${e.y-9}l7,12h-14z`}));
  const t = el('text',{x:e.x+9,y:e.y-5}); t.textContent = '→ Delhi · '+e.n; g.appendChild(t); G('g-entries').appendChild(g);
}
for(const s of D.societies){ const t = el('text',{x:s.x,y:s.y,class:'soc'}); t.textContent=s.n; G('g-soc').appendChild(t); }
document.getElementById('st-soc').textContent = D.societies.length.toLocaleString('en-IN');

function paint(){
  for(const k of order){
    const s = D.sectors[k], a = AGG[k], e = sectorEls[k];
    if(!e) continue;
    const isPath = s.boundary;
    if(a){
      const b = bandOf(a.med), idx = bandIdx(a.med);
      const fill = `var(${b.v})`;
      if(isPath){ e.classList.remove('nodata','nostock'); e.style.fill = fill; }
      else { e.firstChild.style.fill = fill; e.firstChild.style.stroke = 'var(--muted)'; }
      // the ramp runs light→dark in both themes, so label ink depends only on the step
      const fillIsDark = idx>=4;
      s._lbl.style.fill = fillIsDark ? '#ffffff' : '#1a222c';
      s._lbl.style.stroke = fillIsDark ? 'rgba(0,0,0,.35)' : 'rgba(255,255,255,.55)';
      const dim = !inBand(idx); e.classList.toggle('dim', dim); s._lbl.classList.toggle('dim', dim);
    } else {
      e.classList.toggle('dim', bandSel.size>0); s._lbl.classList.toggle('dim', bandSel.size>0);
      const ns = !!D.nostock[k];
      if(isPath){ e.classList.toggle('nodata', !ns); e.classList.toggle('nostock', ns); e.style.fill=''; }
      else { e.firstChild.style.fill='var(--nodata)'; e.firstChild.style.stroke='var(--nodata-hatch)'; e.firstChild.style.strokeDasharray = ns ? '1 2' : ''; }
      s._lbl.style.fill='var(--muted)'; s._lbl.style.stroke='var(--bg)';
    }
    if(!isPath){ s._lbl.style.fill = a ? 'var(--ink)' : 'var(--muted)'; s._lbl.style.stroke='var(--panel)'; }
  }
  document.getElementById('st-sectors').textContent = Object.keys(AGG).length;
  document.getElementById('st-quotes').textContent = Object.values(AGG).reduce((n,a)=>n+a.n,0);
  for(const c of document.querySelectorAll('.chip[data-b]')){ c.querySelector('.n').textContent = D.quotes.filter(q=>q.bucket===c.dataset.b).length; }
}
paint();

// ---- pan / zoom --------------------------------------------------------
const [cx0,cy0,cw,ch] = D.bbox;
let VB = {x:cx0,y:cy0,w:cw,h:ch}, BASEW = cw;
function applyVB(){
  svg.setAttribute('viewBox', `${VB.x} ${VB.y} ${VB.w} ${VB.h}`);
  const z = VB.w/BASEW;
  svg.style.setProperty('--z', z.toFixed(4));
  svg.style.setProperty('--zf', Math.pow(z,0.78).toFixed(4));
  svg.classList.toggle('z2', z<0.62); svg.classList.toggle('z3', z<0.36); svg.classList.toggle('z4', z<0.22);
}
function fit(){
  const r = svg.getBoundingClientRect(), ar = r.width/Math.max(1,r.height);
  let w = cw, h = ch;
  if(w/h < ar) w = h*ar; else h = w/ar;
  VB = {x:cx0+(cw-w)/2, y:cy0+(ch-h)/2, w, h}; BASEW = w; applyVB();
}
function clampVB(){
  const minW = BASEW/16, maxW = BASEW*1.4;
  if(VB.w<minW||VB.w>maxW){ const f = Math.min(maxW,Math.max(minW,VB.w))/VB.w; VB.w*=f; VB.h*=f; }
  VB.x = Math.min(Math.max(VB.x, cx0 - VB.w*0.7), cx0+cw - VB.w*0.3);
  VB.y = Math.min(Math.max(VB.y, cy0 - VB.h*0.7), cy0+ch - VB.h*0.3);
}
function toSvg(px,py){ const r = svg.getBoundingClientRect(); return {x: VB.x + (px-r.left)/r.width*VB.w, y: VB.y + (py-r.top)/r.height*VB.h}; }
function zoomAt(f, px, py){
  const p = toSvg(px,py);
  let nw = VB.w*f; nw = Math.min(BASEW*1.4, Math.max(BASEW/16, nw)); f = nw/VB.w;
  VB.x = p.x - (p.x-VB.x)*f; VB.y = p.y - (p.y-VB.y)*f; VB.w = nw; VB.h *= f;
  clampVB(); applyVB();
}
let anim = null;
function flyTo(x, y, w){
  if(anim) cancelAnimationFrame(anim);
  w = Math.min(BASEW*1.4, Math.max(BASEW/16, w));
  const r = svg.getBoundingClientRect(), h = w*r.height/r.width;
  const to = {x:x-w/2, y:y-h/2, w, h}, from = {...VB};
  if(reduceMotion){ VB = to; clampVB(); applyVB(); return; }
  const t0 = performance.now(), dur = 380;
  const step = now => {
    const t = Math.min(1,(now-t0)/dur), e = 1-Math.pow(1-t,3);
    VB = {x:from.x+(to.x-from.x)*e, y:from.y+(to.y-from.y)*e, w:from.w+(to.w-from.w)*e, h:from.h+(to.h-from.h)*e};
    applyVB(); if(t<1) anim = requestAnimationFrame(step); else anim=null;
  };
  anim = requestAnimationFrame(step);
}
fit(); addEventListener('resize', ()=>{ const c = {x:VB.x+VB.w/2, y:VB.y+VB.h/2, w:VB.w}; fit(); const r=svg.getBoundingClientRect(); VB.w=c.w; VB.h=c.w*r.height/r.width; VB.x=c.x-VB.w/2; VB.y=c.y-VB.h/2; clampVB(); applyVB(); });
svg.addEventListener('wheel', ev=>{ ev.preventDefault(); zoomAt(Math.exp(ev.deltaY*(ev.deltaMode===1?0.05:0.0016)), ev.clientX, ev.clientY); }, {passive:false});
const ptrs = new Map(); let dragged = false, pinch0 = null;
// Pointer capture is taken only once a drag starts: Chrome delivers the click to the capturing element, so
// capturing on pointerdown would make every plain click land on the <svg> instead of the sector under the cursor.
svg.addEventListener('pointerdown', ev=>{ if(ev.button!==0 && ev.pointerType==='mouse') return; ptrs.set(ev.pointerId,{x:ev.clientX,y:ev.clientY,sx:ev.clientX,sy:ev.clientY}); dragged=false; if(ptrs.size===2){ const [a,b]=[...ptrs.values()]; pinch0 = {d:Math.hypot(a.x-b.x,a.y-b.y), w:VB.w}; try{ for(const id of ptrs.keys()) svg.setPointerCapture(id); }catch(e){} } });
svg.addEventListener('pointermove', ev=>{
  const p = ptrs.get(ev.pointerId); if(!p) return;
  const r = svg.getBoundingClientRect();
  if(ptrs.size===1){
    const dx = ev.clientX-p.x, dy = ev.clientY-p.y;
    if(!dragged && Math.hypot(ev.clientX-p.sx, ev.clientY-p.sy) > 4){ dragged = true; svg.classList.add('dragging'); tip.classList.remove('on'); try{ svg.setPointerCapture(ev.pointerId); }catch(e){} }
    if(dragged){ VB.x -= dx/r.width*VB.w; VB.y -= dy/r.height*VB.h; clampVB(); applyVB(); }
    p.x = ev.clientX; p.y = ev.clientY;
  } else if(ptrs.size===2){
    p.x = ev.clientX; p.y = ev.clientY; dragged = true;
    const [a,b]=[...ptrs.values()], d = Math.hypot(a.x-b.x,a.y-b.y);
    if(pinch0 && d>0){ const f = (pinch0.w*pinch0.d/d)/VB.w; zoomAt(f,(a.x+b.x)/2,(a.y+b.y)/2); }
  }
});
const endPtr = ev=>{ ptrs.delete(ev.pointerId); if(ptrs.size<2) pinch0=null; if(!ptrs.size){ svg.classList.remove('dragging'); setTimeout(()=>{dragged=false;},0); } };
svg.addEventListener('pointerup', endPtr); svg.addEventListener('pointercancel', endPtr);
document.getElementById('theme').onclick = ()=>{
  const root = document.documentElement, sysDark = matchMedia('(prefers-color-scheme: dark)').matches;
  const cur = root.getAttribute('data-theme') || (sysDark ? 'dark' : 'light'), next = cur === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next); try{ localStorage.setItem('ggn-theme', next); }catch(e){}
  track('theme_toggle', {theme: next});
};
document.getElementById('zin').onclick = ()=>{ const r=svg.getBoundingClientRect(); zoomAt(0.6, r.left+r.width/2, r.top+r.height/2); };
document.getElementById('zout').onclick = ()=>{ const r=svg.getBoundingClientRect(); zoomAt(1/0.6, r.left+r.width/2, r.top+r.height/2); };
document.getElementById('zfit').onclick = ()=>{ fit(); };
svg.addEventListener('keydown', ev=>{
  if(ev.target!==svg) return;
  const r=svg.getBoundingClientRect(), cx=r.left+r.width/2, cy=r.top+r.height/2, step=VB.w*0.08;
  if(ev.key==='+'||ev.key==='=') zoomAt(0.7,cx,cy); else if(ev.key==='-') zoomAt(1/0.7,cx,cy);
  else if(ev.key==='ArrowLeft') VB.x-=step; else if(ev.key==='ArrowRight') VB.x+=step; else if(ev.key==='ArrowUp') VB.y-=step; else if(ev.key==='ArrowDown') VB.y+=step; else if(ev.key==='0') return fit(); else return;
  ev.preventDefault(); clampVB(); applyVB();
});

// ---- layers ------------------------------------------------------------
const LAYER = {metro:['g-metro','g-stations'], landmarks:['g-landmarks','g-entries','g-areas'], minor:['g-roads-minor'], societies:['g-soc'], placenames:[]};
for(const c of document.querySelectorAll('.chip.layer')){
  if(c.getAttribute('aria-pressed')!=='true'){ for(const id of LAYER[c.dataset.l]) G(id).classList.add('hide'); if(c.dataset.l==='placenames') svg.classList.add('nonames'); }
  c.addEventListener('click', ()=>{ const on = c.getAttribute('aria-pressed')==='true'; c.setAttribute('aria-pressed', on?'false':'true'); for(const id of LAYER[c.dataset.l]) G(id).classList.toggle('hide', on); if(c.dataset.l==='placenames') svg.classList.toggle('nonames', on); track('layer_toggle', {layer: c.dataset.l, on: !on}); });
}

// ---- tooltip -----------------------------------------------------------
const tip = document.getElementById('tip');
function tipHTML(k){
  const a = AGG[k];
  const bch = D.bench[k] && D.bench[k].avg ? `<div class="m">Sector-wide portal avg ${fmt(D.bench[k].avg)} / sq ft</div>` : '';
  if(!a) return `<div class="t">${secName(k)}</div><div class="m">${D.nostock[k] ? 'No premium apartment stock — '+esc(D.nostock[k].reason) : 'No premium-developer quotes found'}${D.sectors[k].boundary?'':' · location approximate'}.</div>${bch}`;
  const rows = a.rows.slice(0,4).map(q=>`<li><span>${esc(q.project.replace(/\s*\(resale\)/i,''))}</span><span>${fmtK(q.price_psf_min)}${q.price_psf_max!==q.price_psf_min?'–'+fmtK(q.price_psf_max):''}</span></li>`).join('');
  return `<div class="t">${secName(k)}</div><div class="r">${fmtK(a.lo)}${a.hi!==a.lo?' – '+fmtK(a.hi):''} <span class="m">/ sq ft</span></div><div class="m">median ${fmt(Math.round(a.med))} · ${a.n} project${a.n>1?'s':''} · 3 BHK ≈ ₹${cr(a.lo*SIZES[3])}–${cr(a.hi*SIZES[3])} cr${D.sectors[k].boundary?'':' · location approximate'}</div>${bch}<ul>${rows}${a.n>4?`<li><span class="m">+${a.n-4} more</span><span></span></li>`:''}</ul><div class="hint2">Click to pin the full evidence →</div>`;
}
function showTip(k, ev){
  tip.innerHTML = tipHTML(k); tip.classList.add('on');
  const r = wrap.getBoundingClientRect();
  let x = ev.clientX - r.left + 14, y = ev.clientY - r.top + 14;
  if(x + 270 > r.width) x = ev.clientX - r.left - 280;
  if(y + tip.offsetHeight + 10 > r.height) y = ev.clientY - r.top - tip.offsetHeight - 14;
  tip.style.left = x+'px'; tip.style.top = Math.max(4,y)+'px';
}
const ROAD_CLASS = {mw:'Expressway / national highway', gc:'Golf Course corridor', tr:'Trunk road', pr:'Main road', sc:'Secondary road', tt:'Local road'};
let hovRoad = null;
function setHovRoad(k){ if(hovRoad===k) return; if(hovRoad) for(const e of roadEls[hovRoad]||[]) e.classList.remove('hov'); hovRoad = k; if(k) for(const e of roadEls[k]||[]) e.classList.add('hov'); }
svg.addEventListener('mousemove', ev=>{
  if(dragged || ptrs.size) return;
  const t = ev.target.closest('[data-s]');
  if(t){ setHovRoad(null); showTip(t.dataset.s, ev); return; }
  const rh = ev.target.closest('.roadhit');
  if(rh){ const k = rh.dataset.r, i = D.roadInfo[k]; setHovRoad(k);
    const secs = i.secs.filter(s=>AGG[s]), meds = secs.map(s=>AGG[s].med);
    tip.innerHTML = `<div class="t">${esc(k)}</div><div class="m">${ROAD_CLASS[i.c]} · ${i.km} km on this map · ${i.secs.length} sector${i.secs.length!==1?'s':''}</div>${meds.length?`<div class="r">${fmtK(Math.min(...meds))}${meds.length>1?' – '+fmtK(Math.max(...meds)):''} <span class="m">/ sq ft · sector medians along it</span></div>`:''}<div class="hint2">Click to list the sectors along it →</div>`;
    tip.classList.add('on'); const r = wrap.getBoundingClientRect(); let x = ev.clientX-r.left+14, y = ev.clientY-r.top+14; if(x+270>r.width) x = ev.clientX-r.left-280; if(y+tip.offsetHeight+10>r.height) y = ev.clientY-r.top-tip.offsetHeight-14; tip.style.left=x+'px'; tip.style.top=Math.max(4,y)+'px';
    return; }
  setHovRoad(null); tip.classList.remove('on');
});
svg.addEventListener('mouseleave', ()=>tip.classList.remove('on'));

// ---- inspector ---------------------------------------------------------
let pinned = null, hlProject = null;
const insp = document.getElementById('inspector');
function pin(k, project){
  if(pinnedRoad){ for(const e of roadEls[pinnedRoad]||[]) e.classList.remove('sel'); pinnedRoad = null; }
  if(pinned && sectorEls[pinned]) sectorEls[pinned].classList.remove('pinned');
  pinned = k; hlProject = project||null; if(sectorEls[k]) sectorEls[k].classList.add('pinned');
  track('sector_pinned', {sector: secName(k), median: AGG[k] ? Math.round(AGG[k].med) : 0, has_quotes: !!AGG[k]});
  renderInspector();
}
function sectorCentre(k){
  const s = D.sectors[k]; if(!s) return null;
  if(s.bb) return {x:(s.bb[0]+s.bb[2])/2, y:(s.bb[1]+s.bb[3])/2, w:Math.max(s.bb[2]-s.bb[0], (s.bb[3]-s.bb[1])*1.4)*2.6};
  return {x:s.cx, y:s.cy, w:BASEW/5};
}
function bhkRows(lo, hi){
  return [2,3,4].map(b=>`<tr><td>${b} BHK</td><td><input type="number" min="300" max="20000" step="50" value="${SIZES[b]}" data-b="${b}" aria-label="${b} BHK super area in sq ft"> <span style="color:var(--muted);font-size:12px">sq ft</span></td><td class="num" data-lo="${lo}" data-hi="${hi}" data-bb="${b}">${tixText(lo,hi,SIZES[b])}</td></tr>`).join('');
}
function newsHTML(k){
  const ns = D.sectorNews[k]; if(!ns || !ns.length) return '';
  return `<div class="bench"><div class="eyebrow">In the press · sector / corridor</div>${ns.slice(0,3).map(n=>`<div><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.publisher||'article')}</a> <span style="color:var(--muted)">${esc(n.as_of)}</span> — ${esc(n.figure||n.headline)}</div>`).join('')}</div>`;
}
function benchHTML(k, a){
  const b = D.bench[k]; if(!b || !b.portals || !b.portals.length) return newsHTML(k);
  const ps = b.portals.map(p=>`<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.portal)}</a> ${fmt(p.avg)}`).join(' · ');
  if(!b.avg) return `<div class="bench"><div class="eyebrow">Independent check · sector-wide average</div><div>Portals disagree too much for a single figure: ${ps}. No stale-check applied.</div></div>`;
  let check = '';
  if(a){ const r = a.med/b.avg;
    check = r < 0.95 ? `<div class="warn">⚠ Our premium median (${fmt(Math.round(a.med))}) is below the sector-wide average. Either these quotes are stale/mis-tagged, or the portal average is pulled up by one luxury project in the sector — read the rows before trusting the colour.</div>`
          : r > 2.5 ? `<div class="ok">Premium median is ${r.toFixed(1)}× the sector-wide average — this sector's colour reflects a few luxury projects, not typical stock.</div>`
          : `<div class="ok">Premium median is ${r.toFixed(1)}× the sector-wide average, as expected for branded stock.</div>`; }
  return `<div class="bench"><div class="eyebrow">Independent check · sector-wide average, all segments</div><div><b>${fmt(b.avg)}</b> / sq ft · ${ps}${b.disputed?' <span style="color:var(--muted)">(portals disagree on this sector; figure anchored on the more conservative source)</span>':''}</div>${check}</div>${newsHTML(k)}`;
}
const confPill = q => q.confidence ? `<span class="pill conf ${esc(q.confidence)}" title="${q.confidence==='A'?'Two independent sources agree within 15%':q.confidence==='B'?'One solid portal or developer page':'Aggregator, broker or unverified'}">${esc(q.confidence)}</span>` : '';
const tixText = (lo,hi,a) => '₹'+cr(lo*a)+(hi!==lo?' – '+cr(hi*a):'')+' cr';
const bhkName = b => b==='floor' ? 'Floor' : b==='villa' ? 'Villa/plot' : b==='penthouse' ? 'Penthouse' : b+' BHK';
const cfgTable = q => {
  const by = {}; for(const c of q.configs){ if(!(c.area>0 && c.price_cr>0)) continue; (by[c.bhk] = by[c.bhk]||[]).push(c); }
  const keys = Object.keys(by).sort((a,b)=>(parseFloat(a)||9)-(parseFloat(b)||9)); if(!keys.length) return '';
  const rows = keys.map(b=>{ const cs = by[b].sort((x,y)=>x.area-y.area), lo=cs[0], hi=cs[cs.length-1];
    const area = lo.area===hi.area ? lo.area.toLocaleString('en-IN') : lo.area.toLocaleString('en-IN')+'–'+hi.area.toLocaleString('en-IN');
    const pr = lo.price_cr===hi.price_cr ? '₹'+lo.price_cr+' cr' : '₹'+lo.price_cr+' – '+hi.price_cr+' cr';
    const psf = Math.round(cs.reduce((t,c)=>t+c.price_cr*1e7/c.area,0)/cs.length);
    return `<tr><td>${bhkName(b)}</td><td class="n">${area} sq ft</td><td class="n">${pr}</td><td class="n" style="color:var(--muted)">${psf.toLocaleString('en-IN')}/sq ft</td></tr>`; }).join('');
  const from = q.configs_from || (q.sot ? q.sot.label : 'source');
  const head = q.configs_stale ? `Unit sizes on ${esc(from)} — its listed prices are launch-era; current asking there is ₹${(q.source_psf||mid(q)).toLocaleString('en-IN')}/sq ft` : `${q.configs_from ? 'Unit table from' : 'Quoted on'} ${esc(from)}${q.configs_as_of?' · '+esc(q.configs_as_of):''}`;
  const tail = q.configs_stale ? `<div style="margin-top:4px">${keys.map(b=>{ const cs=by[b], lo=Math.min(...cs.map(c=>c.area)), hi=Math.max(...cs.map(c=>c.area)), p=(q.source_psf||mid(q)); return `${bhkName(b)} ≈ ₹${cr(p*lo)}${hi!==lo?'–'+cr(p*hi):''} cr`; }).join(' · ')} <span>at current asking</span></div>` : '';
  return `<div class="cfgwrap"><table class="cfg"><tr><th colspan="4">${head}</th></tr>${rows}</table></div>${tail}`;
};
const projTix = q => (q.configs && q.configs.length) ? cfgTable(q) : `${[2,3,4].map(b=>'₹'+cr(mid(q)*SIZES[b])).join(' · ')} <span>cr for 2 · 3 · 4 BHK — indicative, ₹/sq ft × your areas above; no unit table on the source</span>`;
let pinnedRoad = null;
function pinRoad(k){
  if(pinnedRoad) for(const e of roadEls[pinnedRoad]||[]) e.classList.remove('sel');
  if(pinned && sectorEls[pinned]) sectorEls[pinned].classList.remove('pinned');
  pinned = null; pinnedRoad = k; for(const e of roadEls[k]||[]) e.classList.add('sel');
  track('road_pinned', {road: k});
  renderRoad();
}
function renderRoad(){
  const k = pinnedRoad; if(!k) return; const i = D.roadInfo[k];
  const secs = i.secs.slice().sort((a,b)=>((AGG[b]?.med??-1)-(AGG[a]?.med??-1)) || numOf(a)-numOf(b));
  const meds = secs.filter(s=>AGG[s]).map(s=>AGG[s].med);
  const rows = secs.map(s=>{ const a = AGG[s]; if(!a) return `<li class="proj secrow nod" data-s="${s}"><span><span class="sw" style="background:repeating-linear-gradient(45deg,var(--nodata) 0 4px,var(--nodata-hatch) 4px 6px)"></span>${secName(s)}</span><span class="num none" style="font:12px 'IBM Plex Sans',sans-serif;color:var(--muted)">no premium quote</span></li>`;
    return `<li class="proj secrow" data-s="${s}"><span><span class="sw" style="background:var(${bandOf(a.med).v})"></span>${secName(s)}</span><span class="num">${fmtK(a.lo)}${a.hi!==a.lo?' – '+fmtK(a.hi):''}<small>median ${fmt(Math.round(a.med))} · ${a.n} quote${a.n>1?'s':''} · 3 BHK ≈ ₹${cr(a.med*SIZES[3])} cr</small></span></li>`; }).join('');
  insp.innerHTML = `<div class="eyebrow">Road</div><h2>${esc(k)}</h2>
    <div class="sub">${ROAD_CLASS[i.c]} · ${i.km} km on this map · passes ${i.secs.length} sector${i.secs.length!==1?'s':''}</div>
    ${meds.length?`<div class="range">${fmtK(Math.min(...meds))}${meds.length>1?' – '+fmtK(Math.max(...meds)):''} <span style="font-size:13px;color:var(--muted)">₹ / sq ft</span></div><div class="sub">sector medians along it, lowest to highest · ${meds.length} of ${i.secs.length} sectors have quotes</div>`:'<div class="sub">No priced sectors along this stretch.</div>'}
    <button class="locate" data-road="${esc(k)}">Show whole road</button>
    <ul class="projects">${rows}</ul>
    <div class="how">Sectors are listed richest first. Click one to open its evidence. A sector counts as "along" the road if the drawn centreline passes through its boundary (or within ~600 m of a point-mapped sector).</div>`;
}
insp.addEventListener('click', ev=>{
  const a = ev.target.closest('a[href^="http"]'); if(a){ track('source_click', {url: a.href.slice(0,150), sector: pinned ? secName(pinned) : ''}); }
  const li = ev.target.closest('li.secrow'); if(li){ pin(li.dataset.s); const c = sectorCentre(li.dataset.s); if(c) flyTo(c.x,c.y,c.w); return; }
  const b = ev.target.closest('[data-road]'); if(b){ const bb = D.roadInfo[b.dataset.road].bb; flyTo((bb[0]+bb[2])/2,(bb[1]+bb[3])/2, Math.max(bb[2]-bb[0], (bb[3]-bb[1])*1.4)*1.25); }
});
function renderInspector(){
  const k = pinned; if(!k) return;
  const a = AGG[k], s = D.sectors[k];
  const locate = `<button class="locate" data-loc="${k}">Show on map</button>`;
  if(!a){ const ns = D.nostock[k]; insp.innerHTML = `<div class="eyebrow">Sector</div><h2>${secName(k)}</h2><p class="empty" style="margin-top:10px">${ns?`No premium apartment stock: ${esc(ns.reason)}${ns.source_url?` (<a href="${esc(ns.source_url)}" target="_blank" rel="noopener">source</a>)`:''}.`:'No quotes from premium developers matched the current filters.'}${s.boundary?'':' Its position on the map is approximate — OpenStreetMap has this sector only as a point.'}</p>${benchHTML(k,null)}${locate}`; return; }
  const list = a.rows.map(q=>`<li class="proj${hlProject && q.project===hlProject?' hl':''}" data-p="${esc(q.project)}" data-url="${esc(q.source_url)}" title="Open the source page for this quote">
      <div class="row"><div><div class="name"><a href="${esc(q.source_url)}" target="_blank" rel="noopener">${esc(q.project)}</a></div><div class="dev">${esc(q.developer||'')}</div></div>
      <div class="psf">${fmt(q.price_psf_min)}${q.price_psf_max!==q.price_psf_min?'–'+q.price_psf_max.toLocaleString('en-IN'):''}</div></div>
      <div class="tix" data-mid="${mid(q)}">${projTix(q)}</div>
      ${q.basis?`<div class="basis">${esc(q.basis)}</div>`:''}
      ${q.source_psf && (q.source_psf < q.price_psf_min*0.85 || q.source_psf > q.price_psf_max*1.15) ? `<div class="basis" style="color:var(--muted)">Square Yards' tracked price is ₹${q.source_psf.toLocaleString('en-IN')}/sq ft${q.configs_as_of?' ('+esc(q.configs_as_of)+')':''}; this row keeps its stronger source.</div>` : ''}
      <div class="meta"><span class="pill ${q.bucket}">${BUCKET_LABEL[q.bucket]}</span><span class="pill src" title="${esc(q.sot?q.sot.what:'')}">${esc(q.sot?q.sot.label:(q.source_type||'source'))}</span>${confPill(q)}<span>${esc(q.as_of||'')}</span>${q.second_source_url?`<a href="${esc(q.second_source_url)}" target="_blank" rel="noopener" style="font-size:11px">2nd source</a>`:''}</div>
      ${q.audit&&q.audit.reason?`<div class="basis" style="color:var(--muted)">Audit: ${esc(q.audit.reason)}</div>`:''}
      ${q.alts && q.alts.length ? `<div class="alts">Also reported: ${q.alts.map(a=>`<a href="${esc(a.source_url)}" target="_blank" rel="noopener" title="${esc(a.basis||'')}">${esc(a.sot?a.sot.label:SRC_LABEL[a.src])}${a.deal?' (one reported deal)':''}</a> <b>${fmt(a.price_psf_min)}${a.price_psf_max!==a.price_psf_min?'–'+a.price_psf_max.toLocaleString('en-IN'):''}</b>${a.as_of?' <span style="color:var(--muted)">'+esc(a.as_of)+'</span>':''}`).join(' · ')}</div>` : ''}
      <span class="go">open source ↗</span>
    </li>`).join('');
  insp.innerHTML = `<div class="eyebrow">Sector</div><h2>${secName(k)}</h2>
    <div class="range">${fmtK(a.lo)}${a.hi!==a.lo?' – '+fmtK(a.hi):''} <span style="font-size:13px;color:var(--muted)">₹ / sq ft</span></div>
    <div class="sub">median ${fmt(Math.round(a.med))} · ${a.n} project${a.n>1?'s':''} · band <b style="color:var(--ink-2)">${bandOf(a.med).l}</b>${s.boundary?'':' · map position approximate'}</div>
    ${locate}
    <div class="bhk"><div class="eyebrow">Indicative ticket size · ₹ crore</div>
      <table>${bhkRows(a.lo,a.hi)}</table>
      <small>Sector ₹/sq ft range × super area. Edit the areas to match a unit you are looking at. Excludes PLC, parking, GST and club charges.</small></div>
    ${benchHTML(k,a)}
    <ul class="projects">${list}</ul>
    <div class="how"><b>How this range was built:</b> each project's quoted ₹/sq ft is reduced to a midpoint; the range runs from the lowest to the highest midpoint and the sector is coloured by the median (${fmt(Math.round(a.med))}). Quotes are asking prices as seen on the linked page.</div>`;
  if(hlProject){ const h = insp.querySelector('.proj.hl'); if(h) h.scrollIntoView({block:'center', behavior: reduceMotion?'auto':'smooth'}); }
}
insp.addEventListener('input', ev=>{
  const i = ev.target.closest('input[data-b]'); if(!i) return;
  const v = parseInt(i.value); if(!(v>=300)) return;
  SIZES[i.dataset.b] = v; try{ localStorage.setItem('ggn-bhk-sizes', JSON.stringify(SIZES)); }catch(e){}
  for(const td of insp.querySelectorAll('td[data-bb]')) td.textContent = tixText(+td.dataset.lo, +td.dataset.hi, SIZES[td.dataset.bb]);
  for(const d of insp.querySelectorAll('.tix')) if(!d.querySelector('.cfg')) d.innerHTML = projTix({price_psf_min:+d.dataset.mid, price_psf_max:+d.dataset.mid});
});
insp.addEventListener('click', ev=>{
  const b = ev.target.closest('[data-loc]'); if(b){ const c = sectorCentre(b.dataset.loc); if(c){ flyTo(c.x,c.y,c.w); setMarker(null); } return; }
  if(ev.target.closest('a, input, button')) return;
  const card = ev.target.closest('.proj[data-url]');
  if(card){ track('source_open', {project: card.dataset.p.slice(0,100), sector: secName(pinned)}); window.open(card.dataset.url, '_blank', 'noopener'); }
});
svg.addEventListener('click', ev=>{
  if(dragged) return;
  // if the browser retargeted the click to the <svg> (pointer capture, some touch stacks), resolve what is under the cursor
  let el = ev.target;
  if(el === svg || !el.closest('[data-s], .roadhit')){ const under = document.elementFromPoint(ev.clientX, ev.clientY); if(under && svg.contains(under)) el = under; }
  const t = el.closest('[data-s]'); if(t){ pin(t.dataset.s); return; }
  const rh = el.closest('.roadhit'); if(rh) pinRoad(rh.dataset.r);
});
svg.addEventListener('keydown', ev=>{ if(ev.key==='Enter'||ev.key===' '){ const t = ev.target.closest('[data-s]'); if(t){ ev.preventDefault(); pin(t.dataset.s);} } });

// ---- chips -------------------------------------------------------------
for(const c of document.querySelectorAll('.chip[data-b]')){
  c.addEventListener('click', ()=>{
    const b = c.dataset.b, on = c.getAttribute('aria-pressed')==='true';
    if(on && active.size===1) return;
    c.setAttribute('aria-pressed', on?'false':'true');
    on ? active.delete(b) : active.add(b);
    AGG = aggregate(); paint(); renderInspector(); renderRoad(); renderTable();
  });
}

// ---- price-band filter -------------------------------------------------
document.getElementById('legend').addEventListener('click', ev=>{
  const b = ev.target.closest('.sw[data-i]');
  if(b){ const i = +b.dataset.i; bandSel.has(i) ? bandSel.delete(i) : bandSel.add(i); }
  else if(ev.target.closest('#bandclear')) bandSel.clear();
  else return;
  for(const x of document.querySelectorAll('.legend .sw[data-i]')) x.setAttribute('aria-pressed', String(bandSel.has(+x.dataset.i)));
  document.getElementById('legend').classList.toggle('filtering', bandSel.size>0);
  track('band_filter', {bands: [...bandSel].sort().map(i=>BANDS[i].l).join(',') || '(cleared)'});
  paint(); renderTable();
});

// ---- search ------------------------------------------------------------
const norm = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const IDX = [];
for(const q of D.quotes){ if(q.sector.startsWith('SOHNA')||q.sector==='MANESAR'||q.sector==='15II') {} IDX.push({t:'project', n:q.project.replace(/\s*\(resale\)/i,''), k:q.sector, x:q.x, y:q.y, q}); }
const projNames = new Set(IDX.map(i=>norm(i.n)));
for(const s of D.societies){ if(projNames.has(norm(s.n))) continue; IDX.push({t:'society', n:s.n, k:s.k, h:s.h, x:s.x, y:s.y, kind:s.kind}); }
for(const k of order){ const s = D.sectors[k]; IDX.push({t:'sector', n:secName(k), k, alias: k.toLowerCase()}); }
for(const l of D.landmarks){ IDX.push({t:'landmark', n:l.n, x:l.x, y:l.y, k:null}); }
for(const r of Object.keys(D.roadInfo)){ IDX.push({t:'road', n:r, k:null, road:r}); }
for(const s of D.stations){ IDX.push({t:'station', n:s.n+' metro', x:s.x, y:s.y, k:null}); }
for(const i of IDX) i._n = norm(i.n);
function search(qs){
  const q = norm(qs); if(!q) return [];
  const toks = q.split(' ');
  const secQ = q.match(/^(?:sector\s*|sec\s*|s\s*)?(\d+[a-z]?)$/);
  const out = [];
  for(const i of IDX){
    let sc = null;
    if(i.t==='sector'){
      if(secQ && (i.alias===secQ[1] || i.alias===secQ[1].toUpperCase().toLowerCase())) sc = 0;
      else if(i._n.includes(q) && q.length>=3) sc = 3;
    } else {
      if(i._n===q) sc = 0;
      else if(i._n.startsWith(q)) sc = 1;
      else if(i._n.includes(' '+q)) sc = 2;
      else if(i._n.includes(q)) sc = 3;
      else if(toks.length>1 && toks.every(t=>i._n.includes(t))) sc = 4;
    }
    if(sc!==null) out.push([sc + (i.t==='project'?0:i.t==='society'?0.1:i.t==='sector'?0.05:0.3), i]);
  }
  out.sort((a,b)=>a[0]-b[0] || a[1].n.length-b[1].n.length);
  return out.slice(0,9).map(o=>o[1]);
}
const qEl = document.getElementById('q'), resEl = document.getElementById('results');
let results = [], sel = -1;
function priceCell(i){
  if(i.t==='project'){ const q=i.q; return `<span class="price">${fmt(q.price_psf_min)}${q.price_psf_max!==q.price_psf_min?'–'+q.price_psf_max.toLocaleString('en-IN'):''}<small>/ sq ft · this project · 3 BHK ≈ ₹${cr(mid(q)*SIZES[3])} cr</small></span>`; }
  if(i.k && AGG[i.k]){ const a=AGG[i.k]; return `<span class="price">${fmtK(a.lo)}${a.hi!==a.lo?'–'+fmtK(a.hi):''}<small>/ sq ft · ${secName(i.k)} range · ${a.n} quote${a.n>1?'s':''}</small></span>`; }
  if(i.k) return `<span class="price none">no premium quote yet<small>resolves to ${secName(i.k)}</small></span>`;
  if(i.t==='road'){ const inf = D.roadInfo[i.road], meds = inf.secs.filter(s=>AGG[s]).map(s=>AGG[s].med); return meds.length?`<span class="price">${fmtK(Math.min(...meds))}${meds.length>1?'–'+fmtK(Math.max(...meds)):''}<small>/ sq ft · sector medians along it · ${inf.secs.length} sectors</small></span>`:`<span class="price none">road</span>`; }
  return `<span class="price none">${i.t==='landmark'||i.t==='station'?'landmark':'sector unknown'}</span>`;
}
function hl(n, q){ const i = norm(n).indexOf(norm(q)); if(i<0||!q) return esc(n); return esc(n.slice(0,i))+'<mark>'+esc(n.slice(i,i+q.trim().length))+'</mark>'+esc(n.slice(i+q.trim().length)); }
function renderResults(){
  if(!results.length){ resEl.innerHTML = qEl.value.trim() ? `<div class="empty">Nothing matched. Try part of the name (e.g. "Camellias") or a sector number.</div>` : ''; resEl.classList.toggle('on', !!qEl.value.trim()); qEl.setAttribute('aria-expanded', String(!!qEl.value.trim())); return; }
  resEl.innerHTML = results.map((i,n)=>{
    const where = i.t==='sector' ? 'Sector' : i.t==='project' ? `Priced project · ${secName(i.k)}${i.q.developer?' · '+esc(i.q.developer):''}` : i.t==='society' ? `${i.kind.replace('neighbourhood','Neighbourhood').replace('condominium','Condominium').replace('residential area','Residential area').replace('quarter','Locality')}${i.k?' · '+(i.h==='near'?'near ':'')+secName(i.k):' · sector not mapped'}` : i.t==='station' ? 'Metro station' : i.t==='road' ? 'Road · '+ROAD_CLASS[D.roadInfo[i.road].c] : 'Landmark';
    return `<button class="res${n===sel?' sel':''}" role="option" data-i="${n}"><b>${hl(i.n, qEl.value)}</b><span class="kind">${where}</span>${priceCell(i)}</button>`;
  }).join('');
  resEl.classList.add('on'); qEl.setAttribute('aria-expanded','true');
}
function choose(i){
  resEl.classList.remove('on'); qEl.setAttribute('aria-expanded','false');
  track('search_select', {query: qEl.value.trim().slice(0,100), result: i.n.slice(0,100), result_type: i.t, sector: i.k ? secName(i.k) : '(none)'});
  qEl.value = i.n;
  if(i.t==='sector'){ pin(i.k); const c = sectorCentre(i.k); if(c) flyTo(c.x,c.y,c.w); setMarker(null); return; }
  if(i.t==='road'){ pinRoad(i.road); const bb = D.roadInfo[i.road].bb; flyTo((bb[0]+bb[2])/2,(bb[1]+bb[3])/2, Math.max(bb[2]-bb[0], (bb[3]-bb[1])*1.4)*1.25); setMarker(null); return; }
  if(i.k) pin(i.k, i.t==='project' ? i.q.project : null);
  if(i.x!=null){ flyTo(i.x, i.y, BASEW/6); setMarker(i.x, i.y, i.n); }
  else if(i.k){ const c = sectorCentre(i.k); if(c) flyTo(c.x,c.y,c.w); setMarker(null); }
}
function setMarker(x,y,label){
  const g = G('g-marker'); g.innerHTML = '';
  if(x==null) return;
  g.appendChild(el('circle',{cx:x,cy:y,r:11})); g.appendChild(el('circle',{cx:x,cy:y,r:4,class:'dot'}));
  const t = el('text',{x:x+14,y:y-8}); t.textContent = label; g.appendChild(t);
}
let debounce;
qEl.addEventListener('input', ()=>{ clearTimeout(debounce); debounce = setTimeout(()=>{ results = search(qEl.value); sel = results.length?0:-1; renderResults(); }, 60); });
qEl.addEventListener('focus', ()=>{ if(results.length) renderResults(); });
qEl.addEventListener('keydown', ev=>{
  if(ev.key==='ArrowDown'){ ev.preventDefault(); sel = Math.min(results.length-1, sel+1); renderResults(); }
  else if(ev.key==='ArrowUp'){ ev.preventDefault(); sel = Math.max(0, sel-1); renderResults(); }
  else if(ev.key==='Enter'){ if(sel>=0 && results[sel]) choose(results[sel]); }
  else if(ev.key==='Escape'){ resEl.classList.remove('on'); qEl.setAttribute('aria-expanded','false'); }
});
resEl.addEventListener('mousedown', ev=>{ const b = ev.target.closest('.res'); if(b){ ev.preventDefault(); choose(results[+b.dataset.i]); } });
document.addEventListener('click', ev=>{ if(!ev.target.closest('.search')) resEl.classList.remove('on'); });

// ---- table -------------------------------------------------------------
let sortK = 'med', sortDir = -1;
function renderTable(){
  const tb = document.querySelector('#tbl tbody');
  const secs = Object.keys(AGG).filter(k=>inBand(bandIdx(AGG[k].med))).sort((a,b)=>{
    if(sortK==='sector') return (numOf(a)-numOf(b)||a.localeCompare(b))*sortDir;
    return (AGG[a].med-AGG[b].med)*sortDir;
  });
  let h = '';
  for(const k of secs){
    const a = AGG[k], b = bandOf(a.med);
    h += `<tr class="sec" tabindex="0" data-s="${k}"><td><span class="sw" style="background:var(${b.v})"></span>${secName(k)}<span class="cnt">${a.n} quote${a.n>1?'s':''}</span></td><td colspan="2">${D.sectors[k]?.boundary===false?'<span style="color:var(--muted);font-weight:400">location approximate</span>':''}</td><td class="num">${fmtK(a.lo)}${a.hi!==a.lo?' – '+fmtK(a.hi):''} <span style="color:var(--muted)">· med ${fmt(Math.round(a.med))}</span></td><td colspan="4" style="color:var(--muted);font-weight:400">${D.bench[k]&&D.bench[k].avg?`sector-wide portal avg ${fmt(D.bench[k].avg)}`:''}</td></tr>`;
    for(const q of a.rows){
      h += `<tr class="q"><td>${k}</td><td>${esc(q.project)}</td><td>${esc(q.developer||'')}</td><td class="num">${q.price_psf_min.toLocaleString('en-IN')}${q.price_psf_max!==q.price_psf_min?'–'+q.price_psf_max.toLocaleString('en-IN'):''}</td><td><span class="pill ${q.bucket}">${BUCKET_LABEL[q.bucket]}</span> ${confPill(q)}</td><td>${esc(q.basis||'')}</td><td>${esc(q.as_of||'')}</td><td><a href="${esc(q.source_url)}" target="_blank" rel="noopener" title="${esc(q.sot?q.sot.what:'')}">${esc(q.sot?q.sot.label:(q.source_type||'link'))}</a></td></tr>`;
    }
  }
  tb.innerHTML = h;
  for(const th of document.querySelectorAll('#tbl th[data-k]')){ th.removeAttribute('aria-sort'); if((th.dataset.k==='mid'&&sortK==='med')||th.dataset.k===sortK) th.setAttribute('aria-sort', sortDir>0?'ascending':'descending'); }
}
document.querySelector('#tbl thead').addEventListener('click', ev=>{
  const th = ev.target.closest('th[data-k]'); if(!th) return;
  const k = th.dataset.k==='mid'?'med':th.dataset.k;
  if(k!=='sector' && k!=='med') return;
  if(sortK===k) sortDir*=-1; else { sortK=k; sortDir = k==='sector'?1:-1; }
  renderTable();
});
document.querySelector('#tbl tbody').addEventListener('click', ev=>{ const tr = ev.target.closest('tr.sec'); if(tr){ pin(tr.dataset.s); const c = sectorCentre(tr.dataset.s); if(c) flyTo(c.x,c.y,c.w); window.scrollTo({top:0,behavior: reduceMotion?'auto':'smooth'}); } });
renderTable();
</script>
'''

out = PAGE.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')).replace('__GENERATED__', generated).replace('__SOURCE_NOTE__', SOURCE_NOTE)
open(f'{BASE}/gurgaon-price-map.html', 'w').write(out)
GA = '''<script async src="https://www.googletagmanager.com/gtag/js?id=G-BQT0Z05NDL"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-BQT0Z05NDL');</script>'''
open(f'{BASE}/gurgaon-price-map-standalone.html', 'w').write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + GA + '</head><body>' + out + '</body></html>')
print('quotes', len(quotes), 'sectors with data', n_sectors_with_data, '| roads', len(roads), 'metro segs', len(metro), 'stations', len(stations), 'societies', len(societies), 'entries', entries, '| bytes', len(out))
