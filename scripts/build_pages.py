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
AREAS += [
    {"slug": "gangnam", "name": "서울 강남", "full": "서울특별시 강남구 (압구정·청담·대치·도곡·개포·역삼·삼성)", "match": r"^서울 강남", "other": r"강남구|압구정|청담|대치|도곡|개포|역삼|삼성동|수서|일원", "tier": "extra"},
    {"slug": "seocho", "name": "서울 서초", "full": "서울특별시 서초구 (반포·잠원·방배·서초·양재·내곡)", "match": r"^서울 서초", "other": r"서초|반포|잠원|방배|양재|내곡", "tier": "extra"},
    {"slug": "gwangjin", "name": "서울 광진", "full": "서울특별시 광진구 (자양·구의·광장·화양·중곡)", "match": r"^서울 광진", "other": r"광진|자양|구의|광장동|화양|중곡", "tier": "extra"},
    {"slug": "seongdong", "name": "서울 성동", "full": "서울특별시 성동구 (성수·옥수·금호·왕십리·행당)", "match": r"^서울 성동", "other": r"성동|성수|옥수|금호동|왕십리|행당", "tier": "extra"},
    {"slug": "mapo", "name": "서울 마포", "full": "서울특별시 마포구 (공덕·아현·상암·합정·망원)", "match": r"^서울 마포", "other": r"마포|공덕|아현|상암|합정|망원", "tier": "extra"},
    {"slug": "yeongdeungpo", "name": "서울 영등포", "full": "서울특별시 영등포구 (여의도·당산·문래·신길)", "match": r"^서울 영등포", "other": r"영등포|여의도|당산|문래|신길", "tier": "extra"},
    {"slug": "nowon", "name": "서울 노원", "full": "서울특별시 노원구 (상계·중계·하계·공릉·월계)", "match": r"^서울 노원", "other": r"노원|상계|중계|하계|공릉|월계", "tier": "extra"},
    {"slug": "gangseo", "name": "서울 강서", "full": "서울특별시 강서구 (마곡·화곡·등촌·가양·발산)", "match": r"^서울 강서", "other": r"강서구|마곡|화곡|등촌|가양|발산", "tier": "extra"},
    {"slug": "icheon", "name": "이천", "full": "경기도 이천시 (증포·안흥·중리·부발·마장)", "match": r"^이천", "other": r"이천|증포|안흥|부발|마장", "tier": "extra"},
    {"slug": "namyangju", "name": "남양주", "full": "경기도 남양주시 (다산·별내·와부·화도·진접·호평)", "match": r"^남양주", "other": r"남양주|다산|별내|와부|덕소|화도|진접|호평|평내", "tier": "extra"},
    {"slug": "guri", "name": "구리", "full": "경기도 구리시 (인창·교문·수택·갈매)", "match": r"^구리", "other": r"구리|인창|교문|수택|갈매", "tier": "extra"},
    {"slug": "yeoju", "name": "여주", "full": "경기도 여주시", "match": r"^여주", "other": r"여주", "tier": "extra"},
    {"slug": "yangpyeong", "name": "양평", "full": "경기도 양평군", "match": r"^양평", "other": r"양평", "tier": "extra"},
    {"slug": "anyang", "name": "안양", "full": "경기도 안양시 (평촌·범계·인덕원·만안)", "match": r"^안양", "other": r"안양|평촌|범계|인덕원|만안", "tier": "extra"},
    {"slug": "gwacheon", "name": "과천", "full": "경기도 과천시", "match": r"^과천", "other": r"과천", "tier": "extra"},
    {"slug": "uiwang", "name": "의왕", "full": "경기도 의왕시 (내손·포일·오전·백운)", "match": r"^의왕", "other": r"의왕|내손|포일", "tier": "extra"},
    {"slug": "gunpo", "name": "군포", "full": "경기도 군포시 (산본·금정·당동)", "match": r"^군포", "other": r"군포|산본", "tier": "extra"},
    {"slug": "hwaseong", "name": "화성", "full": "경기도 화성시 (동탄·병점·봉담·향남)", "match": r"^화성", "other": r"화성|동탄|병점|봉담|향남", "tier": "extra"},
    {"slug": "osan", "name": "오산", "full": "경기도 오산시 (세교·원동)", "match": r"^오산", "other": r"오산|세교", "tier": "extra"},
    {"slug": "pyeongtaek", "name": "평택", "full": "경기도 평택시 (고덕·소사벌·비전·송탄)", "match": r"^평택", "other": r"평택|소사벌|송탄", "tier": "extra"},
    {"slug": "gwangmyeong", "name": "광명", "full": "경기도 광명시 (철산·하안·소하·일직)", "match": r"^광명", "other": r"광명|철산|하안|소하", "tier": "extra"},
    {"slug": "bucheon", "name": "부천", "full": "경기도 부천시 (중동·상동·송내·옥길)", "match": r"^부천", "other": r"부천|상동|송내|옥길", "tier": "extra"},
    {"slug": "goyang", "name": "고양", "full": "경기도 고양시 (일산·삼송·원흥·화정·행신)", "match": r"^고양", "other": r"고양|일산|삼송|원흥|화정|행신", "tier": "extra"},
    {"slug": "gimpo", "name": "김포", "full": "경기도 김포시 (한강신도시·운양·장기·구래)", "match": r"^김포", "other": r"김포|운양|장기동|구래", "tier": "extra"},
    {"slug": "siheung", "name": "시흥", "full": "경기도 시흥시 (배곧·은계·정왕·목감)", "match": r"^시흥", "other": r"시흥|배곧|은계|정왕|목감", "tier": "extra"},
    {"slug": "ansan", "name": "안산", "full": "경기도 안산시 (고잔·초지·본오·상록)", "match": r"^안산", "other": r"안산|고잔|초지|본오|상록", "tier": "extra"},
    {"slug": "uijeongbu", "name": "의정부", "full": "경기도 의정부시 (민락·장암·신곡)", "match": r"^의정부", "other": r"의정부|민락|장암|신곡", "tier": "extra"},
    {"slug": "incheon", "name": "인천", "full": "인천광역시 (송도·청라·부평·검단·연수·남동)", "match": r"^인천", "other": r"인천|송도|청라|부평|검단|연수|남동구", "tier": "extra"},
]
CORE = [a for a in AREAS if a.get("tier") != "extra"]
EXTRA = [a for a in AREAS if a.get("tier") == "extra"]
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

