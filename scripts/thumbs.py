"""images/*.jpg 마다 가벼운 미리보기(images/t/<이름>.webp, 가로 560px)를 만든다.
홈페이지 카드·갤러리는 이 미리보기를 쓰고, 크게 볼 때만 원본을 쓴다."""
import glob, os
from PIL import Image, ImageOps

W, Q = 560, 70
os.makedirs("images/t", exist_ok=True)
made = 0
for src in glob.glob("images/*.jpg"):
    dst = os.path.join("images/t", os.path.basename(src)[:-4] + ".webp")
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        continue
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if im.width > W:
        im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=Q, method=6)
    made += 1
# 원본이 사라진 미리보기 정리
for t in glob.glob("images/t/*.webp"):
    if not os.path.exists("images/" + os.path.basename(t)[:-5] + ".jpg"):
        os.remove(t)
print("미리보기 생성", made)
