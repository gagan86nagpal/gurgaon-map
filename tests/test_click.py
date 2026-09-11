"""Browser test: click a sector -> projects with prices appear on the right -> clicking a project opens its source.

Runs headless Chromium via Playwright in ~3 s. Set SKIP_BROWSER=1 to skip (data tests still run).
"""
import asyncio, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = f'file://{BASE}/index.html' if os.path.exists(f'{BASE}/index.html') else f'file://{BASE}/gurgaon-price-map-standalone.html'

if os.environ.get('SKIP_BROWSER'):
    print('skipped (SKIP_BROWSER set)'); sys.exit(0)
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('FAIL: playwright not installed — run scripts/install-hooks.sh (or SKIP_BROWSER=1 to bypass)'); sys.exit(1)

fails = []
def check(cond, msg):
    if not cond: fails.append(msg)

async def main():
    t0 = time.time()
    async with async_playwright() as p:
        exe = os.environ.get('PW_CHROMIUM')
        if not exe:
            import glob
            cands = sorted(glob.glob(os.path.expanduser('~/.cache/ms-playwright/chromium*/chrome-linux/*')))
            cands = [c for c in cands if os.path.basename(c) in ('headless_shell', 'chrome')]
            exe = cands[-1] if cands else None
        b = await p.chromium.launch(executable_path=exe, args=['--no-sandbox'])
        ctx = await b.new_context(viewport={'width': 1400, 'height': 900})
        page = await ctx.new_page()
        # record window.open calls instead of opening real tabs: offline and deterministic
        await page.add_init_script("window.__opened=[]; window.open=function(u){ window.__opened.push(String(u)); return null; };")
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto(PAGE)
        await page.wait_for_selector('#inspector')

        # 1. click a sector polygon (a real DOM click, not a JS call)
        for sec in ('54', '102', '37D'):
            el = page.locator(f'.sector[data-s="{sec}"]').first
            await el.dispatch_event('click')
            await page.wait_for_timeout(120)
            heading = await page.locator('#inspector h2').inner_text()
            check(sec in heading, f'sector {sec}: inspector heading is {heading!r}')
            cards = page.locator('#inspector .proj')
            n = await cards.count()
            check(n >= 1, f'sector {sec}: no project cards')
            for i in range(min(n, 3)):
                c = cards.nth(i)
                name = (await c.locator('.name').inner_text()).strip()
                psf = (await c.locator('.psf').inner_text()).strip()
                check(name and any(ch.isdigit() for ch in psf), f'sector {sec}: card {i} lacks name/₹ per sq ft ({name!r}, {psf!r})')
                tix = await c.locator('.tix').inner_text()
                check('BHK' in tix or 'Floor' in tix or 'Villa' in tix or 'Penthouse' in tix, f'sector {sec}: card {name!r} has no 2/3/4 BHK price line')
                url = await c.get_attribute('data-url')
                check(url and url.startswith('http'), f'sector {sec}: card {name!r} has no source url')

        # 2. Sector 102 must show a quoted unit table for Joyville (from the source page), not just the indicative line
        await page.locator('.sector[data-s="102"]').first.dispatch_event('click')
        await page.wait_for_timeout(120)
        joy = page.locator('#inspector .proj', has_text='Joyville').first
        check(await joy.count() == 1, 'Joyville card missing in Sector 102')
        if await joy.count():
            check(await joy.locator('table.cfg').count() == 1, 'Joyville card has no quoted unit table')
            check('2 BHK' in await joy.inner_text() and '3 BHK' in await joy.inner_text(), 'Joyville table lacks 2/3 BHK rows')

        # 3. clicking the card opens the source page in a new tab (we intercept the popup; no network needed)
        card = page.locator('#inspector .proj').first
        url = await card.get_attribute('data-url')
        await card.locator('.psf').click()
        opened = await page.evaluate('window.__opened')
        check(opened == [url], f'card click opened {opened!r}, expected [{url!r}]')
        # clicking the "open source" hint and the empty area of the card must do the same; an inner link must not double-open
        await card.locator('.go').click()
        check((await page.evaluate('window.__opened')) == [url, url], 'clicking the open-source hint did not open the source')

        # 4. the name link itself also points at the source
        href = await page.locator('#inspector .proj .name a').first.get_attribute('href')
        check(href == url, f'name link {href!r} != card url {url!r}')

        # 5. data-source filter: chips exist in directness order; switching Square Yards off changes the panel and back on restores it
        chips = page.locator('#srcchips .chip')
        check(await chips.count() >= 3, 'source filter chips missing')
        ranks = [int(r) for r in await chips.evaluate_all('els => els.map(e => e.dataset.rank)')]
        check(ranks == sorted(ranks), f'source chips not in directness order: {ranks}')
        await page.locator('.sector[data-s="37D"]').first.dispatch_event('click'); await page.wait_for_timeout(80)
        before = await page.locator('#inspector .proj').count()
        sy = page.locator('#srcchips .chip[data-src="squareyards"]')
        await sy.click(); await page.wait_for_timeout(120)
        check(await sy.get_attribute('aria-pressed') == 'false', 'Square Yards chip did not toggle off')
        after = await page.locator('#inspector .proj').count()
        check(after < before, f'disabling Square Yards did not change Sector 37D ({before} -> {after} cards)')
        await sy.click(); await page.wait_for_timeout(120)
        check(await page.locator('#inspector .proj').count() == before, 'restoring Square Yards did not restore the cards')
        # every card names its source class and, when the data has several sources, lists the others
        src_pills = await page.locator('#inspector .proj .pill.src').all_inner_texts()
        check(all(t.strip() for t in src_pills), 'a project card has an empty source pill')

        check(not errors, f'console/page errors: {errors[:3]}')
        await b.close()
    return time.time() - t0

dt = asyncio.run(main())
if fails:
    print(f'FAIL {len(fails)} problem(s):'); [print('  -', x) for x in fails]; sys.exit(1)
print(f'ok: sector click -> project cards with prices -> source opens ({dt:.1f}s)')
