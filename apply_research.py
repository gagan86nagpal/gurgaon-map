"""Fold the research agents' outputs into the data files.

Inputs (in RESEARCH dir): audit.json, gapfill.json, bench_a.json, bench_b.json
Outputs (in BASE): edits to agent_*.json rows named in audit.json, agent_gapfill.json, benchmarks.json, nostock.json
"""
import json, glob, re, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ggn-research'

def load(name):
    p = f'{RESEARCH}/{name}'
    if not os.path.exists(p): return []
    try:
        d = json.load(open(p))
        return d if isinstance(d, list) else []
    except Exception as e:
        print('!! could not parse', name, e); return []

def normsec(s):
    return re.sub(r'^-', '', str(s or '').strip().upper().replace('SECTOR', '').replace(' ', ''))
def key(sector, project):
    return (normsec(sector), re.sub(r'\s+', ' ', str(project or '').strip().lower()))

# ---- audit verdicts --------------------------------------------------------
audit = load('audit.json')
verdicts = {key(a['sector'], a['project']): a for a in audit}
counts = {}
touched = 0
for f in sorted(glob.glob(f'{BASE}/agent_*.json')):
    if f.endswith('agent_gapfill.json'): continue
    rows = json.load(open(f)); out = []; changed = False
    for q in rows:
        a = verdicts.pop(key(q.get('sector'), q.get('project')), None)
        if not a:
            out.append(q); continue
        v = a.get('verdict', 'unverified'); counts[v] = counts.get(v, 0) + 1; changed = True; touched += 1
        if v == 'drop':
            continue
        if v in ('keep', 'adjust', 'reassign'):
            if a.get('new_min') and a.get('new_max'):
                q['price_psf_min'], q['price_psf_max'] = int(a['new_min']), int(a['new_max'])
            for src, dst in (('new_basis', 'basis'), ('new_status', 'status'), ('new_source_url', 'source_url'), ('new_source_type', 'source_type'), ('as_of', 'as_of')):
                if a.get(src): q[dst] = a[src]
            if v == 'reassign' and a.get('new_sector'): q['sector'] = normsec(a['new_sector'])
            q['confidence'] = a.get('confidence') or ('B' if v == 'keep' else 'C')
            if a.get('second_source_url'): q['second_source_url'] = a['second_source_url']
            q['audit'] = {'verdict': v, 'reason': a.get('reason', ''), 'checked': '2026-09'}
        else:  # unverified: keep but mark
            q['confidence'] = 'C'; q['audit'] = {'verdict': 'unverified', 'reason': a.get('reason', ''), 'checked': '2026-09'}
        out.append(q)
    if changed:
        json.dump(out, open(f, 'w'), indent=1, ensure_ascii=False)
print('audit verdicts applied:', counts, '| rows touched', touched, '| unmatched verdicts', len(verdicts))
for k in list(verdicts)[:10]: print('   unmatched:', k)

# ---- refresh round (verdicts on stale rows + new rows) ----------------------
refresh = load('refresh.json')
rverd = {key(r['sector'], r['project']): r for r in refresh if r.get('kind') == 'verdict'}
rcounts = {}
def apply_refresh(q, a):
    """Apply one refresh verdict to a row in place; returns False when the row should be dropped."""
    v = a.get('verdict', 'keep'); rcounts[v] = rcounts.get(v, 0) + 1
    if v == 'drop': return False
    if v == 'adjust' and a.get('new_min') and a.get('new_max'):
        q['price_psf_min'], q['price_psf_max'] = int(a['new_min']), int(a['new_max'])
    for src, dst in (('new_basis', 'basis'), ('new_status', 'status'), ('new_source_url', 'source_url'), ('new_source_type', 'source_type'), ('as_of', 'as_of')):
        if a.get(src): q[dst] = a[src]
    if a.get('confidence'): q['confidence'] = a['confidence']
    if a.get('second_source_url'): q['second_source_url'] = a['second_source_url']
    q['audit'] = {'verdict': v, 'reason': a.get('reason', ''), 'checked': '2026-09'}
    return True
for f in sorted(glob.glob(f'{BASE}/agent_*.json')):
    if f.endswith(('agent_gapfill.json', 'agent_gapfill2.json', 'agent_refresh.json')): continue
    rows = json.load(open(f)); out = []; changed = False
    for q in rows:
        a = rverd.pop(key(q.get('sector'), q.get('project')), None)
        if not a: out.append(q); continue
        changed = True
        if apply_refresh(q, a): out.append(q)
    if changed: json.dump(out, open(f, 'w'), indent=1, ensure_ascii=False)

