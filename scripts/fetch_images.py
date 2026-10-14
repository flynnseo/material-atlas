#!/usr/bin/env python3
"""카드 대표 이미지 수집 (LLM 없이 스크립트로).

  python scripts/fetch_images.py wiki    # A: 카드 sources 의 Wikipedia 문서 대표 이미지(커먼즈 자유 라이선스만) → assets/img/<id>.jpg 저장
  python scripts/fetch_images.py og      # B: 신소재·사례 카드의 출처 페이지 og:image → 주소만 기록(핫링크, 저장 안 함)
  python scripts/fetch_images.py report  # 이미지 있는/없는 카드 수

카드 프론트매터에 image / image_credit / image_source 를 쓴다. 이미 image 가 있으면 건너뜀(--force 로 덮어쓰기).
"""
import json, re, sys, subprocess, urllib.parse, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
UA = "MaterialAtlas/1.0 (personal wiki; https://github.com/flynnseo/material-atlas)"
BAD = re.compile(r"logo|favicon|icon|sprite|placeholder|default|avatar|banner-ad|\.svg($|\?)", re.I)


def cards():
    for p in sorted(list((ROOT / "materials").rglob("*.md")) + list((ROOT / "finishes").glob("*.md")) + list((ROOT / "cases").glob("*.md"))):
        t = p.read_text(encoding="utf-8")
        m = FM.match(t)
        if m:
            yield p, t, m.group(1)


def field(fm, k):
    m = re.search(rf"^{k}:\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip('"') if m else ""


def sources(fm):
    return re.findall(r"^  - (https?://\S+)", fm, re.M) + ([field(fm, "discovered_via")] if field(fm, "discovered_via") else [])


def get(url, binary=False, timeout=20):
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, url], capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "ignore")


def set_image(path, text, image, credit, source):
    def q(s): return json.dumps(s, ensure_ascii=False)
    text = re.sub(r"^(image|image_credit|image_source):.*\n", "", text, flags=re.M)
    text = re.sub(r"^(updated:.*)$", lambda m: f"image: {q(image)}\nimage_credit: {q(credit)}\nimage_source: {q(source)}\n" + m.group(1), text, count=1, flags=re.M)
    path.write_text(text, encoding="utf-8")


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def wiki(force):
    IMG.mkdir(parents=True, exist_ok=True)
    done = skip = none = 0
    for p, t, fm in cards():
        if field(fm, "image") and not force:
            skip += 1; continue
        cid = field(fm, "id")
        wikis = [u for u in sources(fm) if re.match(r"https?://(en|ko)\.wikipedia\.org/wiki/", u)]
        got = False
        for u in wikis:
            lang = u.split("//")[1][:2]
            title = urllib.parse.unquote(u.split("/wiki/", 1)[1].split("#")[0])
            api = f"https://{lang}.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&piprop=thumbnail|name&pithumbsize=640&pilicense=free&redirects=1&titles=" + urllib.parse.quote(title)
            try:
                pages = json.loads(get(api))["query"]["pages"]
            except Exception:
                continue
            pg = next(iter(pages.values()))
            th, name = (pg.get("thumbnail") or {}).get("source"), pg.get("pageimage")
            if not th or not name or BAD.search(name):
                continue
            meta = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=extmetadata&titles=File:" + urllib.parse.quote(name)
            try:
                info = next(iter(json.loads(get(meta))["query"]["pages"].values()))["imageinfo"][0]["extmetadata"]
            except Exception:
                continue  # 커먼즈에 없음 = 로컬(비자유) 파일일 수 있으니 건너뜀
            lic = (info.get("LicenseShortName") or {}).get("value", "")
            if not lic or re.search(r"fair use|non-free", lic, re.I):
                continue
            artist = strip_tags((info.get("Artist") or {}).get("value", ""))[:80]
            ext = ".png" if th.lower().endswith(".png") else ".jpg"
            data = get(th, binary=True)
            if len(data) < 3000:
                continue
            out = IMG / f"{cid}{ext}"
            out.write_bytes(data)
            set_image(p, t, f"assets/img/{out.name}", f"{artist or '작자 미상'} · {lic} · Wikimedia Commons",
                      f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(name)}")
            done += 1; got = True
            break
        if not got:
            none += 1
    print(f"A(wiki): 저장 {done} · 이미 있음 {skip} · 못 찾음 {none}")


