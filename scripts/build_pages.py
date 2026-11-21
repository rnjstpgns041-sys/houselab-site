"""posts.json을 읽어 시공 분야별 페이지(service/*.html), sitemap.xml, robots.txt를 만듭니다.
네이버·구글 검색이 분야별 페이지와 실제 시공 사례를 읽을 수 있도록 글 내용을 HTML에 그대로 넣습니다.
GitHub Actions에서 블로그 동기화 후 자동으로 실행됩니다."""
import html, json, os, re, time

SITE = "https://psb-7.com"
TEL = "010-5931-7025"
TEL_RAW = "01059317025"

CATS = [
    {"slug": "kitchen", "name": "주방 수리", "kw": "싱크대·상판·싱크볼 교체",
     "desc": "싱크대 문짝·경첩, 상판 크랙, 싱크볼·수전 교체, 상부장·하부장 리폼까지 주방에서 필요한 부분만 정확하게 고칩니다.",
     "items": ["싱크대 문짝·경첩 수리", "상판 크랙·대리석 균열 보수", "싱크볼·수전 교체", "팝업 배수구 교체", "상부장·하부장 리폼", "냉장고장 높이 맞춤"]},
    {"slug": "appliance", "name": "가전 설치", "kw": "식기세척기·가스레인지·하이라이트·건조기 설치",
     "desc": "식기세척기 빌트인, 가스레인지·하이라이트·인덕션 교체, 세탁기 위 건조기 설치까지. 자리가 안 맞으면 상판 가공과 공간 리폼으로 맞춰 설치합니다.",
     "items": ["식기세척기 빌트인 설치", "가스레인지 교체·매립", "하이라이트·인덕션 설치", "세탁기 위 건조기 설치", "건조기 렉·선반 제작", "콤보 세탁건조기 빌트인"]},
    {"slug": "bathroom", "name": "욕실·타일 수리", "kw": "변기·타일·실리콘·세면대",
     "desc": "흔들리는 변기 하부 보수, 들뜬 벽타일 재부착, 깨진 아트월 타일 부분 교체, 실리콘 재시공과 세면대 누수까지 고칩니다.",
     "items": ["변기 흔들림·하부 보수", "들뜬 벽타일 재부착", "아트월 타일 부분 교체", "실리콘 재시공", "세면대 누수·배관", "환풍기 교체"]},
    {"slug": "removal", "name": "철거·원상복구", "kw": "TV·상부장·빌트인 냉장고 철거",
     "desc": "이사 전 벽걸이 TV 철거와 콘센트 원상복구, 앙카볼트 제거와 벽면 복원, 상부장·오븐장·빌트인 냉장고 철거와 폐기까지 진행합니다.",
     "items": ["벽걸이 TV 철거·원상복구", "앙카볼트 제거·벽면 복원", "상부장·냉장고장 철거", "빌트인 냉장고 철거·폐기", "오븐장 철거", "벽걸이 세탁기 철거"]},
    {"slug": "repair", "name": "문·가구·기타 수리", "kw": "문짝·붙박이장·수납장·콘센트",
     "desc": "문짝·문틀과 경첩, 손잡이, 붙박이장 롤러와 슬라이딩 도어, 수납장 제작, 콘센트 재설치처럼 집 안 곳곳의 작은 고장을 고칩니다.",
     "items": ["문짝·문틀 교체", "경첩·손잡이·도어락", "붙박이장 롤러·슬라이딩 도어", "베란다 수납장 제작", "콘센트 재설치·배선 정리", "몰딩·선반·커튼레일"]},
]

def cat_of(title):
    t = title
    if re.search(r"식기세척기|가스레인지|하이라이트|인덕션|건조기|세탁기|콤보|환풍기", t) and re.search(r"설치|교체|이동", t) and not re.search(r"철거 앙카|미니 세탁기 철거", t):
        return "bathroom" if "환풍기" in t else "appliance"
    if re.search(r"변기|욕실|화장실|타일|아트월|실리콘|세면대", t):
        return "bathroom"
    if re.search(r"철거|폐기|원상복구|앙카", t):
        return "removal"
    if re.search(r"싱크|상판|상부장|하부장|주방|대리석|냉장고장", t):
        return "kitchen"
    return "repair"

e = lambda s: html.escape(str(s or ""), quote=True)

