#!/usr/bin/env python3
"""적용 사례 JSONL → 카드에 apply_links 기록 + 사례 페이지 대표 사진으로 image 교체(링크).
사용: python scripts/apply_links.py <apply.jsonl ...>
JSONL 한 줄 = {"id","apply":[{"title","url"}],"image_page":"url"}"""
import json, re, sys, urllib.parse, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fetch_images as F

SKIP = re.compile(r"sciencedirect|mdpi\.com|researchgate|springer|wiley|tandfonline|\.pdf($|\?)|wikipedia\.org|coupang|smartstore|aliexpress|alibaba|amazon\.|gmarket|11st", re.I)
CHEM = re.compile(r"skeletal|structure|formula|spacefill|molecule|diagram|schematic|chart|logo|favicon|icon|default|placeholder|share[-_]?image|og[-_]?default", re.I)


def og_image(url):
    page = F.get(url, timeout=15)
    for pat in (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)'):
        m = re.search(pat, page, re.I)
        if m:
            img = urllib.parse.urljoin(url, html.unescape(m.group(1)))
            if not CHEM.search(urllib.parse.unquote(img)):
                return img
    return ""


def main(files):
    by = {F.field(fm, "id"): (p, t) for p, t, fm in F.cards()}
    n_link = n_img = 0
    for f in files:
        for ln in Path(f).read_text().splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("id") not in by:
                continue
            p, t = by[r["id"]]
            apply = [a for a in r.get("apply") or [] if a.get("url") and not SKIP.search(a["url"])][:3]
            if not apply:
                continue
            block = "apply_links:\n" + "".join(f"  - {{title: {json.dumps(a.get('title',''), ensure_ascii=False)}, url: {json.dumps(a['url'])}}}\n" for a in apply)
            t = re.sub(r"^apply_links:\n(  - .*\n)*", "", t, flags=re.M)
            t = re.sub(r"^(updated:.*)$", lambda m: block + m.group(1), t, count=1, flags=re.M)
            p.write_text(t, encoding="utf-8"); n_link += 1
            pages = ([r["image_page"]] if r.get("image_page") and not SKIP.search(r["image_page"]) else []) + [a["url"] for a in apply]
            for u in dict.fromkeys(pages):
                img = og_image(u)
                if img:
                    old = F.field(re.match(r"^---\s*\n(.*?)\n---", t, re.S).group(1), "image")
                    if old and not old.startswith("http"):
                        (F.ROOT / old).unlink(missing_ok=True)
                    host = urllib.parse.urlparse(u).netloc.replace("www.", "")
                    F.set_image(p, t, img, f"적용 사례 사진 · {host} (원본 링크)", u)
                    n_img += 1
                    break
            by[r["id"]] = (p, p.read_text(encoding="utf-8"))
    print(f"적용 사례 링크 {n_link}장 · 사진 교체 {n_img}장")
    F.report()


if __name__ == "__main__":
    main(sys.argv[1:])
