"""img/*.png → imgs/*.jpg (2400×1347, 카메라 이동 여유분) 변환 + 미리보기 격자(img_grid.jpg).
이전 장 그림 재사용은 imgs/ 에 jpg 를 그냥 복사한다.  사용: python prep_images.py"""
import glob, os
from PIL import Image
os.makedirs("imgs", exist_ok=True)
fs = sorted(glob.glob("img/*.png"))
for f in fs:
    out = "imgs/" + os.path.basename(f)[:-4] + ".jpg"
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f):
        Image.open(f).convert("RGB").resize((2400, 1347), Image.LANCZOS).save(out, quality=90)
allj = sorted(glob.glob("imgs/*.jpg"))
g = Image.new("RGB", (1920, 270 * ((len(allj) + 3) // 4)))
for i, f in enumerate(allj): g.paste(Image.open(f).resize((480, 270)), ((i % 4) * 480, (i // 4) * 270))
g.save("img_grid.jpg", quality=85)
print(len(fs), "변환 /", len(allj), "장 →", "img_grid.jpg (Read 로 검수)")
print("\n".join(os.path.basename(x) for x in allj))