CSS = """
:root{--bg:#FBFAF7;--alt:#F3F0E9;--surface:#fff;--ink:#16150F;--muted:#5C584F;--line:#E4DED2;--gold:#C8A96A;--gold2:#E8D5A6;--night:#0D0D0B;--accent:#8A6A2F}
@media (prefers-color-scheme:dark){:root{--bg:#0D0D0B;--alt:#15140F;--surface:#1C1B16;--ink:#F2EEE6;--muted:#A9A398;--line:#2C2A23;--accent:#D4B57A}}
*{box-sizing:border-box}html,body{overflow-x:clip}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;font-size:17px;line-height:1.6;letter-spacing:-.015em;padding-bottom:84px;word-break:keep-all}
a{color:inherit}.wrap{max-width:1160px;margin:0 auto;padding:0 20px}
header{position:sticky;top:0;z-index:5;background:rgba(13,13,11,.88);backdrop-filter:blur(16px);border-bottom:1px solid rgba(200,169,106,.2)}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:56px}
.logo{color:#F2EEE6;text-decoration:none;font-weight:800;font-size:19px}
.call{display:inline-flex;align-items:center;gap:6px;background:var(--gold);color:#16150F;text-decoration:none;font-weight:700;border-radius:999px;padding:8px 16px;font-size:15px}
.hero{background:radial-gradient(900px 400px at 50% 0%,#2A2416,var(--night) 65%);color:#F2EEE6;padding:56px 0 48px;text-align:center}
.crumb{font-size:14px;color:#A9A398}.crumb a{color:var(--gold2)}
h1{font-size:clamp(30px,5vw,52px);line-height:1.2;margin:12px 0 0;letter-spacing:-.04em}
h1 span{color:var(--gold)}
.lead{color:#C9C3B6;max-width:40em;margin:16px auto 0}
.btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:26px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:54px;padding:0 26px;border-radius:999px;font-weight:700;text-decoration:none;font-size:17px}
.btn.gold{background:linear-gradient(135deg,var(--gold2),var(--gold) 60%);color:#16150F}
.btn.ghost{border:1.5px solid rgba(242,238,230,.55);color:#F2EEE6}
.items{list-style:none;padding:0;margin:26px auto 0;display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:820px}
.items li{font-size:14.5px;padding:7px 13px;border-radius:999px;border:1px solid rgba(200,169,106,.45);background:rgba(200,169,106,.1)}
section{padding:64px 0}h2{font-size:clamp(26px,3.6vw,38px);letter-spacing:-.04em;margin:0 0 8px;text-align:center}
.sub{text-align:center;color:var(--muted);margin:0 0 30px}
.cases{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.case{background:var(--surface);border:1px solid var(--line);border-radius:20px;overflow:hidden;text-decoration:none;display:flex;flex-direction:column}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:2px;position:relative}
.pair img{width:100%;aspect-ratio:1;object-fit:cover;display:block}
.pair .t{position:absolute;top:8px;font-size:11px;font-weight:800;letter-spacing:.1em;padding:4px 8px;border-radius:999px}
.pair .b{left:8px;background:#0D0D0B;color:#F2EEE6}.pair .a{left:calc(50% + 8px);background:var(--gold);color:#16150F}
.case h3{font-size:18px;line-height:1.4;margin:16px 18px 8px}
.case blockquote{margin:0 18px 12px;color:var(--muted);font-size:14.5px;border-left:2px solid var(--gold);padding-left:10px}
.case .meta{margin:auto 18px 16px;font-size:13.5px;color:var(--accent);font-weight:700}
.others{background:var(--alt)}
.olinks{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.olinks a{display:block;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px;text-decoration:none}
.olinks b{display:block;font-size:17px}.olinks span{font-size:13.5px;color:var(--muted)}
.home{text-align:center;margin-top:24px}.home a{color:var(--accent);font-weight:700}
footer{background:var(--night);color:#8E887B;font-size:14px;padding:30px 0;text-align:center}
.dock{position:fixed;left:0;right:0;bottom:0;z-index:6;background:rgba(13,13,11,.9);border-top:1px solid rgba(200,169,106,.25);padding:10px 16px;display:flex;gap:10px;justify-content:center}
.dock a{flex:1;max-width:280px;min-height:50px;font-size:16px}
@media(max-width:900px){.cases{grid-template-columns:1fr 1fr}.olinks{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.cases{grid-template-columns:1fr}.hero{padding:40px 0 36px}.items li{font-size:13px;padding:5px 10px}section{padding:48px 0}.btn{font-size:16px;padding:0 18px}}
"""