SHOW_OTHER_BLOG = False  # ssus7777 글은 다른 상호(메이저)가 보여서 2026-11-24 요청으로 표시하지 않음

def other_posts(rx, limit=12):
    if not SHOW_OTHER_BLOG:
        return []
    try:
        allp = json.load(open("data/other_titles.json", encoding="utf-8"))
    except Exception:
        return []
    out = [p for p in allp if re.search(rx, p["title"])]
    return out[:limit]

e = lambda s: html.escape(str(s or ""), quote=True)

CSS = """
.price{padding:8px 0 48px}.price h2{font-size:26px;margin:0 0 6px}
.plist{list-style:none;margin:16px 0 0;padding:6px 22px;border-radius:18px;background:linear-gradient(165deg,#1B1A15,#0D0D0B 70%);border:1px solid rgba(200,169,106,.38);max-width:720px}
.plist li{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:14px 0;color:#E9E4D8;font-weight:600}
.plist li+li{border-top:1px solid rgba(244,239,228,.08)}
.plist small{display:block;font-size:12.5px;font-weight:500;color:#9D978B}
.plist b{white-space:nowrap;font-size:19px;font-weight:800;background:linear-gradient(180deg,#F3E3B8,#C8A96A 60%,#A8853F);-webkit-background-clip:text;background-clip:text;color:transparent}
.pnote{margin:12px 0 0;font-size:14px;color:var(--muted)}.pnote a{color:var(--accent);font-weight:700}
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
.xh{font-size:17px;margin:28px 0 4px}.xlinks{display:flex;flex-wrap:wrap;gap:8px}.xlinks a{padding:8px 13px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--ink);font-size:14px;text-decoration:none}.xlinks a:hover{border-color:var(--gold)}
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
.case h3 a{text-decoration:none}.case h3 a:hover{color:var(--accent)}
.ba{display:grid;grid-template-columns:1fr 1fr;gap:14px;max-width:960px;margin:0 auto}
.ba figure{margin:0;position:relative}.ba img{width:100%;aspect-ratio:4/5;object-fit:cover;border-radius:18px;display:block;background:var(--alt)}
.ba figcaption{position:absolute;top:12px;left:12px;font-size:12px;font-weight:800;letter-spacing:.1em;padding:5px 10px;border-radius:999px;background:#0D0D0B;color:#F2EEE6}
.ba figure+figure figcaption{background:var(--gold);color:#16150F}
.rec{max-width:760px;margin:0 auto}.rec h3{font-size:19px;margin:30px 0 8px;color:var(--accent)}.rec p{margin:0}
.rec ol{margin:0;padding-left:22px}.rec ol li{padding:3px 0}
.ask{margin:0;padding:16px 20px;border-radius:16px;background:var(--alt);border-left:3px solid var(--gold);font-size:16px}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:28px 0 0;padding:0;list-style:none}.facts li{font-size:14.5px;padding:7px 13px;border-radius:999px;border:1px solid var(--line);background:var(--surface)}
.facts a{color:var(--accent);font-weight:700;text-decoration:none}
.rec .blogl{margin-top:22px}.blogl a{color:var(--accent);font-weight:700}
@media(max-width:600px){.ba{gap:8px}.ba img{border-radius:12px}}
@media(max-width:900px){.cases{grid-template-columns:1fr 1fr}.olinks{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.cases{grid-template-columns:1fr}.hero{padding:40px 0 36px}.items li{font-size:13px;padding:5px 10px}section{padding:48px 0}.btn{font-size:16px;padding:0 18px}}
"""

