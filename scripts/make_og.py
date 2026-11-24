"""카카오톡·문자·검색에서 링크를 보낼 때 보이는 공유 이미지(og.jpg, 1200x630)를 만든다."""
import glob, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

BG = sys.argv[1] if len(sys.argv) > 1 else "images/224424462114-2.jpg"
W, H = 1200, 630
GOLD, GOLD2, INK = (200, 169, 106), (232, 213, 166), (13, 13, 11)

def font(bold, size):
    cands = (["/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"] if bold
             else ["/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"])
    cands += glob.glob("/usr/share/fonts/**/wqy-zenhei.ttc", recursive=True)
    for c in cands:
        try:
            return ImageFont.truetype(c, size, index=1 if "Noto" in c else 0)
        except OSError:
            continue
    raise SystemExit("한글 글꼴 없음")

im = ImageOps.fit(ImageOps.exif_transpose(Image.open(BG)).convert("RGB"), (W, H), centering=(0.5, 0.55))
im = im.filter(ImageFilter.GaussianBlur(1.2))
# 왼쪽은 진하게, 오른쪽은 사진이 보이게
shade = Image.new("L", (W, 1))
for x in range(W):
    shade.putpixel((x, 0), int(245 - 130 * max(0, (x - 480) / 720)))
shade = shade.resize((W, H))
im = Image.composite(Image.new("RGB", (W, H), INK), im, shade)
d = ImageDraw.Draw(im)
d.rectangle([0, 0, 10, H], fill=GOLD)
x = 78
d.text((x, 92), "하우스랩 건설  |  집수리·부분 인테리어 전문", font=font(False, 30), fill=GOLD2)
d.text((x, 160), "우리 집 불편한 곳,", font=font(True, 66), fill=(255, 255, 255))
d.text((x, 248), "필요한 부분만 ", font=font(True, 66), fill=(255, 255, 255))
w = d.textlength("필요한 부분만 ", font=font(True, 66))
d.text((x + w, 248), "정확하게", font=font(True, 66), fill=GOLD)
d.text((x, 336), "수리합니다.", font=font(True, 66), fill=(255, 255, 255))
d.text((x, 452), "싱크대 · 욕실 · 가구·문 · 가전 설치 · 철거 및 원상복구", font=font(False, 28), fill=(225, 222, 214))
d.text((x, 510), "사진 상담 · 무료 견적 · 직접 시공", font=font(False, 28), fill=GOLD2)
# 전화번호 배지
f = font(True, 34)
t = "010-5931-7025"
tw = d.textlength(t, font=f)
bx = W - 78 - tw - 56
d.rounded_rectangle([bx, 500, W - 78, 566], radius=33, fill=GOLD)
d.text((bx + 28, 510), t, font=f, fill=INK)
im.save("og.jpg", "JPEG", quality=86, optimize=True, progressive=True)
print("og.jpg 생성")
