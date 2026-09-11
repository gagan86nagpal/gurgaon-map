"""Merge unit-configuration tables (research configs_*.json) into the quote rows.

Adds to each matched row: configs [{bhk, area, price_cr}], configs_url, configs_as_of, source_psf (the source's own
current ₹/sq ft). When the row's source_url was only a sector/listing page and the project page was found, the
project page becomes the source_url (a more specific source of truth). Prints rows whose source psf has drifted
more than 15% from the stored range so they can be reviewed.
"""
import json, glob, re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ggn-research'

def normsec(s): return re.sub(r'^-', '', str(s or '').strip().upper().replace('SECTOR', '').replace(' ', ''))
def key(sector, project): return (normsec(sector), re.sub(r'\s+', ' ', str(project or '').strip().lower()))

# cumulative store committed with the data, so a research file being rewritten mid-run cannot drop rows
MERGED = f'{BASE}/configs_merged.json'
found = {}
if os.path.exists(MERGED):
    for c in json.load(open(MERGED)): found[key(c.get('sector'), c.get('project'))] = c
for f in sorted(glob.glob(f'{RESEARCH}/configs_*.json')):
    if re.search(r'configs_\d+_group', f): continue
    try: data = json.load(open(f))
    except Exception as e: print('!! skip', f, e); continue
    for c in data if isinstance(data, list) else []:
        k = key(c.get('sector'), c.get('project'))
        if k not in found or len(c.get('configs') or []) > len(found[k].get('configs') or []): found[k] = c

json.dump(sorted(found.values(), key=lambda c: (str(c.get('sector')), str(c.get('project')))), open(MERGED, 'w'), indent=1, ensure_ascii=False)

PROJECT_PAGE = re.compile(r'squareyards\.com/.*/\d+/project')
# sector corrections established from the project's own Square Yards page during the config round
SECTOR_FIX = {key('94', 'DLF Gardencity Enclave'): '93', key('87', 'DLF New Town Heights II'): '86',
              key('94', 'Orris Aanandam Ora'): '93', key('100', 'Conscient Heritage Max'): '102', key('72A', 'Birla Pravaah'): '71',
              key('87', 'DLF The Skycourt'): '86', key('SOHNA-36', 'Krisumi Waterfall Residences'): '36A'}
# duplicates of rows that already exist under the sector Square Yards places the project in
DROP = {key('100', 'Vatika Sovereign Park'), key('100', 'BPTP The Amaario'), key('87', 'Anant Raj Maceo')}
def r50(x): return int(round(x / 50.0) * 50)
matched = drift = withcfg = rebased = 0
for f in sorted(glob.glob(f'{BASE}/agent_*.json')):
    rows = json.load(open(f)); changed = False; kept = []
    for q in rows:
        k = key(q.get('sector'), q.get('project'))
        if k in DROP: changed = True; continue
        kept.append(q)
        if k in SECTOR_FIX and q['sector'] != SECTOR_FIX[k]:
            q['audit'] = {'verdict': 'reassign', 'reason': f"Square Yards project page places it in Sector {SECTOR_FIX[k]} (was {q['sector']})", 'checked': '2026-09'}
            q['sector'] = SECTOR_FIX[k]; changed = True
        c = found.get(k)
        if not c: continue
        matched += 1; changed = True
        cfgs = [x for x in (c.get('configs') or []) if isinstance(x, dict) and x.get('area') and x.get('price_cr')]
        for x in cfgs: x['bhk'] = str(x.get('bhk', '')); x['area'] = int(x['area']); x['price_cr'] = round(float(x['price_cr']), 2)
        q['configs'] = cfgs
        if cfgs: withcfg += 1
        if c.get('url') and PROJECT_PAGE.search(c['url']):
            q['configs_url'] = c['url']
            if not PROJECT_PAGE.search(q.get('source_url', '')) and 'squareyards.com' in q.get('source_url', ''):
                q['source_url'] = c['url']   # sector listing page -> the project's own page
        if c.get('as_of'): q['configs_as_of'] = c['as_of']
        if c.get('psf'):
            q['source_psf'] = int(c['psf'])
            lo, hi = int(q['price_psf_min']), int(q['price_psf_max'])
            if not (lo * 0.85 <= q['source_psf'] <= hi * 1.15):
                drift += 1; print(f"  drift [{q['sector']}] {q['project'][:40]}: stored {lo}-{hi}, source now {q['source_psf']} ({c.get('as_of','')})")
        if c.get('note'): q['configs_note'] = c['note']
        # Rows whose source of truth is the Square Yards project page take that page's current asking ₹/sq ft
        # verbatim. Unit-table prices are folded in only when they agree with it (±25%); older projects' tables
        # still carry launch-era list prices, which are flagged instead of being averaged into the range.
        if q.get('prev_psf'): q['price_psf_min'], q['price_psf_max'] = q['prev_psf']   # recompute from the original each run
        cfg_psf = [x['price_cr'] * 1e7 / x['area'] for x in cfgs if 200 <= x['area'] and 2000 <= x['price_cr'] * 1e7 / x['area'] <= 300000]
        sp = q.get('source_psf')
        if sp and cfg_psf:
            med = sorted(cfg_psf)[len(cfg_psf) // 2]
            q['configs_stale'] = not (0.75 * sp <= med <= 1.25 * sp)
        sy = 'squareyards.com' in q.get('source_url', '') and q.get('confidence') != 'A'
        if sy and sp:
            vals = [sp] + [v for v in cfg_psf if 0.75 * sp <= v <= 1.25 * sp]
            lo, hi = r50(min(vals)), r50(max(vals))
            if (lo, hi) != (q['price_psf_min'], q['price_psf_max']):
                q['prev_psf'] = [q['price_psf_min'], q['price_psf_max']]
                q['price_psf_min'], q['price_psf_max'] = lo, hi
                q['basis'] = f"Square Yards project page: current asking ₹{sp:,}/sq ft" + (f"; priced units ₹{lo:,}–{hi:,}/sq ft" if len(vals) > 1 else '') + ("; the page's unit table still shows launch-era list prices" if q.get('configs_stale') else '')
                q['as_of'] = c.get('as_of') or q.get('as_of'); rebased += 1
            else: q.pop('prev_psf', None)
    if changed: json.dump(kept, open(f, 'w'), indent=1, ensure_ascii=False)
print(f'configs: {len(found)} researched, {matched} rows matched, {withcfg} with a unit table, {drift} with >15% psf drift, {rebased} re-based to the source page')