# 작업별 참고 가격 (사장님이 준 금액 그대로, 2026-11-25). 바꿀 때는 index.html 가격표도 같이 바꾸기
P = {
    "base": ("기본 설치", "15만원부터", ""),
    "dish": ("식기세척기 설치", "20~30만원", "하부장 빼고 설치"),
    "lower": ("싱크대 하부장 제작", "35~45만원", ""),
    "marble": ("인조대리석 연마·광택", "30~80만원", ""),
    "film": ("문짝 필름 보수", "20~30만원", ""),
    "tub": ("욕조 코팅", "38~45만원", ""),
    "basin": ("세면대 코팅", "28~30만원", ""),
    "tile": ("타일 보수", "20만원부터", "1장 추가마다 8만원"),
    "grab": ("안전손잡이 설치", "25만원부터", "1개 추가마다 8만원"),
    "rack": ("건조기 렉 설치", "26~30만원", ""),
    "upper": ("세탁실 상부장 철거", "15~20만원", ""),
    "crack": ("크랙 복원", "20~65만원", ""),
    "paper": ("도배", "9~18만원", "소폭합지·광폭합지·실크 · 1평 기준"),
    "maru": ("마루", "11~15만원", "1평 기준"),
}
CAT_PRICES = {
    "kitchen": ["lower", "dish", "marble", "film", "crack"],
    "bathroom": ["tub", "basin", "tile", "grab"],
    "appliance": ["dish", "rack", "base"],
    "repair": ["film", "lower", "base"],
    "removal": ["upper", "crack", "tile"],
    "etc": ["paper", "maru", "grab", "base"],
}

