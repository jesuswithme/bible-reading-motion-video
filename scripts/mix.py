"""오디오 믹스 → mix.m4a (최종), {out_dir}/bgm_only_N장.m4a
- 낭독(원본, 70Hz 고역통과) + 해설(발화 RMS를 낭독과 같게) 배치
- BGM: bgm_cues.json 큐대로 여러 곡의 해당 부분을 이어 붙임(2.5초 크로스페이드).
  곡마다 전체 RMS를 '낭독 RMS × bgm_ratio'로 정규화 → 녹음 음량이 달라도 낭독-BGM 간격 유지
- 더킹: 발화 중 BGM 0.34배, 쉼 0.80배. hero(금빛 문구) 구간은 30% 더 낮춤
- 최종 음량: config target_lufs(기본 -16)에 자동으로 맞춤(리미터 -1.5 dBTP)
"""
import json, subprocess, re, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, jload, load_audio, SR

C = cfg(); TL = jload("tl.json"); END = TL["END"]; N = int(END * SR) + SR
reader = load_audio(C["audio"], "highpass=f=70")
def env(x, win=0.05):
    m = np.abs(x).mean(1); k = int(win * SR); c = np.cumsum(np.concatenate([[0], m]))
    i = np.arange(len(m)); a = np.clip(i - k // 2, 0, len(m)); b = np.clip(i + k // 2, 0, len(m)); return (c[b] - c[a]) / np.maximum(b - a, 1)
def active_rms(x):
    e = env(x); s = x[e > e.max() * 0.08]; return np.sqrt((s ** 2).mean())
voice = np.zeros((N, 2), np.float32); speech = np.zeros(N, np.float32)
rr = active_rms(reader)
for s in TL["segs"]:
    i = int(s["t"] * SR)
    if s["kind"] == "read":
        seg = reader[int(s["src"][0] * SR):int(s["src"][1] * SR)].copy()
        f = int(0.02 * SR); r = np.linspace(0, 1, f)[:, None]; seg[:f] *= r; seg[-f:] *= r[::-1]
    else:
        seg = load_audio(s["file"]); seg *= rr / active_rms(seg)
    voice[i:i + len(seg)] += seg[:N - i]
    e = env(seg); speech[i:i + len(e)] = np.maximum(speech[i:i + len(e)], (e > e.max() * 0.06).astype(np.float32)[:N - i])
def ma(x, k):
    c = np.cumsum(np.concatenate([[0], x])); h = k // 2; i = np.arange(len(x))
    return (c[np.clip(i + h, 0, len(x))] - c[np.clip(i - h, 0, len(x))]) / k
m = np.clip(ma(ma(speech, int(0.6 * SR)), int(0.6 * SR)) * 1.8, 0, 1)
gain = 0.80 - 0.46 * m
for e in TL["ev"]:
    if e["kind"] == "hero":
        a, b = int((e["t"] - .5) * SR), min(N, int((e["e"] + .5) * SR)); f = int(.5 * SR)
        w = np.ones(b - a); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
        gain[a:b] *= 1 - 0.3 * w
CUES = jload("bgm_cues.json"); SRC = {}
target = rr * C.get("bgm_ratio", 0.58)
for c in CUES:
    if c[1] not in SRC:
        x = load_audio(c[1]); x *= target / np.sqrt((x ** 2).mean()); SRC[c[1]] = x
bgm = np.zeros((N, 2), np.float32); XF = 2.5
for k, c in enumerate(CUES):
    ct, f, off = c[0], c[1], c[2]
    nt = CUES[k + 1][0] if k + 1 < len(CUES) else END + 1
    a0 = max(0, ct - XF / 2) if k else 0.0; a1 = min(END + 1, nt + XF / 2)
    i0 = int(a0 * SR); i1 = min(N, int(a1 * SR))
    src = SRC[f]; o0 = int(max(0, off - (ct - a0)) * SR); n = max(0, min(i1 - i0, len(src) - o0))
    if n < (i1 - i0): print(f"! cue {k}: {f}가 {(i1-i0-n)/SR:.1f}초 모자람 — 원곡 위치를 앞당기세요")
    seg = src[o0:o0 + n].copy(); tt = np.arange(n) / SR + a0; w = np.ones(n)
    if k: w *= np.clip((tt - (ct - XF / 2)) / XF, 0, 1)
    if k + 1 < len(CUES): w *= np.clip(((nt + XF / 2) - tt) / XF, 0, 1)
    bgm[i0:i0 + n] += seg * w[:, None]
t = np.arange(N) / SR
fade = (np.clip(t / 2.0, 0, 1) * np.clip((END - 0.3 - t) / 4.0, 0, 1))
out = (voice + bgm * (gain * fade)[:, None])[:int(END * SR)]
out.astype(np.float32).tofile("mix_raw.f32")
db = lambda a: 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9); sp = speech[:len(out)] > 0.5
print(f"낭독 {db(voice[:len(out)][sp]):.1f}dB / 발화 중 BGM {db((bgm*(gain*fade)[:,None])[:len(out)][sp]):.1f}dB (간격 14~15dB 권장)")

def measure(vol):
    af = f"volume={vol}dB,alimiter=limit=0.84:attack=2:release=80:level=disabled"
    r = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "mix_raw.f32", "-af", af + ",loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.search(r'"input_i" : "([-\d.]+)"', r).group(1)), af
T = C.get("target_lufs", -16.0); vol = 5.0
for _ in range(3):
    I, af = measure(vol)
    if abs(I - T) < 0.25: break
    vol = round(vol + (T - I), 1)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "mix_raw.f32", "-af", af, "-c:a", "aac", "-b:a", "256k", "mix.m4a"], check=True)
print(f"최종 {I} LUFS (volume {vol}dB) → mix.m4a")
b = (bgm * fade[:, None])[:int(END * SR)]; b *= 0.5 / (np.abs(b).max() + 1e-9)
bo = os.path.join(C["out_dir"], f"bgm_only_{C['ch']}{C.get('unit','장')}.m4a")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", bo], input=b.astype(np.float32).tobytes(), check=True)
print("BGM 전용 →", bo)
