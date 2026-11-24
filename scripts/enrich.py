"""posts.json 각 글에 작업 기록 형식(work), 짧은 작업명(job), 짧은 지역(area)을 붙입니다."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from parse_post import parse
from build_pages import cat_of

PREFIX = {"송파": "서울 송파", "강동": "서울 강동", "강남": "서울 강남", "서초": "서울 서초", "노원": "서울 노원", "중랑": "서울 중랑",
          "광진": "서울 광진", "성동": "서울 성동", "분당": "성남 분당", "성남": "성남", "용인": "용인", "하남": "하남", "수원": "수원",
          "경기광주": "경기 광주", "광주": "경기 광주", "이천": "이천", "인천": "인천"}

def short_area(region, title):
    if region:
        parts = region.split()
        if parts[0] == "서울":
            return "서울 " + re.sub(r"구$", "", parts[1])
        if parts[0] == "인천":
            return "인천 " + re.sub(r"[구군]$", "", parts[1])
        city = re.sub(r"시$|군$", "", parts[1])
        if city == "광주":
            city = "경기 광주"
        gu = re.sub(r"구$", "", parts[2]) if len(parts) > 2 else ""
        return (city + " " + gu).strip()
    for k, v in PREFIX.items():
        if title.startswith(k):
            return v
    return ""

def main(path="posts.json"):
    d = json.load(open(path, encoding="utf-8"))
    jobs = json.load(open("data/jobs.json", encoding="utf-8")) if os.path.exists("data/jobs.json") else {}
    for p in d["posts"]:
        w = parse(p.get("body", ""), p["title"])
        p["work"] = w
        p["area"] = short_area(w.get("region", ""), p["title"])
        p["job"] = jobs.get(p["id"], "")
        p["cat"] = cat_of(p["title"])
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("enriched", len(d["posts"]))

if __name__ == "__main__":
    main()
