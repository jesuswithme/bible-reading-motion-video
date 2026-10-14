"""본문(verses.json) 글자와 음성인식(asr.json) 글자를 정렬해 글자별 시각표(charmap.json)를 만든다.
머리말('로마서 8장')과 끝의 '아멘'도 포함한다. 각 절의 시작·끝 시각을 출력한다."""
import json, difflib, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, heading, jload

C = cfg()
V = {int(k): v for k, v in jload("verses.json").items()}
A = jload("asr.json")
ac, at = [], []
for s in A:
    for w in s["words"]:
        ch = [c for c in w["w"] if re.match(r"[가-힣0-9]", c)]; n = len(ch)
        for i, c in enumerate(ch):
            ac.append(c); at.append((w["s"] + (w["e"] - w["s"]) * i / max(n, 1), w["s"] + (w["e"] - w["s"]) * (i + 1) / max(n, 1)))
units = [("title", heading(C))] + [(k, V[k]) for k in sorted(V)] + [("amen", "아멘")]
oc, own = [], []
for u, txt in units:
    for c in txt:
        if re.match(r"[가-힣0-9]", c): oc.append(c); own.append(str(u))
sm = difflib.SequenceMatcher(None, oc, ac, autojunk=False); ot = [None] * len(oc)
for a, b, n in sm.get_matching_blocks():
    for i in range(n): ot[a + i] = at[b + i]
print("matched", sum(x is not None for x in ot), "/", len(oc))
for i in range(len(ot)):
    if ot[i] is None:
        p = next((ot[j][1] for j in range(i - 1, -1, -1) if ot[j]), 0)
        q = next((ot[j][0] for j in range(i + 1, len(ot)) if ot[j]), p); ot[i] = (p, q)
json.dump({"oc": oc, "own": own, "ot": ot}, open("charmap.json", "w", encoding="utf-8"), ensure_ascii=False)
for u, _ in units:
    idx = [i for i, x in enumerate(own) if x == str(u)]
    print(u, round(ot[idx[0]][0], 2), round(ot[idx[-1]][1], 2))
