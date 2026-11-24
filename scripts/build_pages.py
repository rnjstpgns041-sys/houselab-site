"""posts.json을 읽어 시공 분야별 페이지(service/*.html), sitemap.xml, robots.txt를 만듭니다.
네이버·구글 검색이 분야별 페이지와 실제 시공 사례를 읽을 수 있도록 글 내용을 HTML에 그대로 넣습니다.
GitHub Actions에서 블로그 동기화 후 자동으로 실행됩니다."""
import html, json, os, re, time

SITE = "https://psb-7.com"
TEL = "010-5931-7025"
TEL_RAW = "01059317025"
FONT = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"

CATS = [
    {"slug": "kitchen", "name": "주방 수리", "kw": "싱크대·상판·수전",
     "desc": "싱크대 문짝·경첩, 상판 크랙, 싱크볼·수전 교체, 상부장·하부장 리폼까지 주방에서 필요한 부분만 정확하게 고칩니다.",
     "items": ["싱크대 문짝·경첩 수리", "상판 크랙·대리석 균열 보수", "싱크볼·수전 교체", "팝업 배수구 교체", "상부장·하부장 리폼", "냉장고장 높이 맞춤"],
     "other": r"싱크|상판|수전|주방|하부장|상부장|양념장|대리석"},
    {"slug": "bathroom", "name": "욕실 수리", "kw": "변기·세면대·타일",
     "desc": "흔들리는 변기 하부와 테두리 백시멘트, 세면대 누수·배관, 들뜬 타일 재부착, 실리콘 재시공까지 욕실의 고장 난 부분만 고칩니다.",
     "items": ["변기 하부·테두리 백시멘트", "세면대 누수·배관", "들뜬 벽타일 재부착", "아트월 타일 부분 교체", "실리콘 재시공", "환풍기 교체"],
     "other": r"변기|세면대|욕실|화장실|욕조|타일|백시멘|환풍기"},
    {"slug": "appliance", "name": "가전 설치", "kw": "인덕션·건조기",
     "desc": "인덕션·하이라이트·가스레인지 교체, 식기세척기 빌트인, 세탁기 위 건조기 설치까지. 자리가 안 맞으면 상판 가공과 공간 리폼으로 맞춰 설치합니다.",
     "items": ["인덕션·하이라이트 설치", "가스레인지 교체·매립", "식기세척기 빌트인 설치", "세탁기 위 건조기 설치", "건조기 렉·선반 제작", "빌트인 콤보 설치"],
     "other": r"인덕션|하이라이트|가스레인지|쿡탑|식기세척기|건조기|세탁기|콤보|오븐"},
    {"slug": "repair", "name": "가구·문 수리", "kw": "경첩·롤러·문짝",
     "desc": "싱크대·수납장 경첩, 붙박이장 롤러와 슬라이딩 도어, 문짝·문틀, 손잡이와 도어락처럼 매일 쓰는 가구와 문을 고칩니다.",
     "items": ["싱크대·수납장 경첩 교체", "붙박이장 롤러·슬라이딩 도어", "서랍·레일 수리", "문짝·문틀 교체", "손잡이·도어락", "베란다 수납장 제작"],
     "other": r"경첩|롤러|문짝|문틀|붙박이장|슬라이딩|도어|서랍|수납장|손잡이|방문"},
    {"slug": "removal", "name": "철거·복원", "kw": "TV 철거·벽면 복원",
     "desc": "아트월 TV 철거와 구멍 복원, 앙카볼트 제거와 벽면 복원, 상부장·오븐장·빌트인 냉장고 철거와 폐기, 이사 전 원상복구까지 진행합니다.",
     "items": ["아트월 TV 철거·구멍 복원", "벽걸이 TV 철거·원상복구", "앙카볼트 제거·벽면 복원", "상부장·냉장고장 철거", "빌트인 냉장고 철거·폐기", "이사 전 원상복구"],
     "other": r"철거|복원|원상복구|앙카|구멍|폐기"},
    {"slug": "etc", "name": "기타 집수리", "kw": "조명·마루·방수",
     "desc": "조명·콘센트 교체, 마루·장판·데코타일, 도배, 방수·실리콘, 몰딩·선반·커튼레일처럼 집 안 곳곳의 작은 수리도 합니다.",
     "items": ["조명·콘센트 교체", "마루·장판·데코타일", "도배", "방수·실리콘 보수", "몰딩·선반·커튼레일", "TV 거치대·베란다 보수"],
     "other": r"조명|콘센트|전기|마루|장판|데코타일|도배|방수|몰딩|커튼|선반|베란다|누수"},
]

