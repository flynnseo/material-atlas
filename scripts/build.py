#!/usr/bin/env python3
"""MATERIAL ATLAS 빌드: 카드(.md) → 검사 → site/index.json + site/index.html

사용법
  python scripts/build.py            # 검사 + 빌드 (오류 있으면 실패)
  python scripts/build.py --audit    # 빌드 없이 품질 리포트만
  python scripts/build.py --test     # 빌드 후 검색 테스트(_meta/search_tests.json) 실행 (Node 필요)
"""
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML 필요: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "_meta"
SITE = ROOT / "site"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)
WIKILINK_RE = re.compile(r"\[\[([A-Z]+-[A-Za-z0-9\-]+)(?:\|([^\]]+))?\]\]")


def load_yaml(p):
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


# ---------- 마크다운(최소) → HTML ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = WIKILINK_RE.sub(lambda m: f'<a href="#{m.group(1)}" class="wl">{m.group(2) or m.group(1)}</a>', s)
    return s


def md_to_html(md):
    out, lst = [], None
    for line in md.splitlines():
        st = line.strip()
        m_ul = re.match(r"^[-*]\s+(.*)", st)
        m_ol = re.match(r"^\d+[.)]\s+(.*)", st)
        kind = "ul" if m_ul else "ol" if m_ol else None
        if lst and kind != lst:
            out.append(f"</{lst}>")
            lst = None
        if kind:
            if not lst:
                out.append(f"<{kind}>")
                lst = kind
            out.append(f"<li>{inline((m_ul or m_ol).group(1))}</li>")
        elif st.startswith("#"):
            lvl = min(len(st) - len(st.lstrip("#")) + 1, 5)
            out.append(f"<h{lvl}>{inline(st.lstrip('#').strip())}</h{lvl}>")
        elif st.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", st):
            cells = [inline(c.strip()) for c in st.strip("|").split("|")]
            out.append("<div class='tr'>" + "".join(f"<span>{c}</span>" for c in cells) + "</div>")
        elif st and not re.match(r"^\|[\s\-:|]+\|$", st):
            out.append(f"<p>{inline(st)}</p>")
    if lst:
        out.append(f"</{lst}>")
    return "\n".join(out)


