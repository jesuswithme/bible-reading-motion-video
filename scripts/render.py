"""프레임 렌더: index.html 의 setTime(t)를 프레임마다 캡처해 MP4로.
- 한 구간:   python render.py 0 2850 part0.mp4
- 4분할 병렬: python render.py all      (part0~3.mp4, r0~3.log 생성, 백그라운드로 띄우고 바로 끝남)
진행 확인:   tail -qn1 r*.log   (DONE 4개면 완료)  — pgrep/pkill 금지(다른 사람의 render.py 를 죽일 수 있음)
"""
import sys, asyncio, subprocess, time, base64, os, json, math
FPS = 30

if sys.argv[1] == "all":
    END = json.load(open("tl.json", encoding="utf-8"))["END"]; Nf = math.ceil(END * FPS); Q = (Nf + 3) // 4
    for i in range(4):
        a, b = i * Q, min(Nf, (i + 1) * Q)
        subprocess.Popen([sys.executable, os.path.abspath(__file__), str(a), str(b), f"part{i}.mp4"],
                         stdout=open(f"r{i}.log", "w"), stderr=subprocess.STDOUT,
                         creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    open("list.txt", "w").write("".join(f"file part{i}.mp4\n" for i in range(4)))
    print("started", Nf, "frames")
    sys.exit()

from playwright.async_api import async_playwright
async def main(i0, i1, out):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        await pg.goto("file:///" + os.path.abspath("index.html").replace("\\", "/")); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(1500)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)
        cdp = await pg.context.new_cdp_session(pg); t0 = time.time()
        for f in range(i0, i1):
            await pg.evaluate(f"setTime({f/FPS})")
            r = await cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 93})
            ff.stdin.write(base64.b64decode(r["data"]))
            if f % 300 == 0: print(out, f, round(time.time() - t0, 1), flush=True)
        ff.stdin.close(); ff.wait(); await b.close()
    print("DONE", out, round(time.time() - t0, 1), flush=True)
asyncio.run(main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]))
