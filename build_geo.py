import json, math, re, os, sys
BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

GEOM = json.load(open(f'{BASE}/osm/sectors_geom.json'))['elements']
NODES = json.load(open(f'{BASE}/osm/nodes.json'))['elements']

# Gurgaon envelope (excludes Dwarka to the north, RK Puram to the east, Manesar town to the south-west)
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 28.36, 28.545, 76.90, 77.13

def norm(name):
    m = re.match(r'^Sector[ -]?(\d+)\s?-?([A-D]|I{1,2})?$', name.strip(), re.I)
    if not m:
        return None
    num, suf = m.group(1), (m.group(2) or '').upper()
    return f"{int(num)}{suf}"

def rings_of(e):
    """Return list of outer rings as [(lon,lat),...]."""
    if e['type'] == 'way':
        pts = [(p['lon'], p['lat']) for p in e.get('geometry', [])]
        return [pts] if len(pts) >= 4 else []
    segs = []
    for m in e.get('members', []):
        if m['type'] == 'way' and m.get('role') in ('outer', ''):
            pts = [(p['lon'], p['lat']) for p in m.get('geometry', [])]
            if len(pts) >= 2:
                segs.append(pts)
    # stitch segments into closed rings
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]; segs.pop(i); changed = True; break
                if s[-1] == ring[-1]:
                    ring += s[-2::-1]; segs.pop(i); changed = True; break
                if s[-1] == ring[0]:
                    ring = s[:-1] + ring; segs.pop(i); changed = True; break
                if s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring; segs.pop(i); changed = True; break
        if len(ring) >= 4:
            rings.append(ring)
    return rings

def centroid(rings):
    pts = [p for r in rings for p in r]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

def area(ring):
    a = 0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(a) / 2

def simplify(ring, tol):
    # Douglas-Peucker
    if len(ring) < 5:
        return ring
    def dp(pts):
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
            return dp(pts[:idx + 1])[:-1] + dp(pts[idx:])
        return [pts[0], pts[-1]]
    # closed ring: split at the vertex farthest from the start so neither half is degenerate
    x0, y0 = ring[0]
    far = max(range(1, len(ring) - 1), key=lambda i: math.hypot(ring[i][0] - x0, ring[i][1] - y0))
    return dp(ring[:far + 1])[:-1] + dp(ring[far:])

cands = {}
for e in GEOM:
    key = norm(e['tags'].get('name', ''))
    if not key:
        continue
    rings = rings_of(e)
    if not rings:
        continue
    cx, cy = centroid(rings)
    if not (LAT_MIN <= cy <= LAT_MAX and LON_MIN <= cx <= LON_MAX):
        continue
    # Manesar town sectors share numbers 1-15 but sit south-west
    num = int(re.match(r'\d+', key).group())
    if num <= 15 and cx < 76.96:
        continue
    score = (1 if e['type'] == 'relation' else 0, 1 if e['tags'].get('admin_level') == '9' else 0)
    if key not in cands or score > cands[key][0]:
        cands[key] = (score, rings, (cx, cy))

# projection: equirectangular with cos(lat) correction -> SVG coords
LAT_TOP, LON_LEFT = 28.615, 76.88
KX = math.cos(math.radians(28.45))
def proj(lon, lat):
    return ((lon - LON_LEFT) * KX * 4000, (LAT_TOP - lat) * 4000)

sectors = {}
for key, (score, rings, (cx, cy)) in cands.items():
    outs = []
    for r in rings:
        pr = [proj(*p) for p in r]
        pr = simplify(pr, 1.2)
        if len(pr) >= 4:
            outs.append([[round(x, 1), round(y, 1)] for x, y in pr])
    if not outs:
        continue
    px, py = proj(cx, cy)
    sectors[key] = {"name": key, "rings": outs, "cx": round(px, 1), "cy": round(py, 1), "boundary": True}

# sectors that exist only as place nodes
for n in NODES:
    key = norm(n['tags'].get('name', ''))
    if not key or key in sectors:
        continue
    lat, lon = n['lat'], n['lon']
    if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
        continue
    num = int(re.match(r'\d+', key).group())
    if num <= 15 and lon < 76.96:
        continue
    px, py = proj(lon, lat)
    sectors[key] = {"name": key, "rings": [], "cx": round(px, 1), "cy": round(py, 1), "boundary": False}

xs = [x for s in sectors.values() for r in s['rings'] for x, y in r] + [s['cx'] for s in sectors.values()]
ys = [y for s in sectors.values() for r in s['rings'] for x, y in r] + [s['cy'] for s in sectors.values()]
bbox = [math.floor(min(xs)) - 20, math.floor(min(ys)) - 20, math.ceil(max(xs) - min(xs)) + 40, math.ceil(max(ys) - min(ys)) + 40]

json.dump({"bbox": bbox, "sectors": sectors}, open(f'{BASE}/sectors.json', 'w'))
print(len(sectors), "sectors;", sum(1 for s in sectors.values() if s['boundary']), "with boundary;", bbox)
print("point-only:", sorted([k for k, s in sectors.items() if not s['boundary']], key=lambda k: (int(re.match(r'\d+', k).group()), k)))
