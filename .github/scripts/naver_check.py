"""네이버 통합검색·웹문서 탭에서 psb-7.com 노출 여부를 키워드별로 확인 (사이트에는 영향 없음)."""
import json, re, time, glob, html, urllib.parse, urllib.request, os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TARGET = "psb-7.com"
BLOG = "blog.naver.com/psb-7"

def titles():
    out = []
    for f in sorted(glob.glob("area/*.html") + glob.glob("service/*.html") + glob.glob("work/*.html")):
        m = re.search(r"<title>([^<]*)", open(f, encoding="utf-8").read())
        if m:
            out.append(html.unescape(m.group(1)).split(" | ")[0].strip())
    return out

KW = ["하우스랩건설", "하우스랩 건설", "하우스랩", "하우스랩 집수리", "하우스랩건설 집수리",
      "하우스랩 인테리어", "psb-7.com", "site:psb-7.com",
      "경기 광주 집수리", "광주 집수리", "성남 집수리", "하남 집수리", "용인 집수리", "수원 집수리",
      "송파 집수리", "강동 집수리", "분당 집수리",
      "싱크대 경첩 교체", "건조기 선반 설치", "세탁기 위 건조기 선반", "식기세척기 빌트인 설치",
      "하이라이트 교체", "벽걸이 TV 철거", "TV 철거 벽면 복원", "상부장 철거", "싱크대 수전 교체",
      "변기 고정 보수", "벽타일 재부착", "집수리 출장"]
for t in titles():
    if t not in KW:
        KW.append(t)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9",
                                               "Referer": "https://www.naver.com/"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")

def check(page):
    hrefs = re.findall(r'href="(https?://[^"]+)"', page)
    ext = []
    for h in hrefs:
        h = html.unescape(h)
        host = urllib.parse.urlparse(h).netloc
        if any(x in host for x in ("naver.com", "naver.net", "pstatic.net")) and "blog.naver.com" not in host:
            continue
        if h not in ext:
            ext.append(h)
    site = [i for i, h in enumerate(ext) if TARGET in h]
    blog = [i for i, h in enumerate(ext) if BLOG in h]
    return {"site": bool(site) or TARGET in page, "site_rank": (site[0] + 1) if site else None,
            "site_urls": [ext[i] for i in site][:5], "blog": bool(blog), "blog_rank": (blog[0] + 1) if blog else None,
            "captcha": ("captcha" in page.lower() and len(page) < 20000), "len": len(page)}

res = []
for k in KW:
    q = urllib.parse.quote(k)
    row = {"kw": k}
    for tab, url in (("통합", f"https://search.naver.com/search.naver?where=nexearch&query={q}"),
                     ("웹문서", f"https://search.naver.com/search.naver?ssc=tab.web.all&query={q}")):
        try:
            row[tab] = check(fetch(url))
        except Exception as e:
            row[tab] = {"error": str(e)}
        time.sleep(2.5)
    res.append(row)
    print(k, "|", {t: (row[t].get("site"), row[t].get("site_rank")) for t in ("통합", "웹문서")}, flush=True)

os.makedirs("naver", exist_ok=True)
json.dump(res, open("naver/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
