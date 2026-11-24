"""사진이 안 받아진 글의 이미지 주소를 조사해서 debug/ 에 저장한다 (사이트에는 반영 안 됨)."""
import os, re, sys, html, urllib.request
sys.path.insert(0, "scripts")
from sync_blog import get, image_urls, fetch_best, save_image
BLOG = "psb-7"
IDS = ["224353957791"]
os.makedirs("debug", exist_ok=True)
for pid in IDS:
    page = get(f"https://m.blog.naver.com/PostView.naver?blogId={BLOG}&logNo={pid}").decode("utf-8", "ignore")
    open(f"debug/{pid}.html", "w").write(page)
    srcs = re.findall(r'(?:data-lazy-src|src|content|data-src)="(https://[^"]+pstatic\.net/[^"]+)"', page)
    open(f"debug/{pid}-srcs.txt", "w").write("\n".join(html.unescape(s) for s in srcs))
    print(pid, len(srcs), len(image_urls(page, "")))
