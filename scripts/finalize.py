"""마무리: part0~3 합치기 + mix.m4a 결합 → {out_dir}/bible_motion_graphics.mp4, 전체 디코딩 검증, 12프레임 격자(final_grid.jpg), project/ 복사.
사용: python finalize.py [격자용 시각 12개…]   (생략하면 균등 간격)
일부 구간만 다시 렌더할 때: python render.py A 끝프레임 fix.mp4 → python finalize.py --splice A
"""
import subprocess, json, sys, os, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg
from PIL import Image

C = cfg(); OUT = os.path.join(C["out_dir"], "bible_motion_graphics.mp4")
args = sys.argv[1:]
open("list.txt", "w").write("".join(f"file part{i}.mp4\n" for i in range(4)))
if args[:1] == ["--splice"]:
    A = int(args[1]); args = args[2:]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "full_old.mp4"], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "full_old.mp4", "-i", "fix.mp4", "-filter_complex",
                    f"[0:v]trim=end_frame={A},setpts=PTS-STARTPTS[a];[a][1:v]concat=n=2:v=1[v]", "-map", "[v]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "video.mp4"], check=True)
    os.remove("full_old.mp4")
else:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "video.mp4"], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "video.mp4", "-i", "mix.m4a", "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest", "-movflags", "+faststart", OUT], check=True)
os.remove("video.mp4")
info = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,r_frame_rate", "-of", "default=nw=1", OUT]).decode()
print(info.replace("\n", " "))
r = subprocess.run(["ffmpeg", "-v", "error", "-i", OUT, "-f", "null", "-"], capture_output=True, text=True)
print("DECODE_OK" if not r.stderr.strip() else "DECODE_ERROR:\n" + r.stderr[:2000])
D = float([l for l in info.split("\n") if l.startswith("duration=")][0].split("=")[1])
ts = [float(x) for x in args] or [round(3 + i * (D - 6) / 11, 1) for i in range(12)]
os.makedirs("final", exist_ok=True); g = Image.new("RGB", (1920, 360 * ((len(ts) + 2) // 3)))
for i, t in enumerate(ts):
    fn = f"final/f{i:02d}.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", OUT, "-frames:v", "1", "-vf", "scale=640:360", fn], check=True)
    g.paste(Image.open(fn), ((i % 3) * 640, (i // 3) * 360))
g.save("final_grid.jpg", quality=85); print("final_grid.jpg 저장 (Read 로 확인)")
P = os.path.join(C["out_dir"], "project"); os.makedirs(P + "/imgs", exist_ok=True); os.makedirs(P + "/tts", exist_ok=True)
for f in ["config.json", "chapter.json", "chapter_tl.py", "narr.json", "manual_split.txt", "verses.json", "textinfo.json", "charmap.json",
          "subs_reader.json", "tl.json", "bgm_cues.json", "tpl.html", "docs.json"] + glob.glob("bgm*.mp3"):
    if os.path.exists(f): shutil.copy(f, P)
for f in glob.glob("imgs/*.jpg"): shutil.copy(f, P + "/imgs")
for f in glob.glob("tts/N[0-9]*.mp3"): shutil.copy(f, P + "/tts")
open(os.path.join(P, "README.md"), "w", encoding="utf-8").write(
    "# 편집용 프로젝트\n\n이 폴더를 작업 폴더로 삼아 스킬 `bible-reading-motion-video` 의 scripts 를 실행하면 다시 만들 수 있습니다.\n\n"
    "1. config.json 의 audio 경로를 원본 낭독 파일 위치로 고칩니다.\n"
    "2. `python {스킬}/scripts/build_tl.py` → `python {스킬}/scripts/render.py all` → `python {스킬}/scripts/mix.py` → `python {스킬}/scripts/finalize.py`\n\n"
    "- 장면·자막 연출: chapter_tl.py / 단락·분할점: chapter.json / 해설 원고: narr.json / 자막 줄 나눔: manual_split.txt\n"
    "- BGM: bgm_cues.json (영상 시각, 곡, 원곡 위치, 설명)\n")
print("project →", P)
