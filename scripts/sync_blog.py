"""네이버 블로그(psb-7) 최신 글과 현장 사진을 받아 posts.json과 images/에 저장합니다.
GitHub Actions에서 매일 실행됩니다."""
import html, io, json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

BLOG = "psb-7"
RSS = f"https://rss.blog.naver.com/{BLOG}.xml"
MAX_POSTS = 15
IMGS_PER_POST = 2
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
SKIP_CATEGORY = ("연락처",)
SKIP_TITLE = ("연락문의",)

def get(url, referer="https://m.blog.naver.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def text_of(fragment):
    t = re.sub(r"<[^>]+>", " ", html.unescape(fragment or ""))
    return re.sub(r"\s+", " ", t.replace("ㅤ", " ").replace("​", " ")).strip()

def image_urls(page, desc):
    found = []
    for src in re.findall(r'(?:data-lazy-src|src|content)="(https://[^"]+pstatic\.net/[^"]+)"', page + desc):
        src = html.unescape(src)
        if any(k in src for k in ("profile", "sticker", "storep", "static", "blogpfthumb", "ssl.pstatic.net/static")):
            continue
        base = src.split("?")[0]
        if not re.search(r"\.(jpe?g|png|webp)$", base, re.I):
            continue
        if base in [b for b, _ in found]:
            continue
        found.append((base, src))
    out = []
    for base, src in found:
        if "postfiles" in base or "blogfiles" in base:
            out.append(base.replace("blogfiles", "postfiles") + "?type=w966")
        elif "mblogthumb-phinf" in base or "blogthumb" in base:
            out.append(base + "?type=w800")
        else:
            out.append(src)
    return out

def save_image(data, path):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((1400, 1400))
        im.save(path, "JPEG", quality=82, optimize=True, progressive=True)
    except Exception:
        open(path, "wb").write(data)

def quote_of(t):
    m = re.search(r"의뢰 내용\s*[\"“](.+?)[\"”]", t)
    return m.group(1).strip()[:120] if m else ""

def main():
    root = ET.fromstring(get(RSS))
    posts = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = item.findtext("link") or ""
        cat = (item.findtext("category") or "").strip()
        m = re.search(r"/(\d{9,})", link)
        if not m or any(s in cat for s in SKIP_CATEGORY) or any(s in title for s in SKIP_TITLE):
            continue
        pid = m.group(1)
        desc = item.findtext("description") or ""
        try:
            date = parsedate_to_datetime(item.findtext("pubDate")).strftime("%Y.%m.%d")
        except Exception:
            date = ""
        try:
            page = get(f"https://m.blog.naver.com/PostView.naver?blogId={BLOG}&logNo={pid}").decode("utf-8", "ignore")
        except Exception as e:
            print("page fail", pid, e, file=sys.stderr); page = ""
        body = text_of(page) if page else text_of(desc)
        images = []
        for i, u in enumerate(image_urls(page, desc)[:IMGS_PER_POST * 3]):
            if len(images) >= IMGS_PER_POST:
                break
            path = f"images/{pid}-{len(images)+1}.jpg"
            if not os.path.exists(path):
                try:
                    save_image(get(u), path); time.sleep(0.5)
                except Exception as e:
                    print("img fail", u, e, file=sys.stderr); continue
            images.append(path)
        posts.append({
            "id": pid, "title": title, "url": f"https://blog.naver.com/{BLOG}/{pid}",
            "date": date, "category": cat, "summary": text_of(desc)[:160],
            "quote": quote_of(body), "images": images,
        })
        if len(posts) >= MAX_POSTS:
            break
    if not posts:
        print("no posts parsed; keeping existing posts.json", file=sys.stderr); return 1
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M"), "posts": posts},
              open("posts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(posts)} posts, {sum(len(p['images']) for p in posts)} images")
    return 0

if __name__ == "__main__":
    sys.exit(main())
