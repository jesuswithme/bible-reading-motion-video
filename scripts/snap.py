"""특정 시각 화면 캡처 → 2열 격자 이미지. 렌더 전 점검용.
사용: python snap.py g1.jpg 4 25 40 60 72 84     (그 뒤 Read 로 g1.jpg 확인)"""
import sys, asyncio, os
from playwright.async_api import async_playwright
from PIL import Image
async def main():
    os.makedirs("snaps", exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("file:///" + os.path.abspath("index.html").replace("\\", "/")); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(1500)
        fs = []
        for t in sys.argv[2:]:
            await pg.evaluate(f"setTime({t})"); fn = f"snaps/s_{t}.jpg"; await pg.screenshot(path=fn, type="jpeg", quality=80); fs.append(fn)
        print("errors:", errs[:5], "TOTAL:", await pg.evaluate("TOTAL"))
        await b.close()
    W, H = 960, 540; g = Image.new("RGB", (W * 2, H * ((len(fs) + 1) // 2)))
    for i, f in enumerate(fs): g.paste(Image.open(f).resize((W, H)), ((i % 2) * W, (i // 2) * H))
    g.save(sys.argv[1], quality=85)
asyncio.run(main())
