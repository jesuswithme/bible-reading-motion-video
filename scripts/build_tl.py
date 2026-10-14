"""타임라인 생성: chapter.json + narr.json + tts/N*.mp3 + subs_reader.json + chapter_tl.py → tl.json, bgm_cues.json, index.html

구조: [해설 N0] [낭독 R1] [해설 N1] [낭독 R2] … [낭독 Rn] [해설 Nn] [엔딩]
- chapter.json "cuts": 낭독 분할점(원본 초). 처음 0, 끝 원본 길이. 무음 구간 중앙을 쓴다.
- 해설 수 = 낭독 구간 수 + 1. tts/N0.mp3 … 길이는 자동 측정.
- chapter.json "nsplit": 해설 자막을 두 줄로 나눌 시각(해설 파일 안의 초). null 이면 두 줄을 한 화면에.
- chapter.json "parts": 낭독 구간마다 {"title","ref"}  (스팅어·엔딩 요약 칩)
- chapter.json "kw": 자막 금색 강조어
chapter_tl.py 안에서 쓸 수 있는 것: R(원본초)→영상초, pt(절,구절,end=False)→원본초, N["N3"]["t"],
  E(kind,t,e,**kw), END, DULL/EMB 색, MG(ΜΗ ΓΕΝΟΙΤΟ). shots=[…] 와 bgm=[…] 를 정의한다.
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, jload, dur

C = cfg(); CJ = jload("chapter.json")
SUB = jload("subs_reader.json"); NAR = jload("narr.json")
CUTS = CJ["cuts"]; NR = len(CUTS) - 1
NDUR = [round(dur(f"tts/N{i}.mp3"), 3) for i in range(NR + 1)]
NSPLIT = CJ.get("nsplit", [None] * (NR + 1))
PAD = CJ.get("pad", 0.8)
segs = []; t = 2.5
def nar(i):
    global t
    segs.append({"kind": "nar", "id": f"N{i}", "t": round(t, 3), "e": round(t + NDUR[i], 3), "file": f"tts/N{i}.mp3"}); t += NDUR[i]
nar(0); t += 1.0
for k in range(NR):
    a, b = CUTS[k], CUTS[k + 1]
    segs.append({"kind": "read", "id": f"R{k+1}", "t": round(t, 3), "e": round(t + b - a, 3), "src": [a, b]}); t += b - a
    t += PAD; nar(k + 1); t += PAD if k < NR - 1 else 0
END = round(t + 5.5, 2)
def r2f(x):
    for s in segs:
        if s["kind"] == "read" and s["src"][0] <= x <= s["src"][1] + 0.01: return round(s["t"] + x - s["src"][0], 3)
    raise ValueError(f"원본 {x}초는 낭독 구간 밖")
R = r2f
subs = [{"kind": "read", "v": s["v"], "text": s["text"], "t": r2f(s["t"]), "e": r2f(s["e"])} for s in SUB]
for i, s in enumerate([x for x in segs if x["kind"] == "nar"]):
    L = NAR[i]["sub"].split("|")
    if NSPLIT[i] and len(L) > 1:
        subs += [{"kind": "nar", "text": L[0], "t": s["t"], "e": round(s["t"] + NSPLIT[i], 3)},
                 {"kind": "nar", "text": L[1], "t": round(s["t"] + NSPLIT[i], 3), "e": s["e"]}]
    else: subs.append({"kind": "nar", "text": "\n".join(L), "t": s["t"], "e": s["e"]})
subs.sort(key=lambda x: x["t"])
vs = {}
for s in subs:
    if s["kind"] == "read" and isinstance(s["v"], int): vs.setdefault(s["v"], s["t"])
V = {int(k): v for k, v in jload("verses.json").items()}
M = jload("charmap.json"); own, ot = M["own"], M["ot"]
def pt(k, phrase, end=False):
    vc = "".join(re.findall(r"[가-힣0-9]", V[k])); pc = "".join(re.findall(r"[가-힣0-9]", phrase))
    i = vc.index(pc); idx = [j for j, x in enumerate(own) if x == str(k)]
    return ot[idx[i + len(pc) - 1]][1] if end else ot[idx[i]][0]
N = {s["id"]: s for s in segs}
ev = []
def E(kind, t, e, **kw): ev.append(dict(kind=kind, t=round(t, 3), e=round(e, 3), **kw))
DULL = "#a89b86"; EMB = "#e9a77a"; MG = "ΜΗ ΓΕΝΟΙΤΟ"
shots = []; bgm = []
exec(open("chapter_tl.py", encoding="utf-8").read())
shots = [s if isinstance(s, dict) else {"img": s[0], "t": round(s[1], 3), "mv": s[2], "g": s[3], "rays": s[4]} for s in shots]
for i, s in enumerate(shots): s["e"] = shots[i + 1]["t"] if i + 1 < len(shots) else END
# 겹침 정리: 화면 가운데 요소는 다음 요소 직전에 끝냄(keep=1 은 예외), 인용 칩끼리도 동일
CENTER = {"kw", "hero", "dual", "stack", "list", "swap", "sins", "stamp"}
evs = sorted(ev, key=lambda x: x["t"])
for i, e in enumerate(evs):
    grp = CENTER if e["kind"] in CENTER else {e["kind"]}
    nxt = [x for x in evs[i + 1:] if x["kind"] in grp and x["t"] > e["t"] + 0.5 and e["kind"] != "sins"]
    if nxt and nxt[0]["t"] < e["e"] and not e.get("keep"): e["e"] = round(max(e["t"] + 1.0, nxt[0]["t"] - 0.1), 3)
ev = evs
E("endtitle", N[f"N{NR}"]["t"] + 0.3, END)
parts = [{"n": f"{i+1:02d}", "title": p["title"], "ref": p["ref"], "t": N[f"N{i}"]["t"]} for i, p in enumerate(CJ["parts"])]
info = jload("textinfo.json")
TL = {"ch": C["ch"], "book": C["book_ko"], "bookEn": C["book_en"], "unit": C.get("unit", "장"), "version": C.get("version_label", "개역개정"),
      "segs": segs, "subs": subs, "vstart": vs, "END": END, "shots": shots, "ev": ev, "parts": parts, "kw": CJ.get("kw", []), "vl": info.get("vl", {})}
json.dump(TL, open("tl.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(bgm, open("bgm_cues.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
s = open("tpl.html", encoding="utf-8").read().replace("__TL__", json.dumps(TL, ensure_ascii=False))
open("index.html", "w", encoding="utf-8").write(s)
for s in segs: print(s["id"], s["t"], s["e"])
print("END", END, "frames", int(END * 30 + 0.999), "|", len(shots), "shots", len(ev), "events", len(bgm), "bgm cues")
for b in bgm: print(f"  {b[0]:6.1f}s {b[1]} @{b[2]:.1f} {b[3]}")
