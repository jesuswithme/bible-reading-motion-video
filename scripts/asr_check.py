"""의심 구간을 두 모델(turbo, small)로 다시 인식해 낭독자의 실제 읽기인지 인식 오류인지 판정한다.
두 모델이 똑같이 본문과 다르게 들으면 '낭독 확인 필요'로 보고한다.
사용: python asr_check.py 145.0-151.3 196.3-204.3
"""
import sys
import numpy as np
from faster_whisper import WhisperModel

a = np.fromfile("voice16k.f32", np.float32)
spans = [tuple(map(float, x.split("-"))) for x in sys.argv[1:]]
for name in ["mobiuslabsgmbh/faster-whisper-large-v3-turbo", "Systran/faster-whisper-small"]:
    m = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=8)
    for s, e in spans:
        segs, _ = m.transcribe(a[int(s * 16000):int(e * 16000)], language="ko", beam_size=5, condition_on_previous_text=False)
        print(name.split("-")[-1], s, "|", " ".join(x.text for x in segs), flush=True)
