"""prompts.json({"01_name": "프롬프트", ...}) → codex-image(gpt-image-2, ChatGPT 로그인)로 img/01_name.png 생성.
이미 있는 파일은 건너뛴다(다시 만들 그림은 img/ 에서 지우고 재실행). 한 장씩 순서대로, 장당 약 1분.
사용: python gen_images.py   (백그라운드: nohup python gen_images.py > img.log 2>&1 &)"""
import glob, json, os, shutil, subprocess, time
os.makedirs("img", exist_ok=True)
GEN = os.path.expanduser("~/.codex/generated_images")
prompts = json.load(open("prompts.json", encoding="utf-8"))
for name, prompt in prompts.items():
    out = f"img/{name}.png"
    if os.path.exists(out):
        continue
    t0 = time.time()
    msg = f"Generate an image of '{prompt}' in landscape 1536x1024 size using the image_gen tool. Do not run any shell commands."
    subprocess.run(["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "-"],
                   input=msg, text=True, encoding="utf-8", capture_output=True, shell=os.name == "nt")
    new = [f for f in glob.glob(GEN + "/*/*.png") if os.path.getmtime(f) > t0]
    if new:
        shutil.copy(max(new, key=os.path.getmtime), out)
        print("OK  ", out, flush=True)
    else:
        print("FAIL", out, flush=True)
