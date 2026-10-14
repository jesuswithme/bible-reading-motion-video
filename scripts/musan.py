"""곡의 4초 단위 음량(dB)과 밝기(스펙트럼 중심, kHz)를 출력 — BGM 큐의 '원곡 위치'를 고르는 데 쓴다.
가라앉는 곳 = 음량이 낮고 밝기도 낮은 곳, 솟는 곳 = 음량·밝기가 오르는 곳.
사용: python musan.py bgm1.mp3 bgm2.mp3 …"""
import numpy as np, subprocess, sys
SR = 22050
for f in sys.argv[1:]:
    x = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "0", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]), np.float32)
    W = SR * 4; out = []
    for i in range(0, len(x) - W, W):
        s = x[i:i + W]; db = 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9)
        sp = np.abs(np.fft.rfft(s * np.hanning(len(s)))); fr = np.fft.rfftfreq(len(s), 1 / SR); c = (sp * fr).sum() / (sp.sum() + 1e-9)
        out.append(f"{i//SR:3d}s:{db:4.0f}dB/{c/1000:3.1f}k")
    print(f, round(len(x) / SR, 1)); print("  " + " ".join(out))