def og(force):
    done = skip = none = 0
    for p, t, fm in cards():
        if field(fm, "image") and not force:
            skip += 1; continue
        if not (re.search(r"^novelty: emerging", fm, re.M) or p.parent.name == "cases"):
            continue
        got = False
        for u in sources(fm):
            if "wikipedia.org" in u:
                continue
            page = get(u, timeout=15)
            m = (re.search(r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)', page, re.I)
                 or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page, re.I)
                 or re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)', page, re.I))
            if not m:
                continue
            img = html.unescape(m.group(1))
            img = urllib.parse.urljoin(u, img)
            if BAD.search(img):
                continue
            host = urllib.parse.urlparse(u).netloc.replace("www.", "")
            set_image(p, t, img, f"출처 페이지 대표 이미지 · {host} (원본 링크)", u)
            done += 1; got = True
            break
        if not got:
            none += 1
    print(f"B(og): 기록 {done} · 이미 있음 {skip} · 못 찾음 {none}")


def report():
    have = {"local": 0, "link": 0}; miss = []
    for p, t, fm in cards():
        im = field(fm, "image")
        if not im: miss.append(field(fm, "id"))
        elif im.startswith("http"): have["link"] += 1
        else: have["local"] += 1
    print(f"저장 {have['local']} · 링크 {have['link']} · 없음 {len(miss)}")
    return miss


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    force = "--force" in sys.argv
    {"wiki": lambda: wiki(force), "og": lambda: og(force), "report": report}[cmd]()


def commons_search(cid, query, must):
    """커먼즈 파일 검색으로 대체 이미지: 파일명에 must(정규식)가 있어야 채택. 자유 라이선스만."""
    p, t, fm = next(x for x in cards() if field(x[2], "id") == cid)
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=12"
           "&prop=imageinfo&iiprop=url|extmetadata|mime&iiurlwidth=640&gsrsearch=" + urllib.parse.quote(query))
    try:
        pages = sorted(json.loads(get(api))["query"]["pages"].values(), key=lambda x: x.get("index", 99))
    except Exception:
        return False
    for pg in pages:
        name = pg["title"].split(":", 1)[1]
        ii = (pg.get("imageinfo") or [{}])[0]
        if not re.search(must, name, re.I) or BAD.search(name) or "jpeg" not in ii.get("mime", "") and "png" not in ii.get("mime", ""):
            continue
        meta = ii.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        if not lic or re.search(r"fair use|non-free", lic, re.I):
            continue
        data = get(ii["thumburl"], binary=True)
        if len(data) < 3000:
            continue
        out = IMG / f"{cid}.jpg"
        out.write_bytes(data)
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "70", "-Z", "480", str(out)], capture_output=True)
        artist = strip_tags((meta.get("Artist") or {}).get("value", ""))[:80]
        set_image(p, t, f"assets/img/{out.name}", f"{artist or '작자 미상'} · {lic} · Wikimedia Commons",
                  "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(pg["title"]))
        print(f"  ✓ {cid} ← {name[:60]}")
        return True
    print(f"  ✗ {cid} ({query})")
    return False


def clear_image(cid):
    p, t, fm = next(x for x in cards() if field(x[2], "id") == cid)
    p.write_text(re.sub(r"^(image|image_credit|image_source):.*\n", "", t, flags=re.M), encoding="utf-8")
    for f in IMG.glob(f"{cid}.*"):
        f.unlink()