AREAS = [
    {"slug": "gwangju", "name": "경기 광주", "full": "경기도 광주시", "match": r"^경기 광주", "other": r"경기\s?광주|광주시|오포|태전|능평|곤지암|초월|경안"},
    {"slug": "seongnam", "name": "성남", "full": "경기도 성남시 (분당·판교·수정·중원)", "match": r"^성남", "other": r"성남|분당|판교|정자동|서현|야탑|수내|중원구|수정구"},
    {"slug": "hanam", "name": "하남", "full": "경기도 하남시 (미사·감일·위례)", "match": r"^하남", "other": r"하남|미사|감일|덕풍|풍산"},
    {"slug": "yongin", "name": "용인", "full": "경기도 용인시 (수지·기흥·처인)", "match": r"^용인", "other": r"용인|수지|기흥|처인|죽전|동백|상현|동천|보정"},
    {"slug": "suwon", "name": "수원", "full": "경기도 수원시 (영통·광교·권선·팔달·장안)", "match": r"^수원", "other": r"수원|영통|광교|권선|팔달|망포|인계|장안구"},
    {"slug": "songpa", "name": "서울 송파", "full": "서울특별시 송파구 (잠실·가락·문정·오금·방이)", "match": r"^서울 송파", "other": r"송파|잠실|가락|문정|오금|방이|석촌|장지"},
    {"slug": "gangdong", "name": "서울 강동", "full": "서울특별시 강동구 (천호·명일·고덕·암사·성내·둔촌)", "match": r"^서울 강동", "other": r"강동|천호|명일|고덕|암사|성내|둔촌|길동|상일|강일"},
]
OTHER_BLOG = "ssus7777"

def cat_of(title):
    t = title
    if re.search(r"경첩|롤러|문짝|붙박이장|수납장|문 설치|도어락|손잡이", t) and not re.search(r"철거", t):
        return "repair"
    if re.search(r"식기세척기|가스레인지|하이라이트|인덕션|건조기|세탁기|콤보", t) and re.search(r"설치|교체|이동", t) and not re.search(r"철거 앙카|미니 세탁기 철거", t):
        return "appliance"
    if re.search(r"변기|욕실|화장실|세면대|욕조|타일|실리콘", t):
        return "bathroom"
    if re.search(r"철거|폐기|원상복구|앙카", t):
        return "removal"
    if re.search(r"싱크|상판|상부장|하부장|주방|대리석|냉장고장|양념장", t):
        return "kitchen"
    return "etc"