def price_block(slug):
    keys = CAT_PRICES.get(slug, [])
    if not keys:
        return ""
    rows = "".join(f'<li><span>{e(P[k][0])}{f"<small>{e(P[k][2])}</small>" if P[k][2] else ""}</span><b>{e(P[k][1])}</b></li>' for k in keys)
    return (f'<section class="price"><div class="wrap"><h2>참고 가격</h2><p class="sub">자주 맡기시는 작업의 기준 가격입니다.</p>'
            f'<ul class="plist">{rows}</ul><p class="pnote">현장 상황, 작업 범위, 자재·제품에 따라 금액은 달라질 수 있습니다. '
            f'<a href="../#price">전체 가격표 보기 →</a></p></div></section>')

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
    return (f'<article class="case">{pair}<h3><a href="../work/{e(p["id"])}.html">{e(head)}</a></h3>' + (f'<dl class="work">{dl}</dl>' if dl else "")
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
    hubs = {"시공 분야": SITE + "/#services", "출장 지역": SITE + "/#area", "시공 사례": SITE + "/#cases"}
    trail = [("하우스랩건설", SITE + "/")] + [(n, url if i == len(names) - 1 else hubs.get(n)) for i, n in enumerate(names)]
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        dict({"@type": "ListItem", "position": i + 1, "name": n}, **({"item": u} if u else {})) for i, (n, u) in enumerate(trail)]}
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url, "description": desc,
          "inLanguage": "ko", "about": {"@type": "HomeAndConstructionBusiness", "@id": SITE + "/#business", "name": "하우스랩건설",
          "url": SITE + "/", "telephone": "+82-10-5931-7025"}}
    img = f"{SITE}/{og_img}" if og_img else f"{SITE}/og.jpg"
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="../apple-touch-icon.png"><meta name="theme-color" content="#0D0D0B"><link rel="manifest" href="../site.webmanifest">
<meta property="og:type" content="website"><meta property="og:site_name" content="하우스랩건설"><meta property="og:locale" content="ko_KR"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{e(img)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{e(img)}">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="{FONT}" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="{FONT}"></noscript>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head><body>
<header><div class="wrap"><a class="logo" href="../">하우스랩건설</a><a class="call" href="tel:{TEL_RAW}">전화하기</a></div></header>
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
<footer>하우스랩건설 · 집수리 및 종합 인테리어 · 경기 광주·성남·하남·용인·수원 및 서울·경기 출장 · {TEL}</footer>
<div class="dock"><a class="btn ghost" href="sms:{TEL_RAW}">무료견적 문자하기</a><a class="btn gold" href="tel:{TEL_RAW}">전화하기</a></div>
</body></html>
"""

def links_block(cur_cat=None, cur_area=None):
    cl = "".join(f'<a href="../service/{c["slug"]}.html"><b>{e(c["name"])}</b><span>{e(c["kw"])}</span></a>' for c in CATS if c is not cur_cat)
    al = "".join(f'<a href="../area/{a["slug"]}.html"><b>{e(a["name"])} 집수리</b><span>{e(a["full"].split(" (")[0])}</span></a>' for a in CORE if a is not cur_area)
    xl = "".join(f'<a href="../area/{a["slug"]}.html">{e(a["name"])}</a>' for a in EXTRA if a is not cur_area)
    return f"""<section class="others"><div class="wrap">
<h2>시공 분야</h2><p class="sub">사진 상담 · 무료 견적 · 직접 시공</p><div class="olinks">{cl}</div>
<h2 style="margin-top:40px">출장 지역</h2><p class="sub">정기적으로 방문하는 지역입니다</p><div class="olinks">{al}</div>
<h3 class="xh">그 밖의 출장 지역</h3><p class="sub">서울·경기·인천 어디든 일정과 작업 내용에 맞춰 방문합니다</p><div class="xlinks">{xl}</div>
<p class="home"><a href="../">하우스랩건설 홈으로 →</a></p>
</div></section>"""

def page(cat, cases, cats):
    title = f"{cat['name']} {cat['kw']} | 하우스랩건설 집수리"
    desc = f"{cat['desc']} 경기 광주·성남·하남·용인·수원 및 서울·경기 출장, 사진 무료 견적. 실제 시공 사례 {len(cases)}건."
    url = f"{SITE}/service/{cat['slug']}.html"
    items = '<ul class="items">' + "".join(f"<li>{e(i)}</li>" for i in cat["items"]) + "</ul>"
    oth = other_posts(cat["other"])
    body = f"""<section><div class="wrap">
<h2>{e(cat['name'])} 실제 시공 사례</h2>
<p class="sub">하우스랩건설이 직접 시공하고 블로그에 기록한 현장 {len(cases)}건입니다.</p>
<div class="cases">{''.join(card(p) for p in cases) if cases else '<p class="sub">사진이 있는 사례를 정리하고 있습니다. 궁금한 작업은 사진과 함께 문자로 문의해 주세요.</p>'}</div>
</div></section>
{price_block(cat["slug"])}
{f'<section class="blog"><div class="wrap"><h2>{e(cat["name"])} 블로그 작업 기록</h2><p class="sub">하우스랩건설 작업 블로그에 올린 {e(cat["name"])} 현장입니다.</p>{olist(oth)}</div></section>' if oth else ''}
{links_block(cur_cat=cat)}"""
    og = (cases[0].get("after") or cases[0]["images"][0]) if cases else ""
    return shell(title, desc, url, f"<a href=\"../#services\">시공 분야</a> › {e(cat['name'])}", f"{e(cat['name'])}<br><span>{e(cat['kw'])}</span>",
                 f"{e(cat['desc'])}", items, body, og)

def area_page(ar, cases, recent=()):
    oth = other_posts(ar["other"], 15)
    title = f"{ar['name']} 집수리 | 싱크대·욕실·가전 설치·철거 복원 - 하우스랩건설"
    desc = f"{ar['full']} 집수리 출장. 싱크대 수리, 욕실 보수, 가전 설치, 가구·문 수리, 철거 및 원상복구. {ar['name']} 실제 작업 사례와 사진 무료 견적."
    url = f"{SITE}/area/{ar['slug']}.html"
    if not cases:
        cases = recent[:3]
        h2, sub = "최근 시공 사례", f"{e(ar['name'])} 사례는 정리 중입니다. 가까운 지역에서 최근 직접 시공한 현장입니다."
    else:
        h2, sub = f"{e(ar['name'])} 실제 시공 사례", f"{e(ar['name'])}에서 직접 시공하고 사진으로 기록한 현장입니다."
    body = f"""<section><div class="wrap">
<h2>{h2}</h2>
<p class="sub">{sub}</p>
<div class="cases">{''.join(card(p) for p in cases)}</div>
</div></section>
{f'<section class="blog"><div class="wrap"><h2>{e(ar["name"])} 블로그 작업 기록</h2><p class="sub">하우스랩건설 작업 블로그에 올린 {e(ar["name"])} 현장 {len(oth)}건입니다.</p>{olist(oth)}</div></section>' if oth else ''}
{links_block(cur_area=ar)}"""
    og = (cases[0].get("after") or cases[0]["images"][0]) if cases else ""
    base = re.sub(r"[^가-힣]", "", ar['full'])[-1]
    josa = "은" if (ord(base) - 0xAC00) % 28 else "는"
    lead = f"{e(ar['full'])}{josa} 하우스랩건설이 {'일정과 작업 내용에 맞춰 출장하는' if ar.get('tier') == 'extra' else '정기적으로 방문하는'} 지역입니다. 전체 사진 1장과 문제 부위 사진 1장을 문자로 보내 주시면 무료로 견적을 안내해 드립니다."
    items = '<ul class="items">' + "".join(f'<li><a href="../service/{c["slug"]}.html">{e(c["name"])}</a></li>' for c in CATS) + "</ul>"
    return shell(title, desc, url, f"<a href=\"../#area\">출장 지역</a> › {e(ar['name'])}", f"{e(ar['name'])} 집수리<br><span>하우스랩건설</span>", lead, items, body, og)

def head_of(p):
    return (p.get("area", "") + " " + p["job"]).strip() if p.get("job") else p["title"]

def area_of(p):
    """글의 지역에 맞는 지역 페이지 (없으면 None)"""
    for a in AREAS:
        if re.search(a["match"], p.get("area", "")):
            return a
    return None

def work_page(p, same):
    """블로그 시공 글 하나를 '지역 + 작업명' 페이지로 만든다 (사진·작업 기록은 실제 글 내용 그대로)."""
    cat = next(c for c in CATS if c["slug"] == cat_of(p["title"]))
    ar = area_of(p)
    w = p.get("work") or {}
    head = head_of(p)
    region = w.get("region") or p.get("area", "")
    title = f"{head} | {cat['name']} 시공 사례 - 하우스랩건설"
    first = w.get("before") or p.get("quote") or cat["desc"]
    desc = f"{region + ' ' if region else ''}{p.get('job') or p['title']} 실제 시공 사례. {first}"[:150]
    url = f"{SITE}/work/{p['id']}.html"
    b = p["images"][0]
    a = p.get("after") or (p["images"][1] if len(p["images"]) > 1 else "")
    figs = f'<figure><img src="../{e(b)}" alt="{e(head)} 시공 전" decoding="async"><figcaption>{"BEFORE" if a else "현장"}</figcaption></figure>'
    if a:
        figs += f'<figure><img src="../{e(a)}" alt="{e(head)} 시공 후" loading="lazy" decoding="async"><figcaption>AFTER</figcaption></figure>'
    rec = ""
    if p.get("quote"):
        rec += f'<h3>고객 요청</h3><p class="ask">“{e(p["quote"])}”</p>'
    if w.get("before"):
        rec += f'<h3>작업 전 상태</h3><p>{e(w["before"])}</p>'
    if w.get("steps"):
        rec += "<h3>작업 과정</h3><ol>" + "".join(f"<li>{e(x)}</li>" for x in w["steps"]) + "</ol>"
    if w.get("done"):
        rec += f'<h3>작업 완료</h3><p>{e(w["done"])}</p>'
    if w.get("wrap"):
        rec += f'<h3>마무리 안내</h3><p>{e(w["wrap"])}</p>'
    facts = [f'<li>작업일 {e(p.get("date", ""))}</li>' if p.get("date") else "",
             f'<li>지역 {e(region)}</li>' if region else "",
             f'<li><a href="../service/{cat["slug"]}.html">{e(cat["name"])} 더 보기</a></li>',
             f'<li><a href="../area/{ar["slug"]}.html">{e(ar["name"])} 집수리</a></li>' if ar else ""]
    more = [x for x in same if x is not p][:3]
    body = f"""<section><div class="wrap">
<div class="ba">{figs}</div>
<div class="rec">{rec}
<ul class="facts">{''.join(facts)}</ul>
<p class="blogl"><a href="{e(p['url'])}" target="_blank" rel="noopener">블로그에서 사진 {e(p.get('nimg') or '')}장과 전체 과정 보기 →</a></p>
</div></div></section>
{price_block(cat["slug"])}
{f'<section><div class="wrap"><h2>다른 {e(cat["name"])} 사례</h2><p class="sub">하우스랩건설이 직접 시공한 비슷한 현장입니다.</p><div class="cases">{"".join(card(x) for x in more)}</div></div></section>' if more else ''}
{links_block(cur_cat=cat)}"""
    lead = f"{e(region)} 현장에서 하우스랩건설이 직접 시공한 기록입니다. 비슷한 문제가 있으시면 전체 사진 1장과 문제 부위 사진 1장을 문자로 보내 주세요." if region else "하우스랩건설이 직접 시공한 기록입니다. 비슷한 문제가 있으시면 사진을 문자로 보내 주세요."
    return shell(title, desc, url, f"<a href=\"../#cases\">시공 사례</a> › {e(head)}", e(head), lead, "", body, a or b)

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
        open(f"area/{ar['slug']}.html", "w", encoding="utf-8").write(area_page(ar, cs, jobs))
        print(ar["slug"], len(cs), len(other_posts(ar["other"], 15)))
    # 시공 글마다 페이지 (사진이 있는 실제 시공 글만)
    works = [p for p in posts if p.get("images")]
    os.makedirs("work", exist_ok=True)
    keep = set()
    for p in works:
        same = [x for x in works if cat_of(x["title"]) == cat_of(p["title"])]
        open(f"work/{p['id']}.html", "w", encoding="utf-8").write(work_page(p, same))
        keep.add(f"{p['id']}.html")
    for f in os.listdir("work"):
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join("work", f))
    print("work", len(works))
    today = time.strftime("%Y-%m-%d")
    urls = [(f"{SITE}/", today)] + [(f"{SITE}/service/{c['slug']}.html", today) for c in CATS] + [(f"{SITE}/area/{a['slug']}.html", today) for a in AREAS]
    urls += [(f"{SITE}/work/{p['id']}.html", p.get("date", today).replace(".", "-")) for p in works]
    open("sitemap.xml", "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")
    from email.utils import formatdate
    now = formatdate(usegmt=True)
    items = [(f"{c['name']} {c['kw']} | 하우스랩건설", f"{SITE}/service/{c['slug']}.html", c["desc"]) for c in CATS]
    items += [(f"{a['name']} 집수리 | 하우스랩건설", f"{SITE}/area/{a['slug']}.html", f"{a['full']} 집수리 출장. 싱크대 수리, 욕실 보수, 가전 설치, 가구·문 수리, 철거 및 원상복구. 사진 무료 견적.") for a in AREAS]
    items = [(f"{head_of(p)} | 하우스랩건설", f"{SITE}/work/{p['id']}.html", (p.get("work") or {}).get("before") or p.get("quote") or p["title"]) for p in works] + items
    open("rss.xml", "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
        f"<title>하우스랩건설</title><link>{SITE}/</link><description>하우스랩 집수리 및 종합 인테리어. 서울·경기·인천 집수리, 사진 무료 견적.</description><language>ko</language><lastBuildDate>{now}</lastBuildDate>\n"
        + "".join(f"<item><title>{e(t)}</title><link>{u}</link><guid>{u}</guid><description>{e(d)}</description><pubDate>{now}</pubDate></item>\n" for t, u, d in items)
        + "</channel></rss>\n")
    open("robots.txt", "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

if __name__ == "__main__":
    main()
