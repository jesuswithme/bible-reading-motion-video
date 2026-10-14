"""작업 폴더 준비: config.json 작성, 낭독 음성 16k 변환, 개역개정 본문·소제목·난외주 수집, 무음 구간 분석.

사용 예 (작업 폴더를 새로 만들 위치에서):
  python setup_work.py --work work10 --audio ../롬10장.m4a --book-ko 로마서 --book-en ROMANS --code rom --ch 10 --out ../10장
옵션: --unit 편 (시편), --version GAE (개역개정, 기본), --prompt "첫 구절 일부" (음성인식 힌트)
책 코드는 references/book_codes.md 참고 (요나서만 jnh).
"""
import argparse, os, re, json, html, subprocess, sys, urllib.request, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASSETS

ap = argparse.ArgumentParser()
ap.add_argument("--work", required=True); ap.add_argument("--audio", required=True)
ap.add_argument("--book-ko", required=True); ap.add_argument("--book-en", required=True)
ap.add_argument("--code", required=True); ap.add_argument("--ch", type=int, required=True)
ap.add_argument("--out", required=True); ap.add_argument("--unit", default="장")
ap.add_argument("--version", default="GAE"); ap.add_argument("--version-label", default="개역개정")
ap.add_argument("--prompt", default="")
a = ap.parse_args()

W = os.path.abspath(a.work)
for d in ["", "tts", "img", "imgs", "snaps", "final"]:
    os.makedirs(os.path.join(W, d), exist_ok=True)
os.makedirs(os.path.abspath(a.out), exist_ok=True)
audio = os.path.relpath(os.path.abspath(a.audio), W).replace("\\", "/")
out = os.path.relpath(os.path.abspath(a.out), W).replace("\\", "/") + "/"
os.chdir(W)

# 1) 본문 수집
url = f"https://www.bskorea.or.kr/bible/korbibReadpage.php?version={a.version}&book={a.code}&chap={a.ch}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
open("gae.html", "w", encoding="utf-8").write(raw)
s = raw[raw.find("tdBible1"):]
s = s[:s.find("성경 단어 검색")]
s = re.sub(r"<div id='D_[^>]*class=D2[^>]*>(.*?)</div>", lambda m: "[[N:" + re.sub(r"<[^>]+>", "", m.group(1)) + "]]", s, flags=re.S)
s = re.sub(r"<a class=comment.*?</a>", "", s, flags=re.S)
s = re.sub(r'<font class="smallTitle">(.*?)</font>', lambda m: "[[T:" + re.sub(r"<[^>]+>", "", m.group(1)) + "]]", s, flags=re.S)
parts = re.split(r'<span class="number">(\d+)(?:-(\d+))?&nbsp;&nbsp;&nbsp;</span>', s)
V, NOTES, TITLES, VL = {}, {}, {}, {}
for t in re.findall(r"\[\[T:(.*?)\]\]", parts[0]): TITLES["1"] = html.unescape(t).strip()
for i in range(1, len(parts), 3):
    k, k2, t = int(parts[i]), parts[i + 1], parts[i + 2]
    if k2: VL[str(k)] = f"{k}–{k2}"
    for h in re.findall(r"\[\[T:(.*?)\]\]", t): TITLES[str(k + 1)] = html.unescape(h).strip()
    t = re.sub(r"\[\[T:.*?\]\]", "", t)
    NOTES[str(k)] = [html.unescape(n).strip() for n in re.findall(r"\[\[N:(.*?)\]\]", t)]
    t = re.sub(r"\[\[N:.*?\]\]", "", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t)).replace("\xa0", " ")
    t = re.sub(r"[ㄱ-ㅎ]\)|\d\)", "", t)          # 난외주 표시 ㄱ) 1)
    t = re.sub(r"\s+", " ", t).strip()
    if not t: break
    V[str(k)] = t
json.dump(V, open("verses.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"titles": TITLES, "notes": NOTES, "vl": VL}, open("textinfo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 2) config
first = V[min(V, key=int)]
C = {"book_ko": a.book_ko, "book_en": a.book_en.upper(), "book_code": a.code, "ch": a.ch, "unit": a.unit,
     "version": a.version, "version_label": a.version_label, "audio": audio, "out_dir": out,
     "initial_prompt": a.prompt or f"{a.book_ko} {a.ch}{a.unit}. {first[:40]}",
     "narr_voice_id": "kKTntBsdDuheAZ0N6LTEVkDrAlQL7icT", "narr_speed": 0.92,
     "bgm_ratio": 0.58, "target_lufs": -16.0}
json.dump(C, open("config.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(os.path.join(ASSETS, "tpl.html"), "tpl.html")

# 3) 16k 모노 변환 + 무음 구간
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "f32le", "voice16k.f32"], check=True)
d = float(subprocess.check_output(["ffprobe", "-v", "0", "-show_entries", "format=duration", "-of", "csv=p=0", audio]))
log = subprocess.run(["ffmpeg", "-v", "info", "-i", audio, "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"], capture_output=True, text=True).stderr
sil = [(round(float(e) - float(du), 2), round(float(e), 2)) for e, du in re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", log)]
json.dump({"duration": d, "silences": sil}, open("silences.json", "w", encoding="utf-8"), indent=0)

# 4) 자막 줄 나눔 초안 (직접 고쳐서 manual_split.txt 로 저장)
def split(txt, lim=24):
    w = txt.split(" "); out_, cur = [], []
    for i, x in enumerate(w):
        cur.append(x); L = len(" ".join(cur)); rest = len(" ".join(w[i + 1:]))
        if rest == 0: break
        if (L >= 12 and re.search(r"(니|고|며|사|되|요|매|라|,)$", x) and rest >= 6) or L >= lim:
            out_.append(" ".join(cur)); cur = []
    if cur: out_.append(" ".join(cur))
    if len(out_) > 1 and len(out_[-1]) < 6:
        last = out_.pop(); out_[-1] += " " + last
    return out_
with open("manual_split_draft.txt", "w", encoding="utf-8") as f:
    for k in sorted(V, key=int): f.write(k + "|" + "|".join(split(V[k])) + "\n")

print(f"절 {len(V)}개, 길이 {d:.1f}초")
print("소제목:", TITLES); print("병합 절:", VL)
print("난외주:", {k: v for k, v in NOTES.items() if v})
print("무음:", "; ".join(f"{x}-{y}" for x, y in sil))
