"""공통 설정·유틸. 모든 스크립트는 작업 폴더(work dir)를 현재 디렉터리로 두고 실행한다.
작업 폴더의 config.json 을 읽는다 (setup_work.py 가 만든다)."""
import json, os, re, subprocess
import numpy as np

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")

def cfg():
    return json.load(open("config.json", encoding="utf-8"))

def jload(p):
    return json.load(open(p, encoding="utf-8"))

def jdump(o, p, indent=1):
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=indent)

def heading(c):
    """예: '로마서 8장', '시편 23편'"""
    return f"{c['book_ko']} {c['ch']}{c.get('unit','장')}"

def hangul(s):
    return "".join(re.findall(r"[가-힣0-9]", s))

def dur(fn):
    return float(subprocess.check_output(["ffprobe", "-v", "0", "-show_entries", "format=duration", "-of", "csv=p=0", fn]))

SR = 48000
def load_audio(fn, af=None, sr=SR, ch=2):
    cmd = ["ffmpeg", "-v", "0", "-i", fn] + (["-af", af] if af else []) + ["-f", "f32le", "-ac", str(ch), "-ar", str(sr), "-"]
    x = np.frombuffer(subprocess.check_output(cmd), np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x

def mmss(x):
    return f"{int(x//60)}:{x%60:05.2f}"
