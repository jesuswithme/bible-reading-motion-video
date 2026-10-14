"""문서 4종 생성: bible_subtitles.srt / bible_transcript.txt / bible_narration_script.md / bible_storyboard.md
장마다 다른 내용은 작업 폴더의 docs.json 에 쓴다 (형식은 references/docs_json_example.json).
시각 표기: 숫자(영상 초) 또는 "N0"/"R2"(구간 시작), "N0.e"(구간 끝), "v12"(12절 첫 자막), "END".
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, jload, heading, mmss, dur

C = cfg(); CJ = jload("chapter.json"); DJ = jload("docs.json")
D = jload("tl.json"); S = {s["id"]: s for s in D["segs"]}; END = D["END"]
OUT = C["out_dir"]; CH = C["ch"]; BK = C["book_ko"]; HD = heading(C); VER = C.get("version_label", "개역개정")
def T(x):
    if isinstance(x, (int, float)): return float(x)
    if x == "END": return END
    if x.startswith("v"): return D["vstart"][x[1:]]
    if x.endswith(".e"): return S[x[:-2]]["e"]
    return S[x]["t"]
def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ---- SRT
subs = sorted(D["subs"], key=lambda s: s["t"]); out = []
for i, s in enumerate(subs):
    t1 = s["e"] + 0.25
    if i + 1 < len(subs): t1 = min(t1, subs[i + 1]["t"] - 0.04)
    txt = ("[해설] " + s["text"].replace("\n", " ")) if s["kind"] == "nar" else s["text"]
    out.append(f"{i+1}\n{ts(s['t'])} --> {ts(t1)}\n{txt}\n")
open(OUT + "bible_subtitles.srt", "w", encoding="utf-8-sig").write("\n".join(out)); print(len(out), "cues")

# ---- transcript
V = {int(k): v for k, v in jload("verses.json").items()}; INFO = jload("textinfo.json")
A = jload("asr.json"); W = [w for s in A for w in s["words"]]
M = jload("charmap.json"); own, ot = M["own"], M["ot"]
def r2f(x):
    for s in D["segs"]:
        if s["kind"] == "read" and s["src"][0] <= x <= s["src"][1] + 0.01: return s["t"] + x - s["src"][0]
    return 0
def span(u):
    idx = [i for i, x in enumerate(own) if x == u]; return ot[idx[0]][0], ot[idx[-1]][1]
NOTE = DJ.get("transcript_notes", {})
L = [f"{HD} 낭독 받아쓰기 및 본문 대조", "=" * 40,
     f"원본 파일 : {os.path.basename(C['audio'])} ({dur(C['audio']):.2f}초)",
     f"대조 본문 : {VER} (대한성서공회 bskorea.or.kr 본문과 대조)",
     "음성 인식 : faster-whisper large-v3-turbo (CPU int8) + 확인용 Systran small", "", "[판정 요약]",
     f"- 낭독은 {VER} {BK} {CH}:1–{max(V)}을 처음부터 끝까지 읽은 것으로 판단됩니다."]
L += ["- " + x for x in DJ.get("transcript_summary", [])]
L += ["", "[시각 표기] 원본 = 원본 음성 기준, 영상 = 완성 영상 기준(해설 삽입 후)", ""]
t0, t1 = span("title"); L += [f"[머리말] 원본 {mmss(t0)}–{mmss(t1)} / 영상 {mmss(r2f(t0))}", f"  낭독: {HD}", ""]
for k in sorted(V):
    a, b = span(str(k)); asr = "".join(w["w"] for w in W if a - 0.05 <= w["s"] < b - 0.05).strip()
    same = re.sub(r"[^가-힣]", "", asr) == re.sub(r"[^가-힣]", "", V[k])
    lab = INFO.get("vl", {}).get(str(k), str(k))
    L += [f"[{lab}절] 원본 {mmss(a)}–{mmss(b)} / 영상 {mmss(r2f(a))}–{mmss(r2f(b))}", f"  본문({VER}): {V[k]}", f"  음성인식 원문 : {asr}",
          "  판정          : " + NOTE.get(str(k), "본문과 일치" if same else "본문과 일치(차이는 음성인식 오류로 판단)"), ""]
a, b = span("amen"); L += [f"[맺음말] 원본 {mmss(a)}–{mmss(b)} / 영상 {mmss(r2f(a))}", "  낭독: 아멘 (본문 외, 낭독자가 덧붙인 말)", ""]
notes = {k: v for k, v in INFO.get("notes", {}).items() if v}
if notes: L += ["[개역개정 난외주] " + " / ".join(f"{k}절: {'; '.join(v)}" for k, v in notes.items()), ""]
L += ["[단락 전환과 낭독 분할점(무음 구간 중앙)]"]
L += [f"  원본 {mmss(c)}" for c in CJ["cuts"][1:-1]]
L += ["  낭독 음성의 속도·음높이·내용은 바꾸지 않았고, 위 지점에서 나눠 사이에 해설을 넣었습니다.", ""]
L += ["[처리 메모] " + x for x in DJ.get("processing_notes", [])]
open(OUT + "bible_transcript.txt", "w", encoding="utf-8-sig").write("\n".join(L))

# ---- narration script + BGM
N = jload("narr.json"); NA = DJ["narration"]; CUES = jload("bgm_cues.json")
L = [f"# {HD} — AI 해설 원고 · BGM 설계", "",
     f"- 해설 음성: **TopView TTS · 'Eunji'(한국어 중년 여성)**, 속도 {C.get('narr_speed',0.92)}, neutral",
     f"- 해설 횟수: **{len(N)}회** (오프닝·전환 {len(N)-2}회·클로징)",
     "- 원칙: 1회 1~2문장, 15초 이내 / 배경·흐름 안내만 / 성경 구절을 해설 목소리로 다시 읽지 않음 / 설교·적용·교파별 판단 배제",
     "- 숫자 표기: TTS는 읽는 대로, 자막은 아라비아 숫자", ""]
for i, n in enumerate(N):
    s = S[f"N{i}"]; x = NA[i]
    L += [f"## 해설 {i+1} (N{i}) — {x['pos']}", "", f"- 영상 시각: **{mmss(s['t'])} – {mmss(s['e'])}** ({s['e']-s['t']:.1f}초)",
          f"- TTS 원고: {n['text']}", "- 자막: " + n["sub"].replace("|", " / "), f"- 화면: {x['screen']}", "- 근거:", x["basis"], ""]
L += ["## BGM 설계 — 음악만으로 본문 흐름을 따라가도록", "", DJ.get("bgm_summary", ""), "",
      "| 영상 시각 | 곡 | 원곡 위치 | 본문과 음악 |", "|---|---|---|---|"]
L += [f"| {mmss(c[0])} | {c[1]} | {c[2]:.0f}초 | {c[3]} |" for c in CUES]
L += ["", "- 곡별 제작 의도: " + DJ.get("bgm_intent", ""), f"- **BGM만 따로 들을 수 있는 파일**: `bgm_only_{CH}{C.get('unit','장')}.m4a`", "",
      "## 확인이 필요한 항목", ""] + [f"{i+1}. {x}" for i, x in enumerate(DJ.get("check_items", []))]
open(OUT + "bible_narration_script.md", "w", encoding="utf-8").write("\n".join(L))

# ---- storyboard
L = [f"# {HD} — 장면별 스토리보드", "", f"- 전체 길이: {mmss(END)[:-3]}"] + ["- " + x for x in DJ.get("storyboard_notes", [])] + ["",
     "| # | 영상 시각 | 구간 | 구절 | 내용 | 시각 요소 | 카메라 | 모션그래픽 | 자막·강조 | BGM |", "|---|---|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(DJ["storyboard_rows"]):
    a, b, kind = T(r[0]), T(r[1]), r[2]
    L.append(f"| {i+1} | {mmss(a)[:-3]}–{mmss(b)[:-3]} | {'**'+kind+'**' if '해설' in kind else kind} | " + " | ".join(r[3:]) + " |")
L += ["", "## 사용 일러스트", ""] + DJ.get("images", []) + ["", "## 역사적 사실과 예술적 상상의 구분", ""] + ["- " + x for x in DJ.get("art_notes", [])]
open(OUT + "bible_storyboard.md", "w", encoding="utf-8").write("\n".join(L))
print("docs ok →", OUT)
