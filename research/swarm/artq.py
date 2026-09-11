#!/usr/bin/env python3
"""Fetch an article and print only what matters: title, date, and sentences that contain a price figure.
Usage: artq.py URL [extra-keyword]  — prints BLOCKED <code> if the site refuses."""
import sys, re, html, urllib.request
u = sys.argv[1]; kw = sys.argv[2].lower() if len(sys.argv) > 2 else None
req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36', 'Accept-Language': 'en-IN,en;q=0.9'})
try:
    raw = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
except Exception as e:
    print('BLOCKED', getattr(e, 'code', e)); sys.exit(0)
title = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I); title = html.unescape(re.sub(r'\s+', ' ', title.group(1))).strip() if title else ''
date = re.search(r'(datePublished|article:published_time|publishdate|pubdate)["\']?\s*[:=]\s*["\']([^"\']+)', raw, re.I)
print('TITLE:', title[:160]); print('DATE:', date.group(2)[:25] if date else '?'); print('URL:', u)
txt = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', raw, flags=re.S | re.I)
txt = html.unescape(re.sub(r'<[^>]+>', ' ', txt)); txt = re.sub(r'\s+', ' ', txt)
sents = re.split(r'(?<=[.!?])\s+(?=[A-Z₹])', txt)
pat = re.compile(r'(₹|\bRs\.?|INR)\s?[\d,.]+\s*(crore|cr\b|lakh|per sq|/sq|psf)|per\s*sq\.?\s*ft|sq\.?\s*ft|square feet|price', re.I)
seen = set(); n = 0
for s_ in sents:
    s_ = s_.strip()
    if len(s_) < 30 or len(s_) > 600 or s_ in seen: continue
    if pat.search(s_) and (not kw or kw in s_.lower()):
        seen.add(s_); print('-', s_); n += 1
        if n >= 25: break
if not n: print('(no price sentences found)')
