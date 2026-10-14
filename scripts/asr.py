"""전체 받아쓰기 (faster-whisper large-v3-turbo, CPU int8) → asr.json
앞부분이나 뒷부분이 빠지면(알려진 현상) 그 구간만 다시 인식해 합친다.
백그라운드 실행 권장:  PYTHONIOENCODING=utf-8 nohup python asr.py > asr.log 2>&1 &
"""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg
from faster_whisper import WhisperModel

C = cfg()
a = np.fromfile("voice16k.f32", np.float32); D = len(a) / 16000
m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=8)

def run(s0, s1, prompt=None):
    segs, _ = m.transcribe(a[int(s0 * 16000):int(s1 * 16000)], language="ko", word_timestamps=True, vad_filter=False,
                           beam_size=5, initial_prompt=prompt, condition_on_previous_text=prompt is not None)
    out = []
    for x in segs:
        out.append({"s": s0 + x.start, "e": s0 + x.end, "text": x.text,
                    "words": [{"w": w.word, "s": s0 + w.start, "e": s0 + w.end, "p": w.probability} for w in x.words]})
        print(f"{s0 + x.start:7.2f} {s0 + x.end:7.2f} {x.text}", flush=True)
    return out

A = run(0, D, C["initial_prompt"])
if A and A[0]["s"] > 1.5:                       # 앞부분 누락
    print("# 앞부분 재인식", flush=True)
    A = run(0, A[0]["s"] + 0.3) + A
if A and A[-1]["e"] < D - 3:                    # 뒷부분 누락 → 40초 단위로 나눠 재인식
    print("# 뒷부분 재인식", flush=True)
    t = A[-1]["e"]
    while t < D - 0.5:
        A += run(t, min(D, t + 40)); t += 40
json.dump(A, open("asr.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE", len(A))
