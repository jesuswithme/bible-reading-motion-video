"""해설 음성 검수: tts/N*.mp3 길이, 음성인식 결과(발음 확인), 문장 끝 시각(→ chapter.json nsplit 값).
15초를 넘거나 발음이 이상하면 원고를 줄이거나 pronRules 로 다시 생성한다.
※ 인식기는 '계명→개명', '침례→침내', '할례→할레'처럼 표준 발음대로 적기도 한다(문제 아님)."""
import glob, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")
for f in sorted(glob.glob("tts/N[0-9]*.mp3")):
    a = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "0", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"]), np.float32)
    s, _ = m.transcribe(a, language="ko", word_timestamps=True)
    words = [w for seg in s for w in seg.words]
    ends = [round(w.end, 2) for w in words if w.word.strip().endswith((".", ",", "?"))]
    d = len(a) / 16000
    print(f"{f} {d:.2f}s {'⚠ 15초 초과' if d > 15 else ''}\n  {''.join(w.word for w in words).strip()}\n  문장 끝: {ends}")
