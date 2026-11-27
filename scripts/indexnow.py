"""매일 사이트 주소를 네이버(IndexNow)와 Bing 등에 색인 요청한다.

sitemap.xml의 주소 중 최대 50개를 보낸다.
- 매일 보냄: 홈, 서비스 6개, 정기 출장 지역 7개, 최신 시공 사례 10개
- 나머지 칸: 남은 시공 사례와 지역 페이지를 날마다 돌아가며 채워 이틀이면 전부 한 번씩 보낸다
"""
import datetime, glob, json, os, re, sys, urllib.request, urllib.error

HOST = "psb-7.com"
LIMIT = 50
FIXED = 14       # PRIORITY 앞부분 (홈·서비스·정기 출장 지역)은 매일
NEW_WORK = 10    # 최신 시공 사례는 매일
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 많이 검색될 만한 순서 (앞일수록 먼저 보냄)
PRIORITY = [
    "/", "/service/bathroom.html", "/service/kitchen.html", "/service/repair.html",
    "/service/appliance.html", "/service/removal.html", "/service/etc.html",
    # 정기 출장 지역
    "/area/songpa.html", "/area/gangdong.html", "/area/hanam.html", "/area/seongnam.html",
    "/area/yongin.html", "/area/suwon.html", "/area/gwangju.html",
    # 인구·검색량 많은 지역
    "/area/gangnam.html", "/area/seocho.html", "/area/incheon.html", "/area/goyang.html",
    "/area/hwaseong.html", "/area/bucheon.html", "/area/namyangju.html", "/area/ansan.html",
    "/area/anyang.html", "/area/pyeongtaek.html", "/area/siheung.html", "/area/gimpo.html",
    "/area/mapo.html", "/area/nowon.html", "/area/gangseo.html", "/area/yeongdeungpo.html",
    "/area/gwangjin.html", "/area/seongdong.html", "/area/uijeongbu.html",
    "/area/gwangmyeong.html", "/area/guri.html", "/area/gunpo.html", "/area/osan.html",
    "/area/icheon.html", "/area/uiwang.html", "/area/gwacheon.html", "/area/yeoju.html",
    "/area/yangpyeong.html",
]


def key():
    for f in glob.glob(os.path.join(ROOT, "*.txt")):
        name = os.path.basename(f)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", name):
            return name
    sys.exit("IndexNow 키 파일이 없습니다")


def urls():
    xml = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    found = re.findall(r"<url>\s*<loc>\s*([^<\s]+)\s*</loc>(?:\s*<lastmod>([^<]*)</lastmod>)?", xml)
    date = {u: d for u, d in found if HOST in u}
    paths = {u.split(HOST, 1)[1] or "/": u for u in date}
    ordered = [paths.pop(p) for p in PRIORITY if p in paths]
    works = sorted((u for p, u in paths.items() if p.startswith("/work/")), key=lambda u: date[u], reverse=True)
    rest = [u for p, u in paths.items() if not p.startswith("/work/")]  # 새로 생긴 다른 페이지
    fixed = ordered[:FIXED] + works[:NEW_WORK]
    pool = rest + ordered[FIXED:] + works[NEW_WORK:]
    room = max(0, LIMIT - len(fixed))
    if len(pool) > room:
        start = (datetime.date.today().toordinal() * room) % len(pool)
        pool = (pool[start:] + pool[:start])[:room]
    return fixed + pool


def send(endpoint, body):
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode(errors="replace")[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:200]
    except Exception as e:
        return None, str(e)


def main():
    k = key()
    lst = urls()
    body = {"host": HOST, "key": k, "keyLocation": f"https://{HOST}/{k}.txt", "urlList": lst}
    print(f"보낼 주소 {len(lst)}개")
    for u in lst:
        print(" ", u)
    ok = False
    for name, ep in [("네이버", "https://searchadvisor.naver.com/indexnow"),
                     ("IndexNow(Bing 등)", "https://api.indexnow.org/indexnow")]:
        code, text = send(ep, body)
        print(f"{name}: {code} {text}")
        ok = ok or code in (200, 202)
    if not ok:
        sys.exit("색인 요청이 모두 실패했습니다")


if __name__ == "__main__":
    main()