def plain(md):
    t = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), md)
    t = re.sub(r"[#*`|>\-\[\]()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:3000]


# ---------- 로딩 ----------
def load_cards(schema):
    cards, errors = [], []
    for tname, t in schema["types"].items():
        folder = ROOT / t["folder"]
        if not folder.exists():
            continue
        for p in sorted(folder.rglob("*.md")):
            if p.name.startswith("_") or "_templates" in p.parts:
                continue
            raw = p.read_text(encoding="utf-8")
            m = FM_RE.match(raw)
            rel = p.relative_to(ROOT).as_posix()
            if not m:
                errors.append(f"{rel}: 프론트매터(---) 없음")
                continue
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError as e:
                errors.append(f"{rel}: YAML 오류 {e}")
                continue
            fm["_type"], fm["_path"], fm["_body"] = tname, rel, m.group(2)
            cards.append(fm)
    return cards, errors


def validate(cards, schema, vocab):
    errors, warns = [], []
    ids = {}
    for c in cards:
        t = schema["types"][c["_type"]]
        where = c["_path"]
        for f in t["required"]:
            if c.get(f) in (None, "", []):
                errors.append(f"{where}: 필수 필드 '{f}' 비어 있음")
        cid = str(c.get("id", ""))
        if cid and not cid.startswith(t["id_prefix"]):
            errors.append(f"{where}: id '{cid}'는 {t['id_prefix']}로 시작해야 함")
        if cid in ids:
            errors.append(f"{where}: id 중복 ({ids[cid]})")
        ids[cid] = where
        for field, enum in schema["enums"].items():
            v = c.get(field)
            if v not in (None, "") and str(v) not in [str(x) for x in enum]:
                errors.append(f"{where}: {field}='{v}' 허용값 {enum}")
        allowed_known = set()
        for axis in vocab.values():
            allowed_known |= set(axis.keys())
        for field, axis in schema["tag_fields"].items():
            for v in as_list(c.get(field)):
                if v not in vocab.get(axis, {}):
                    warns.append(f"{where}: {field} 태그 '{v}'가 vocab.yaml에 없음")
    # 링크 대상 존재 확인
    for c in cards:
        for f in schema["link_fields"]:
            for v in as_list(c.get(f)):
                if isinstance(v, str) and re.match(r"^[A-Z]+-", v) and v not in ids:
                    warns.append(f"{c['_path']}: {f} → '{v}' 카드 없음 (만들 대상)")
        for m in WIKILINK_RE.finditer(c["_body"]):
            if m.group(1) not in ids:
                warns.append(f"{c['_path']}: 본문 [[{m.group(1)}]] 카드 없음")
    return errors, warns


def audit(cards):
    rep = {"C등급(검증 필요)": [], "출처 없음": [], "draft": [], "사례 없음(소재)": [], "hands_on": []}
    for c in cards:
        cid = c.get("id")
        if c.get("confidence") == "C":
            rep["C등급(검증 필요)"].append(cid)
        if c["_type"] in ("material", "finish") and not c.get("sources"):
            rep["출처 없음"].append(cid)
        if c.get("status") == "draft":
            rep["draft"].append(cid)
        if c["_type"] == "material" and not c.get("cases") and not c.get("_backlink_cases"):
            rep["사례 없음(소재)"].append(cid)
        if c.get("hands_on"):
            rep["hands_on"].append(cid)
    return rep


# ---------- 인덱스 ----------
def build_index(cards, schema, vocab):
    known = {str(c["id"]) for c in cards if c.get("id")}
    all_tags = {}
    for axis in vocab.values():
        all_tags.update(axis)

    docs = []
    for c in cards:
        cid = str(c["id"])
        tags = set()
        for f in schema["tag_fields"]:
            tags |= {str(v) for v in as_list(c.get(f))}
        io = c.get("properties", {}) or {}
        io = io.get("indoor_outdoor") if isinstance(io, dict) else None
        if io in ("both", "indoor"):
            tags.add("indoor")
        if io in ("both", "outdoor"):
            tags.add("outdoor")
        if c.get("novelty"):
            tags.add(str(c["novelty"]))
        links = []
        for f in schema["link_fields"]:
            for v in as_list(c.get(f)):
                v = str(v)
                if v in known:
                    links.append(v)
                elif v in all_tags:
                    tags.add(v)  # applies_to: metal 같은 태그형 값
        links += [m.group(1) for m in WIKILINK_RE.finditer(c["_body"]) if m.group(1) in known]
        links = list(dict.fromkeys(x for x in links if x != cid))
        props = c.get("properties") or {}
        docs.append({
            "id": cid,
            "type": c["_type"],
            "name_ko": c.get("name_ko", ""),
            "name_en": c.get("name_en", ""),
            "aliases": [str(a) for a in as_list(c.get("aliases"))],
            "family": c.get("family", ""),
            "subfamily": c.get("subfamily", ""),
            "brand": c.get("brand", ""),
            "tags": sorted(tags),
            "links": links,
            "confidence": c.get("confidence", ""),
            "status": c.get("status", ""),
            "hands_on": bool(c.get("hands_on")),
            "sample": bool(c.get("sample")),
            "cost_tier": c.get("cost_tier"),
            "lead_time": c.get("lead_time", ""),
            "props": props if isinstance(props, dict) else {},
            "sources": [str(s) for s in as_list(c.get("sources"))],
            "updated": str(c.get("updated", "")),
            "path": c["_path"],
            "html": md_to_html(c["_body"]),
            "text": plain(c["_body"]),
        })

    by = {d["id"]: d for d in docs}
    for d in docs:
        d["backlinks"] = []
    for d in docs:
        for l in d["links"]:
            if d["id"] not in by[l]["backlinks"]:
                by[l]["backlinks"].append(d["id"])
    # 유사 카드: 태그 Jaccard 상위 6 (직접 링크 제외)
    for d in docs:
        a = set(d["tags"])
        cand = []
        for e in docs:
            if e is d or e["id"] in d["links"] or e["id"] in d["backlinks"]:
                continue
            b = set(e["tags"])
            if not a or not b:
                continue
            j = len(a & b) / len(a | b)
            if j >= 0.2:
                cand.append((j, e["id"]))
        d["related"] = [i for _, i in sorted(cand, reverse=True)[:6]]

    synonyms, labels = [], {}
    for axis, terms in vocab.items():
        for tag, syns in (terms or {}).items():
            syns = [str(s) for s in (syns or [])]
            labels[tag] = syns[0] if syns else tag
            for s in syns:
                synonyms.append([s, tag])
    return {"built": date.today().isoformat(), "docs": docs, "synonyms": synonyms, "tagLabels": labels}


def write_site(index):
    SITE.mkdir(exist_ok=True)
    (SITE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    tpl = (ROOT / "scripts" / "atlas_template.html").read_text(encoding="utf-8")
    engine = (ROOT / "scripts" / "search.js").read_text(encoding="utf-8")
    data = json.dumps(index, ensure_ascii=False).replace("</", "<\\/")
    out = tpl.replace("/*__SEARCH_JS__*/", engine).replace("/*__DATA__*/null", data)
    (SITE / "index.html").write_text(out, encoding="utf-8")


def main():
    args = set(sys.argv[1:])
    schema, vocab = load_yaml(META / "schema.yaml"), load_yaml(META / "vocab.yaml")
    cards, errors = load_cards(schema)
    e2, warns = validate(cards, schema, vocab)
    errors += e2

    print(f"카드 {len(cards)}장 · 오류 {len(errors)} · 경고 {len(warns)}")
    for e in errors:
        print("  ✗", e)
    for w in warns:
        print("  !", w)

    if "--audit" in args:
        for k, v in audit(cards).items():
            print(f"\n[{k}] {len(v)}개")
            for i in v:
                print("  -", i)
        return
    if errors:
        sys.exit("빌드 중단: 오류를 먼저 고치세요")

    index = build_index(cards, schema, vocab)
    write_site(index)
    print(f"→ site/index.html, site/index.json 생성 ({len(index['docs'])}개 문서, 동의어 {len(index['synonyms'])}개)")

    if "--test" in args:
        r = subprocess.run(["node", str(ROOT / "scripts" / "test_search.js")], cwd=ROOT)
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
