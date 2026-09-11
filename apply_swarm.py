"""Merge the direct-source swarm outputs (research swarm_out_*.json) into the data files.

Writes agent_direct.json (press / developer / project-site quotes, one per project per source class) and
sector_news.json (sector- or corridor-level press figures shown in the inspector's independent-check block).
"""
import json, glob, re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ggn-research'

def normsec(s): return re.sub(r'^-', '', str(s or '').strip().upper().replace('SECTOR', '').replace(' ', ''))
OK_TYPES = {'news', 'developer', 'project-site'}
GOOGLE = re.compile(r'news\.google\.com')

quotes, news, tried = {}, {}, []
for f in sorted(glob.glob(f'{RESEARCH}/swarm_out_*.json')):
    try: d = json.load(open(f))
    except Exception as e: print('!! skip', f, e); continue
    for q in d.get('quotes') or []:
        try: lo, hi = int(q['price_psf_min']), int(q['price_psf_max'])
        except Exception: continue
        st = (q.get('source_type') or '').lower()
        url = q.get('source_url') or ''
        if st not in OK_TYPES or not url.startswith('http') or GOOGLE.search(url): continue
        if not (2000 <= lo <= hi <= 300000): continue
        if not re.match(r'20(25|26)', str(q.get('as_of', ''))): continue      # only current material colours the map
        s = normsec(q.get('sector'))
        cls = 'developer' if st in ('developer', 'project-site') else 'news'
        k = (s, str(q.get('project', '')).strip().lower(), cls)
        if k in quotes: continue
        cfgs = []
        for c in q.get('configs') or []:
            try:
                a, p = int(c['area']), round(float(c['price_cr']), 2)
                if a >= 200 and p > 0 and 2000 <= p * 1e7 / a <= 300000: cfgs.append({'bhk': str(c.get('bhk', '')), 'area': a, 'price_cr': p})
            except Exception: pass
        row = {'sector': s, 'project': q['project'], 'developer': q.get('developer', ''), 'price_psf_min': lo, 'price_psf_max': hi,
               'basis': q.get('basis', ''), 'status': q.get('status', ''), 'source_url': url, 'source_type': st,
               'publisher': q.get('publisher', ''), 'as_of': q['as_of'], 'snippet': (q.get('snippet') or '')[:220],
               'confidence': 'B', 'audit': {'verdict': 'direct', 'reason': f"{st}: {q.get('publisher', '')} — \"{(q.get('snippet') or '')[:160]}\"", 'checked': '2026-09'}}
        if cfgs: row['configs'] = cfgs; row['configs_as_of'] = q['as_of']
        quotes[k] = row
    for n in d.get('sector_news') or []:
        url = n.get('url') or ''
        if not url.startswith('http') or GOOGLE.search(url) or not re.match(r'20(25|26)', str(n.get('as_of', ''))): continue
        for s in re.split(r'[,/&]| and ', str(n.get('sector', ''))):
            s = normsec(s)
            if not s: continue
            lst = news.setdefault(s, [])
            if any(x['url'] == url for x in lst): continue
            lst.append({'headline': n.get('headline', ''), 'publisher': n.get('publisher', ''), 'as_of': n['as_of'], 'url': url, 'figure': n.get('figure', ''), 'psf': n.get('psf')})
    tried += d.get('no_direct_source') or []

json.dump(list(quotes.values()), open(f'{BASE}/agent_direct.json', 'w'), indent=1, ensure_ascii=False)
json.dump(news, open(f'{BASE}/sector_news.json', 'w'), indent=1, ensure_ascii=False)
by = {}
for q in quotes.values(): by[q['source_type']] = by.get(q['source_type'], 0) + 1
print(f'direct quotes {len(quotes)} {by} over {len({k[0] for k in quotes})} sectors | sector news for {len(news)} sectors | no-direct-source notes {len(tried)}')