def clean_quotes(rows, tag):
    quotes, nostock = [], {}
    for g in rows:
        s = normsec(g.get('sector'))
        if g.get('no_premium_stock'):
            nostock[s] = {'reason': g.get('reason', ''), 'source_url': g.get('source_url', '')}; continue
        try: lo, hi = int(g['price_psf_min']), int(g['price_psf_max'])
        except Exception: continue
        if lo <= 0 or hi < lo: continue
        if g.get('area_basis') == 'carpet': g['basis'] = 'CARPET-AREA rate (not directly comparable): ' + str(g.get('basis', ''))
        g['sector'] = s; g.setdefault('confidence', 'B'); g.setdefault('as_of', '2026-09'); g.pop('kind', None)
        quotes.append(g)
    json.dump(quotes, open(f'{BASE}/agent_{tag}.json', 'w'), indent=1, ensure_ascii=False)
    print(tag, 'quotes', len(quotes), 'sectors', len({q["sector"] for q in quotes}), '| no-stock', sorted(nostock))
    return nostock
nostock = {}
nostock.update(clean_quotes([r for r in refresh if r.get('kind') == 'new'], 'refresh'))
nostock.update(clean_quotes(load('gapfill2.json'), 'gapfill2'))

# ---- gap fill --------------------------------------------------------------
gap = load('gapfill.json')
quotes = []
for g in gap:
    s = normsec(g.get('sector'))
    if g.get('no_premium_stock'):
        nostock[s] = {'reason': g.get('reason', ''), 'source_url': g.get('source_url', '')}; continue
    try:
        lo, hi = int(g['price_psf_min']), int(g['price_psf_max'])
    except Exception:
        continue
    if lo <= 0 or hi < lo: continue
    if g.get('area_basis') == 'carpet':
        g['basis'] = 'CARPET-AREA rate (not directly comparable): ' + str(g.get('basis', ''))
    g['sector'] = s; g.setdefault('confidence', 'B'); g.setdefault('as_of', '2026-09')
    a = rverd.pop(key(s, g.get('project')), None)
    if a and not apply_refresh(g, a): continue
    quotes.append(g)
json.dump(quotes, open(f'{BASE}/agent_gapfill.json', 'w'), indent=1, ensure_ascii=False)
print('refresh verdicts applied:', rcounts, '| unmatched', len(rverd), list(rverd)[:6])
json.dump(nostock, open(f'{BASE}/nostock.json', 'w'), indent=1, ensure_ascii=False)
print('gapfill quotes', len(quotes), 'sectors', len({q["sector"] for q in quotes}), '| no-premium-stock sectors', sorted(nostock))

# ---- benchmarks ------------------------------------------------------------
bench = {}
for b in load('bench_a.json') + load('bench_b.json'):
    s = normsec(b.get('sector'))
    e = bench.setdefault(s, {'portals': [], 'flag': '', 'no_market': False})
    if b.get('no_apartment_market'):
        e['no_market'] = True; e['note'] = b.get('note', '')
    portal = (b.get('portal') or '').lower()
    if not any(w in portal for w in ('99acres', 'magicbricks', 'squareyards', 'square yards', 'housing', 'nobroker')):
        continue  # unattributed syntheses and one-off aggregators are not a benchmark
    try:
        avg = int(b['avg_psf']) if b.get('avg_psf') else (int((float(b['range_min']) + float(b['range_max'])) / 2) if b.get('range_min') and b.get('range_max') else None)
    except Exception:
        avg = None
    if avg and 2000 <= avg <= 150000:
        e['portals'].append({'portal': b.get('portal', ''), 'avg': avg, 'min': b.get('range_min'), 'max': b.get('range_max'), 'as_of': b.get('as_of', ''), 'url': b.get('url', '')})
    if b.get('flag') and not e['flag']: e['flag'] = b['flag']
for s, e in bench.items():
    # de-duplicate portals, keep the first figure per portal
    seen = set(); ps = []
    for p in e['portals']:
        if p['portal'].lower() in seen: continue
        seen.add(p['portal'].lower()); ps.append(p)
    # portals can disagree 2-3x on one sector (all-inclusive averages vs new-launch listings); use a robust centre
    e['disputed'] = False
    if len(ps) >= 3:
        vals = sorted(p['avg'] for p in ps); med = vals[len(vals) // 2]
        kept = [p for p in ps if 0.55 <= p['avg'] / med <= 1.8]
        e['disputed'] = len(kept) < len(ps); ps = kept
    e['portals'] = ps
    if len(ps) == 2 and max(p['avg'] for p in ps) > 1.6 * min(p['avg'] for p in ps):
        e['disputed'] = True; e['avg'] = None   # two portals, 1.6x apart: no honest single figure
    else:
        e['avg'] = round(sum(p['avg'] for p in ps) / len(ps)) if ps else None
json.dump(bench, open(f'{BASE}/benchmarks.json', 'w'), indent=1, ensure_ascii=False)
print('benchmarks: sectors', len(bench), 'with a figure', sum(1 for e in bench.values() if e['avg']), 'flags', sum(1 for e in bench.values() if e['flag']))