def other_posts(rx, limit=12):
    try:
        allp = json.load(open("data/other_titles.json", encoding="utf-8"))
    except Exception:
        return []
    out = [p for p in allp if re.search(rx, p["title"])]
    return out[:limit]

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
.case .meta{margin:auto 18px 16px;font-size:13.5px;color:var(--accent);font-weight:700;display:inline-block;padding:6px 0}
.others{background:var(--alt)}
.olinks{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.olinks a{display:block;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px;text-decoration:none}
.olinks b{display:block;font-size:17px}.olinks span{font-size:13.5px;color:var(--muted)}
.home{text-align:center;margin-top:24px}.home a{color:var(--accent);font-weight:700}
footer{background:var(--night);color:#8E887B;font-size:14px;padding:30px 0;text-align:center}
.dock{position:fixed;left:0;right:0;bottom:0;z-index:6;background:rgba(13,13,11,.9);border-top:1px solid rgba(200,169,106,.25);padding:10px 16px;display:flex;gap:10px;justify-content:center}
.dock a{flex:1;max-width:280px;min-height:50px;font-size:16px}
.work{margin:0 18px 12px;display:grid;gap:6px;font-size:14px;line-height:1.55}
.work div{display:grid;grid-template-columns:62px minmax(0,1fr);gap:8px}.work dt{font-weight:800;color:var(--accent);font-size:13px}.work dd{margin:0}
.case .meta{text-decoration:none}
.blog .olist{list-style:none;padding:0;margin:0 auto;max-width:820px;background:var(--surface);border:1px solid var(--line);border-radius:18px;overflow:hidden}
.olist li{display:flex;justify-content:space-between;gap:12px;padding:14px 18px;border-top:1px solid var(--line);font-size:15.5px}.olist li:first-child{border-top:0}
.olist a{text-decoration:none;font-weight:600}.olist span{flex:none;color:var(--muted);font-size:13px}
.items a{text-decoration:none}
@media(max-width:900px){.cases{grid-template-columns:1fr 1fr}.olinks{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.cases{grid-template-columns:1fr}.hero{padding:40px 0 36px}.items li{font-size:13px;padding:5px 10px}section{padding:48px 0}.btn{font-size:16px;padding:0 18px}}
"""

def th(src):
    """가벼운 미리보기(images/t/*.webp)가 있으면 그것을 쓴다."""
    m = re.match(r"images/([^/]+)\.jpg$", src or "")
    if m and os.path.exists(f"images/t/{m.group(1)}.webp"):
        return f"images/t/{m.group(1)}.webp"
    return src

def card(p):
    b = p["images"][0]
    a = p.get("after") or (p["images"][1] if len(p["images"]) > 1 else "")
    head = (p.get("area", "") + " " + p["job"]).strip() if p.get("job") else p["title"]
    w = p.get("work") or {}
    rows = [("작업 전", w.get("before") or ("“" + p["quote"] + "”" if p.get("quote") else "")),
            ("작업 내용", " → ".join(w.get("steps") or [])),
            ("작업 완료", w.get("done", "")), ("마무리", w.get("wrap", ""))]
    dl = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in rows if v)
    pair = (f'<div class="pair"><img src="../{e(th(b))}" alt="{e(head)} 시공 전" loading="lazy" decoding="async"><img src="../{e(th(a))}" alt="{e(head)} 시공 후" loading="lazy" decoding="async"><span class="t b">BEFORE</span><span class="t a">AFTER</span></div>'
            if a else f'<div class="pair" style="grid-template-columns:1fr"><img src="../{e(th(b))}" alt="{e(head)} 현장" loading="lazy" decoding="async" style="aspect-ratio:2/1"></div>')
    return (f'<article class="case">{pair}<h3>{e(head)}</h3>' + (f'<dl class="work">{dl}</dl>' if dl else "")
            + f'<a class="meta" href="{e(p["url"])}" target="_blank" rel="noopener">{e(p.get("date",""))} · 블로그에서 전체 과정 보기 →</a></article>')

def olist(items):
    if not items:
        return ""
    lis = "".join(f'<li><a href="https://blog.naver.com/{OTHER_BLOG}/{e(o["id"])}" target="_blank" rel="noopener">{e(o["title"])}</a>'
                  + (f'<span>{e(o["date"])}</span>' if re.match(r"\d{4}\.", o.get("date", "")) else "") + "</li>" for o in items)
    return f'<ul class="olist">{lis}</ul>'

def shell(title, desc, url, crumb, h1, lead, items_html, body, og_img=""):
    # 경로 표시(홈 › 시공 분야 › 주방 수리)를 검색에도 알려 준다
    names = [re.sub(r"<[^>]+>", "", x).strip() for x in crumb.split("›")]
    hubs = {"시공 분야": SITE + "/#services", "출장 지역": SITE + "/#area"}
    trail = [("하우스랩 건설", SITE + "/")] + [(n, url if i == len(names) - 1 else hubs.get(n)) for i, n in enumerate(names)]
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        dict({"@type": "ListItem", "position": i + 1, "name": n}, **({"item": u} if u else {})) for i, (n, u) in enumerate(trail)]}
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url, "description": desc,
          "inLanguage": "ko", "about": {"@type": "HomeAndConstructionBusiness", "@id": SITE + "/#business", "name": "하우스랩 건설",
          "url": SITE + "/", "telephone": "+82-10-5931-7025"}}
    img = f"{SITE}/{og_img}" if og_img else f"{SITE}/og.jpg"
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="../apple-touch-icon.png"><meta name="theme-color" content="#0D0D0B">
<meta property="og:type" content="website"><meta property="og:site_name" content="하우스랩 건설"><meta property="og:locale" content="ko_KR"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{e(img)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{e(img)}">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="{FONT}" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="{FONT}"></noscript>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head><body>
<header><div class="wrap"><a class="logo" href="../">하우스랩 건설</a><a class="call" href="tel:{TEL_RAW}">전화하기</a></div></header>
<main>
<div class="hero"><div class="wrap">
<p class="crumb"><a href="../">홈</a> › {crumb}</p>
<h1>{h1}</h1>
<p class="lead">{lead}</p>
{items_html}
<div class="btns"><a class="btn gold" href="tel:{TEL_RAW}">전화 상담 {TEL}</a><a class="btn ghost" href="sms:{TEL_RAW}">무료 사진 견적 문자</a></div>
</div></div>
{body}
</main>
<footer>하우스랩 건설 · 집수리·부분 인테리어 전문 · 경기 광주·성남·하남·용인·수원 및 서울·경기 출장 · {TEL}</footer>
<div class="dock"><a class="btn ghost" href="sms:{TEL_RAW}">무료견적 문자하기</a><a class="btn gold" href="tel:{TEL_RAW}">전화하기</a></div>
</body></html>
"""

def links_block(cur_cat=None, cur_area=None):
    cl = "".join(f'<a href="../service/{c["slug"]}.html"><b>{e(c["name"])}</b><span>{e(c["kw"])}</span></a>' for c in CATS if c is not cur_cat)
    al = "".join(f'<a href="../area/{a["slug"]}.html"><b>{e(a["name"])} 집수리</b><span>{e(a["full"].split(" (")[0])}</span></a>' for a in AREAS if a is not cur_area)
    return f"""<section class="others"><div class="wrap">
<h2>시공 분야</h2><p class="sub">사진 상담 · 무료 견적 · 직접 시공</p><div class="olinks">{cl}</div>
<h2 style="margin-top:40px">출장 지역</h2><p class="sub">정기적으로 방문하는 지역입니다</p><div class="olinks">{al}</div>
<p class="home"><a href="../">하우스랩 건설 홈으로 →</a></p>
</div></section>"""

def page(cat, cases, cats):
    title = f"{cat['name']} {cat['kw']} | 하우스랩 건설 집수리"
    desc = f"{cat['desc']} 경기 광주·성남·하남·용인·수원 및 서울·경기 출장, 사진 무료 견적. 실제 시공 사례 {len(cases)}건."
    url = f"{SITE}/service/{cat['slug']}.html"
    items = '<ul class="items">' + "".join(f"<li>{e(i)}</li>" for i in cat["items"]) + "</ul>"
    oth = other_posts(cat["other"])
    body = f"""<section><div class="wrap">
<h2>{e(cat['name'])} 실제 시공 사례</h2>
<p class="sub">하우스랩 건설이 직접 시공하고 블로그에 기록한 현장 {len(cases)}건입니다.</p>
<div class="cases">{''.join(card(p) for p in cases) if cases else '<p class="sub">사진이 있는 사례를 정리하고 있습니다. 아래 블로그 작업 기록을 참고해 주세요.</p>'}</div>
</div></section>
{f'<section class="blog"><div class="wrap"><h2>{e(cat["name"])} 블로그 작업 기록</h2><p class="sub">하우스랩 건설 작업 블로그에 올린 {e(cat["name"])} 현장입니다.</p>{olist(oth)}</div></section>' if oth else ''}
{links_block(cur_cat=cat)}"""
    og = (cases[0].get("after") or cases[0]["images"][0]) if cases else ""
    return shell(title, desc, url, f"<a href=\"../#services\">시공 분야</a> › {e(cat['name'])}", f"{e(cat['name'])}<br><span>{e(cat['kw'])}</span>",
                 f"{e(cat['desc'])}", items, body, og)

def area_page(ar, cases):
    oth = other_posts(ar["other"], 15)
    title = f"{ar['name']} 집수리 | 싱크대·욕실·가전 설치·철거 복원 - 하우스랩 건설"
    desc = f"{ar['full']} 집수리 출장. 싱크대 수리, 욕실 보수, 가전 설치, 가구·문 수리, 철거 및 원상복구. {ar['name']} 실제 작업 사례와 사진 무료 견적."
    url = f"{SITE}/area/{ar['slug']}.html"
    body = f"""<section><div class="wrap">
<h2>{e(ar['name'])} 실제 시공 사례</h2>
<p class="sub">{e(ar['name'])}에서 직접 시공하고 사진으로 기록한 현장입니다.</p>
<div class="cases">{''.join(card(p) for p in cases) if cases else ''}</div>
{'' if cases else '<p class="sub">사진 사례는 아래 블로그 작업 기록에서 볼 수 있습니다.</p>'}
</div></section>
{f'<section class="blog"><div class="wrap"><h2>{e(ar["name"])} 블로그 작업 기록</h2><p class="sub">하우스랩 건설 작업 블로그에 올린 {e(ar["name"])} 현장 {len(oth)}건입니다.</p>{olist(oth)}</div></section>' if oth else ''}
{links_block(cur_area=ar)}"""
    og = (cases[0].get("after") or cases[0]["images"][0]) if cases else ""
    lead = f"{e(ar['full'])}은 하우스랩 건설이 정기적으로 방문하는 지역입니다. 전체 사진 1장과 문제 부위 사진 1장을 문자로 보내 주시면 무료로 견적을 안내해 드립니다."
    items = '<ul class="items">' + "".join(f'<li><a href="../service/{c["slug"]}.html">{e(c["name"])}</a></li>' for c in CATS) + "</ul>"
    return shell(title, desc, url, f"<a href=\"../#area\">출장 지역</a> › {e(ar['name'])}", f"{e(ar['name'])} 집수리<br><span>하우스랩 건설</span>", lead, items, body, og)

def main():
    posts = json.load(open("posts.json", encoding="utf-8"))["posts"]
    jobs = [p for p in posts if p.get("images") and p.get("quote")]
    os.makedirs("service", exist_ok=True); os.makedirs("area", exist_ok=True)
    by = {c["slug"]: [] for c in CATS}
    for p in jobs:
        by[cat_of(p["title"])].append(p)
    for c in CATS:
        open(f"service/{c['slug']}.html", "w", encoding="utf-8").write(page(c, by[c["slug"]], CATS))
        print(c["slug"], len(by[c["slug"]]))
    for ar in AREAS:
        cs = [p for p in jobs if re.search(ar["match"], p.get("area", ""))]
        open(f"area/{ar['slug']}.html", "w", encoding="utf-8").write(area_page(ar, cs))
        print(ar["slug"], len(cs), len(other_posts(ar["other"], 15)))
    today = time.strftime("%Y-%m-%d")
    urls = [f"{SITE}/"] + [f"{SITE}/service/{c['slug']}.html" for c in CATS] + [f"{SITE}/area/{a['slug']}.html" for a in AREAS]
    open("sitemap.xml", "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open("robots.txt", "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

if __name__ == "__main__":
    main()
