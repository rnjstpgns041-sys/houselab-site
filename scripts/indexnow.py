"""매일 사이트 주소를 네이버(IndexNow)와 Bing 등에 색인 요청한다.

sitemap.xml의 주소 중 사람들이 많이 찾을 만한 순서(홈 > 욕실·주방 등 서비스 > 주요 출장 지역 >
인구 많은 지역)로 최대 50개를 보낸다.
"""
import glob, json, os, re, sys, urllib.request, urllib.error

HOST = "psb-7.com"
LIMIT = 50
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
    found = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
    paths = {u.split(HOST, 1)[1] or "/": u for u in found if HOST in u}
    ordered = [paths.pop(p) for p in PRIORITY if p in paths]
    ordered += list(paths.values())  # 새로 생긴 페이지는 뒤에
    return ordered[:LIMIT]


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
