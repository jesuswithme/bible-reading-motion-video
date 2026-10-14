"""manual_split.txt(절|줄1|줄2…) 로 낭독 자막과 시각(subs_reader.json)을 만든다.
- 각 줄을 이어 붙이면 개역개정 본문과 정확히 같아야 한다(다르면 오류).
- chapter.json 의 "onsets": {"절": 초} — 단락 분할 직후 절의 첫 글자 시각을 무음 끝으로 당긴다
  (안 하면 첫 자막이 앞 단락 끝에 붙는다). charmap.json 에 반영된다.
- chapter.json 의 "amen": [시작, 끝] — '아멘'이 인식에서 빠졌을 때 직접 지정.
- chapter.json 의 "extra_subs": 낭독자가 구절을 반복해 읽은 경우 등 실제 낭독대로 넣을 줄.
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, heading, jload

C = cfg(); CJ = jload("chapter.json") if os.path.exists("chapter.json") else {}
V = {int(k): v for k, v in jload("verses.json").items()}
M = jload("charmap.json"); own, ot = M["own"], M["ot"]
for k, f in CJ.get("onsets", {}).items():
    for i in [j for j, x in enumerate(own) if x == str(k)][:20]:
        a, b = ot[i]
        if a < f: ot[i] = [f, max(b, f + 0.05)]
if CJ.get("amen"):
    idx = [j for j, x in enumerate(own) if x == "amen"]; a0, a1 = CJ["amen"]
    for n, i in enumerate(idx): ot[i] = [a0 + (a1 - a0) * n / len(idx), a0 + (a1 - a0) * (n + 1) / len(idx)]
json.dump(M, open("charmap.json", "w", encoding="utf-8"), ensure_ascii=False)

S = []
idx = [i for i, x in enumerate(own) if x == "title"]
S.append({"v": "title", "text": heading(C), "t": round(ot[idx[0]][0], 2), "e": round(ot[idx[-1]][1], 2)})
for line in open("manual_split.txt", encoding="utf-8"):
    if not line.strip(): continue
    k, *parts = line.strip().split("|"); k = int(k)
    assert " ".join(parts) == V[k], f"{k}절 줄 나눔이 본문과 다름:\n{' '.join(parts)}\n{V[k]}"
    idx = [i for i, x in enumerate(own) if x == str(k)]; p = 0
    for c in parts:
        n = len(re.findall(r"[가-힣0-9]", c)); seg = idx[p:p + n]; p += n
        S.append({"v": k, "text": c, "t": round(ot[seg[0]][0], 2), "e": round(ot[seg[-1]][1], 2)})
for x in CJ.get("extra_subs", []): S.append(dict(x, repeat=1))
idx = [i for i, x in enumerate(own) if x == "amen"]
S.append({"v": "amen", "text": "아멘", "t": round(ot[idx[0]][0], 2), "e": round(ot[idx[-1]][1], 2)})
S.sort(key=lambda s: s["t"])
json.dump(S, open("subs_reader.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(S), "줄 / 최장", max(len(s["text"]) for s in S), "자")
