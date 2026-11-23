"""다른 블로그(같은 업체)에서 특정 작업 글과 사진을 찾아 extra_out/ 에 모읍니다. 저장소에는 올리지 않고 Actions 결과물로만 받습니다."""
import html, io, json, os, re, sys, time, urllib.parse, urllib.request

BLOG = os.environ.get("EXTRA_BLOG", "ssus7777")
KEYS = re.compile(r"아트월|TV|티비|tv|백시멘|백세멘|백색\s*시멘트|변기\s*테두리|변기")
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
OUT = "extra_out"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://m.blog.naver.com/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def titles():
    out = []
    for page in range(1, 40):
        u = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={BLOG}&viewdate=&currentPage={page}&categoryNo=0&parentCategoryNo=&countPerPage=30"
        try:
            t = get(u).decode("utf-8", "ignore")
        except Exception as e:
            print("list fail", page, e, file=sys.stderr); break
        items = re.findall(r'"logNo":"(\d+)","title":"([^"]*)".*?"addDate":"([^"]*)"', t)
        if not items:
            break
        for no, ti, d in items:
            out.append({"id": no, "title": urllib.parse.unquote_plus(ti), "date": d})
        time.sleep(0.3)
    if not out:  # RSS로 대신
        t = get(f"https://rss.blog.naver.com/{BLOG}.xml").decode("utf-8", "ignore")
        for link, ti in re.findall(r"<item>.*?<link>(.*?)</link>.*?<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", t, re.S):
            m = re.search(r"/(\d{9,})", link)
            if m: out.append({"id": m.group(1), "title": html.unescape(ti), "date": ""})
    return out

def images(page):
    found = []
    for src in re.findall(r'(?:data-lazy-src|src)="(https://[^"]+pstatic\.net/[^"]+)"', page):
        src = html.unescape(src)
        if any(k in src for k in ("ssl.pstatic.net", "blogpfthumb", "dthumb", "storep", "sticker", "mblogvideo")):
            continue
        base = src.split("?")[0]
        if not re.search(r"\.jpe?g$", base, re.I) or base in found:
            continue
        found.append(base)
    return [b.replace("blogfiles", "postfiles") + "?type=w966" for b in found]

def main():
    os.makedirs(OUT, exist_ok=True)
    all_t = titles()
    json.dump(all_t, open(f"{OUT}/titles.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hits = [p for p in all_t if KEYS.search(p["title"])]
    def prio(p):
        t = p["title"]
        if re.search(r"백시멘|백세멘|변기\s*테두리", t): return 0
        if re.search(r"아트월", t) and re.search(r"TV|티비|tv", t): return 0
        if re.search(r"아트월", t): return 1
        if re.search(r"변기", t): return 2
        return 3
    hits.sort(key=prio)
    print(len(all_t), "posts,", len(hits), "matches")
    from PIL import Image
    for p in hits[:25]:
        try:
            page = get(f"https://m.blog.naver.com/PostView.naver?blogId={BLOG}&logNo={p['id']}").decode("utf-8", "ignore")
        except Exception as e:
            print("page fail", p["id"], e, file=sys.stderr); continue
        urls = images(page)
        p["nimg"] = len(urls)
        d = f"{OUT}/{p['id']}"; os.makedirs(d, exist_ok=True)
        for i, u in enumerate(urls[:16]):
            try:
                data = None
                for uu in (u, u.replace("type=w966", "type=w800")):
                    try: data = get(uu); break
                    except Exception: pass
                im = Image.open(io.BytesIO(data)).convert("RGB"); im.thumbnail((1400, 1400))
                im.save(f"{d}/{i+1:02d}.jpg", "JPEG", quality=84, optimize=True)
                time.sleep(0.3)
            except Exception as e:
                print("img fail", u, e, file=sys.stderr)
        body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(page)))
        m = re.search(r"의뢰 내용\s*[\"“](.+?)[\"”]", body)
        p["quote"] = m.group(1)[:160] if m else ""
    json.dump(hits, open(f"{OUT}/hits.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
