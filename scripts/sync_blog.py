"""네이버 블로그(psb-7) 최신 글과 현장 사진을 받아 posts.json과 images/에 저장합니다.
GitHub Actions에서 매일 실행됩니다."""
import html, io, json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

BLOG = "psb-7"
RSS = f"https://rss.blog.naver.com/{BLOG}.xml"
MAX_POSTS = 40
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
        if any(k in src for k in ("ssl.pstatic.net", "blogpfthumb", "dthumb", "storep", "sticker", "mblogvideo")):
            continue
        base = src.split("?")[0]
        # 현장 카메라 사진(JPEG)만 사용. 표지용 PNG 일러스트는 제외
        if not re.search(r"\.jpe?g$", base, re.I) or "type=w80_blur" in src:
            continue
        if base in [b for b, _ in found]:
            continue
        found.append((base, src))
    found.sort(key=lambda bs: 0 if re.search(r"\.jpe?g$", bs[0], re.I) else 1)
    out = []
    for base, src in found:
        if "postfiles" in base or "blogfiles" in base:
            out.append(base.replace("blogfiles", "postfiles") + "?type=w966")
        elif "mblogthumb-phinf" in base or "blogthumb" in base:
            out.append(base + "?type=w966")
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

HIRES_LOG = "images/.hires"

def fetch_best(url):
    """고화질(w966)을 먼저 받고, 안 되면 w800으로 받습니다."""
    tries = [url]
    if "type=w966" in url:
        tries.append(url.replace("type=w966", "type=w800"))
    last = None
    for u in tries:
        try:
            return get(u)
        except Exception as e:
            last = e
    raise last

def need_upgrade(path, done):
    """예전에 800px로 받은 사진은 한 번만 고화질로 다시 받습니다."""
    if not os.path.exists(path):
        return True
    if path in done:
        return False
    try:
        from PIL import Image
        return Image.open(path).size[0] < 900 and Image.open(path).size[1] < 1100
    except Exception:
        return False

def quote_of(t):
    m = re.search(r"의뢰 내용\s*[\"“](.+?)[\"”]", t)
    return m.group(1).strip()[:120] if m else ""

def main():
    os.makedirs("images", exist_ok=True)
    done = set(open(HIRES_LOG).read().split()) if os.path.exists(HIRES_LOG) else set()
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
            if need_upgrade(path, done):
                had = os.path.exists(path)
                try:
                    save_image(fetch_best(u), path); time.sleep(0.4)
                except Exception as e:
                    print("img fail", u, e, file=sys.stderr)
                    if not had:
                        continue
                done.add(path)
            images.append(path)
        # 글의 마지막 현장 사진 = 보통 시공 완료(After) 사진
        after = ""
        urls = image_urls(page, desc)
        if len(urls) > IMGS_PER_POST:
            apath = f"images/{pid}-a.jpg"
            if need_upgrade(apath, done):
                had = os.path.exists(apath)
                try:
                    save_image(fetch_best(urls[-1]), apath); time.sleep(0.4)
                except Exception as e:
                    print("img fail", urls[-1], e, file=sys.stderr)
                    if not had:
                        apath = ""
                done.add(apath)
            after = apath
        posts.append({
            "id": pid, "title": title, "url": f"https://blog.naver.com/{BLOG}/{pid}",
            "date": date, "category": cat, "summary": text_of(desc)[:160],
            "quote": quote_of(body), "images": images, "after": after, "nimg": len(urls),
        })
        if len(posts) >= MAX_POSTS:
            break
    if not posts:
        print("no posts parsed; keeping existing posts.json", file=sys.stderr); return 1
    open(HIRES_LOG, "w").write("\n".join(sorted(x for x in done if x)))
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M"), "posts": posts},
              open("posts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(posts)} posts, {sum(len(p['images']) for p in posts)} images")
    return 0

if __name__ == "__main__":
    sys.exit(main())
