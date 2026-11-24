"""블로그 본문 텍스트에서 작업 기록 형식(지역, 작업 전, 작업 내용, 작업 완료, 마무리)을 뽑습니다.
본문에 있는 문장만 사용하고, 없는 내용은 비워 둡니다."""
import re

SKIP_STEP = re.compile(r"의뢰|전후 비교|하우스\s?랩|자주 묻는|견적|몰아보기|완료 및 마무리|마무리|달라진 점|현장 확인|목\s*차|읽어주셔서")
HEADS = re.compile(r"^(?:\d+\s*[.)]\s*)?(고객님의 의뢰 내용|작업 전후 비교|현장 확인.*|「작업 과정」|작업 과정|작업 전후 달라진 점|작업 완료 및 마무리|고객님들께서 자주 묻는 질문|하우스\s?랩 건설.*|작업 몰아보기|「목 차」)$")

END = re.compile(r".+?(?:습니다|었습니다|ㅂ니다|니다|[었였했됐있없된한진졌]다|요)(?:[.!]|(?=\s)|$)")

def split_sent(t):
    out, i = [], 0
    for m in END.finditer(t):
        out.append(m.group(0).strip()); i = m.end()
    rest = t[i:].strip()
    if rest and not out:
        out.append(rest)
    return [o for o in out if o]

def sentences(lines, n=2, limit=120):
    t = " ".join(lines)
    t = re.sub(r"\s+", " ", t).strip()
    parts = split_sent(t)
    out = ""
    for p in parts[:n]:
        p = p.strip().rstrip(".") + "."
        if len(out) + len(p) > limit and out:
            break
        out = (out + " " + p).strip()
    return out[:limit + 20]

def section(lines, name_re, start=0):
    """name_re 제목 다음 줄부터 다음 제목 전까지 (목차가 아닌 실제 본문 위치)."""
    idxs = [i for i, l in enumerate(lines) if re.match(r"^(?:\d+\s*[.)]\s*)?" + name_re + r"\s*$", l)]
    for i in idxs:
        body = []
        for l in lines[i + 1:]:
            if HEADS.match(l) or re.match(r"^\d+\s*[.)]\s*\S", l) and len(l) < 30 and body:
                break
            body.append(l)
        if len(body) >= 2:  # 목차 항목이면 바로 다음이 제목이라 비어 있음
            return body
    return []

def region_of(lines, title):
    for i, l in enumerate(lines):
        if re.match(r"^(?:\d+\s*[.)]\s*)?현장 확인", l):
            for m in lines[i + 1:i + 4]:
                g = re.match(r"^(서울(?:특별)?시?|경기도|인천(?:광역)?시?)\s+(\S+[시구군])(?:\s+(\S+[구]))?", m)
                if g:
                    a, b, c = g.groups()
                    a = "서울" if a.startswith("서울") else ("인천" if a.startswith("인천") else "경기")
                    return f"{a} {b}" + (f" {c}" if c and a == "경기" else "")
    return ""

def steps_of(lines):
    sec = section(lines, r"「?작업 과정」?")
    cand = sec if sec else lines
    out = []
    for l in cand:
        m = re.match(r"^\d+\s*[.)]\s*(.+)$", l)
        if m:
            s = m.group(1).strip()
            if not SKIP_STEP.search(s) and s not in out and len(s) <= 24:
                out.append(s)
        elif out and sec == []:
            # 목차는 번호 줄이 연속으로 나옴. 끊기면 그만
            if len(out) >= 3:
                break
    return out[:5]

def parse(body, title=""):
    lines = [l.strip() for l in (body or "").split("\n") if l.strip()]
    if lines and "se-main-container" in lines[0]:
        lines = lines[1:]
    before = section(lines, r"작업 전후 비교")
    done = section(lines, r"작업 전후 달라진 점") or section(lines, r"작업 완료 및 마무리")
    done = [l for l in done if not re.search(r"하우스\s?랩|읽어주셔서|감사합니다", l)]
    w = {
        "region": region_of(lines, title),
        "before": sentences(before, 2, 110) if before else "",
        "steps": steps_of(lines),
        "done": sentences(done, 2, 120) if done else "",
    }
    if done:
        # 마무리: 달라진 점의 마지막 문장
        t = re.sub(r"\s+", " ", " ".join(done)).strip()
        parts = split_sent(t)
        last = parts[-1].rstrip(".") + "." if parts else ""
        bad = (not last) or last.rstrip(".") in w["done"] or len(last) > 140 or (title and title[:8] in last)
        w["wrap"] = "" if bad else last
    else:
        w["wrap"] = ""
    return w
