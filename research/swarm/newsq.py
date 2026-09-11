#!/usr/bin/env python3
"""Bing News RSS query -> real publisher URLs. Usage: newsq.py "query words" [max]
Prints one line per item: date | source | title | url  (newest first, 2025-26 only)."""
import sys, re, html, urllib.request, urllib.parse, xml.etree.ElementTree as ET
q = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
u = 'https://www.bing.com/news/search?q=' + urllib.parse.quote(q) + '&format=RSS'
req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=20).read()
root = ET.fromstring(data)
out = []
for it in root.iter('item'):
    t = html.unescape(it.findtext('title') or ''); link = it.findtext('link') or ''; d = it.findtext('pubDate') or ''
    src = it.findtext('{http://www.bing.com/news/rss}Source') or html.unescape(it.findtext('source') or '') or ''
    m = re.search(r'[?&]url=([^&]+)', link); real = urllib.parse.unquote(m.group(1)) if m else link
    yr = re.search(r'20\d\d', d); yr = yr.group(0) if yr else ''
    if yr and yr not in ('2025', '2026'): continue
    out.append((d[:16], src or urllib.parse.urlparse(real).netloc, t, real))
for d, s, t, r in out[:n]: print(f'{d} | {s} | {t} | {r}')
if not out: print('NO 2025-26 ITEMS')