def page(cat, cases, cats):
    title = f"{cat['name']} | {cat['kw']} - 하우스랩 건설"
    desc = f"{cat['desc']} 경기 광주·성남·하남·용인·수원 정기 출장, 사진 상담·무료 견적. 실제 시공 사례 {len(cases)}건."
    url = f"{SITE}/service/{cat['slug']}.html"
    cards = []
    for p in cases:
        b = p["images"][0]
        a = p.get("after") or (p["images"][1] if len(p["images"]) > 1 else "")
        q = (p.get("quote") or "").strip()
        if len(q) > 90: q = q[:88].rsplit(" ", 1)[0] + "…"
        pair = (f'<div class="pair"><img src="../{e(b)}" alt="{e(p["title"])} 시공 전" loading="lazy"><img src="../{e(a)}" alt="{e(p["title"])} 시공 후" loading="lazy"><span class="t b">BEFORE</span><span class="t a">AFTER</span></div>'
                if a else f'<div class="pair" style="grid-template-columns:1fr"><img src="../{e(b)}" alt="{e(p["title"])} 현장" loading="lazy" style="aspect-ratio:2/1"></div>')
        cards.append(f'<a class="case" href="{e(p["url"])}" target="_blank" rel="noopener">{pair}<h3>{e(p["title"])}</h3>'
                     + (f"<blockquote>“{e(q)}”</blockquote>" if q else "")
                     + f'<span class="meta">{e(p.get("date",""))} · 블로그에서 작업 과정 보기 →</span></a>')
    others = "".join(f'<a href="{c["slug"]}.html"><b>{e(c["name"])}</b><span>{e(c["kw"])}</span></a>' for c in cats if c is not cat)
    items = "".join(f"<li>{e(i)}</li>" for i in cat["items"])
    ld = {"@context": "https://schema.org", "@type": "HomeAndConstructionBusiness", "name": "하우스랩 건설",
          "url": SITE, "telephone": TEL, "areaServed": ["서울", "경기", "인천"],
          "makesOffer": {"@type": "Offer", "itemOffered": {"@type": "Service", "name": cat["name"], "description": cat["desc"]}}}
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}">
{f'<meta property="og:image" content="{SITE}/{e(cases[0].get("after") or cases[0]["images"][0])}">' if cases else ''}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head><body>
<header><div class="wrap"><a class="logo" href="../">하우스랩 건설</a><a class="call" href="tel:{TEL_RAW}">전화하기</a></div></header>
<main>
<div class="hero"><div class="wrap">
<p class="crumb"><a href="../">홈</a> › 시공 분야 › {e(cat['name'])}</p>
<h1>{e(cat['name'])}<br><span>{e(cat['kw'])}</span></h1>
<p class="lead">{e(cat['desc'])} 경기 광주·성남·하남·용인·수원과 서울 송파·강동은 정기적으로 방문합니다.</p>
<ul class="items">{items}</ul>
<div class="btns"><a class="btn gold" href="tel:{TEL_RAW}">전화하기 {TEL}</a><a class="btn ghost" href="sms:{TEL_RAW}">무료견적 문자하기</a></div>
</div></div>
<section><div class="wrap">
<h2>{e(cat['name'])} 실제 시공 사례</h2>
<p class="sub">하우스랩 건설이 직접 시공하고 블로그에 기록한 현장 {len(cases)}건입니다.</p>
<div class="cases">{''.join(cards) if cards else '<p class="sub">시공 사례를 준비 중입니다. 사진과 함께 문의해 주세요.</p>'}</div>
</div></section>
<section class="others"><div class="wrap">
<h2>다른 시공 분야</h2><p class="sub">사진 상담 · 무료 견적 · 현장 직접 시공 · 전체 사진 1장 + 문제 부위 사진 1장</p>
<div class="olinks">{others}</div>
<p class="home"><a href="../">하우스랩 건설 홈으로 →</a></p>
</div></section>
</main>
<footer>하우스랩 건설 · 집수리·부분 인테리어 전문업체 · 경기 광주·성남·하남·용인·수원 정기 출장 · {TEL}</footer>
<div class="dock"><a class="btn ghost" href="sms:{TEL_RAW}">무료견적 문자하기</a><a class="btn gold" href="tel:{TEL_RAW}">전화하기</a></div>
</body></html>
"""

def main():
    posts = json.load(open("posts.json", encoding="utf-8"))["posts"]
    jobs = [p for p in posts if p.get("images")]
    os.makedirs("service", exist_ok=True)
    by = {c["slug"]: [] for c in CATS}
    for p in jobs:
        by[cat_of(p["title"])].append(p)
    for c in CATS:
        open(f"service/{c['slug']}.html", "w", encoding="utf-8").write(page(c, by[c["slug"]], CATS))
        print(c["slug"], len(by[c["slug"]]))
    today = time.strftime("%Y-%m-%d")
    urls = [f"{SITE}/"] + [f"{SITE}/service/{c['slug']}.html" for c in CATS]
    open("sitemap.xml", "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open("robots.txt", "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

if __name__ == "__main__":
    main()
