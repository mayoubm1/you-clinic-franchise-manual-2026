# -*- coding: utf-8 -*-
"""Builds the YOU WELLNESS CLINIC manual portal from the 10 modular chapter files.

OUTPUTS
  chapters/01-chapter.html .. 10-chapter.html  modular sources (cleaned)
  chapters.json                                 manifest (title + body per chapter)
  master.html                                   single unified document for print / PDF
  index.html                                    interactive futuristic HUD reader (no server needed)

The reader inlines all content + per-chapter CSS, so index.html works offline via file://
and on any static host (GitHub Pages / Vercel / Netlify) with zero build step at deploy time.
"""
import io, os, re, json, glob

BASE = os.path.dirname(os.path.abspath(__file__))
CH_OSRC = r"C:\Users\3mayo\OneDrive\D-Latitude-7480\Repos\telstp-omnicognitor-unity\New folder"
CITE_RE = re.compile(r"\s*\[cite:\s*\d+\]")

# ---------------------------------------------------------------------------- css scoping
def _split_top(css):
    """Yield (segment) top-level chunks of css, brace-depth aware."""
    out, i, n = [], 0, len(css)
    while i < n:
        while i < n and css[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        start, d = i, 0
        while i < n:
            c = css[i]
            if d == 0 and c == ";":
                out.append((css[start:i], ""))
                i += 1
                break
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
                if d == 0:
                    out.append((css[start:i], ""))
                    i += 1
                    break
            i += 1
        else:
            out.append((css[start:i], ""))
            break
    return out


def _split_selectors(prelude):
    """Split a selector list on commas that sit outside parentheses (e.g. :is())."""
    parts, cur, depth, in_str = [], "", 0, None
    for ch in prelude:
        if in_str:
            cur += ch
            if ch == in_str:
                in_str = None
            continue
        if ch in "\"'":
            in_str, cur = ch, cur + ch
        elif ch == "(":
            depth, cur = depth + 1, cur + ch
        elif ch == ")":
            depth, cur = depth - 1, cur + ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _scope_selectors(sel, scope):
    sel = sel.strip()
    if sel in ("body", "html", ":root"):
        return scope
    if sel.startswith(":root"):
        return scope + sel[len(":root"):]
    if sel == "*":
        return scope + " *"
    return "%s %s" % (scope, sel)


def _scope(css, scope):
    """Prefix every selector with the chapter container id, keeping @media/@supports nesting."""
    out = []
    for seg, _ in _split_top(css):
        seg = seg.strip()
        if not seg:
            continue
        if seg.startswith(("@media", "@supports", "@layer")):
            m = re.match(r"(@media[^{]*)\{(.*)", seg, re.S)
            inner = m.group(2)
            out.append("%s{ %s }" % (m.group(1).rstrip(), _scope(inner, scope)))
        elif seg.startswith(("@page", "@font-face", "@keyframes", "@import", "@charset")):
            out.append(seg)
        else:
            m = re.match(r"([^{]*)\{(.*)\}\s*$", seg, re.S)
            if not m:
                out.append(seg)
                continue
            selectors = ", ".join(_scope_selectors(s, scope) for s in _split_selectors(m.group(1)))
            out.append("%s { %s }" % (selectors, m.group(2)))
    return " ".join(out)


# ---------------------------------------------------------------------------- chapter parse
SRC_PAT = os.path.join(CH_OSRC, "gemini-code*.html")
chapters = []
for f in sorted(glob.glob(SRC_PAT)):
    raw = io.open(f, encoding="utf-8", errors="replace").read()
    num = int(re.search(r"code(\d+)", os.path.basename(f)).group(1))

    title_m = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
    title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "Chapter %d" % num

    css_m = re.search(r"<style[^>]*>([\s\S]*?)</style>", raw, re.I)
    css = css_m.group(1) if css_m else ""

    body_m = re.search(r"<body[^>]*>([\s\S]*?)</body>", raw, re.I) or re.search(r"<main[^>]*>([\s\S]*?)</main>", raw, re.I)
    body = body_m.group(1).strip() if body_m else raw

    body = CITE_RE.sub("", body)
    title = CITE_RE.sub("", title)

    h1_m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", body, re.I)
    h1 = re.sub(r"<[^>]+>", "", h1_m.group(1)).strip() if h1_m else title

    chapters.append({
        "n": num,
        "title": title,
        "h1": h1,
        "css": css,
        "body": body,
        "src": os.path.basename(f),
        "scss": _scope(css, "#ch%d" % num),
    })

chapters.sort(key=lambda c: c["n"])

# ---------------------------------------------------------------------------- 3D widget injection
WIDGET = ('<div class="asbuilt-3d-widget" data-gltf-src="assets/models/facility-as-built.gltf">'
          '<div class="hud-3d-overlay">'
          '<button class="hud-3d-btn" onclick="asBuiltManager.toggleWireframe(this)">Wireframe</button>'
          '<button class="hud-3d-btn" onclick="asBuiltManager.toggleAutoRotate(this)">Rotate</button>'
          '<button class="hud-3d-btn" onclick="asBuiltManager.resetCamera()">Reset View</button>'
          '</div>'
          '<div class="hud-3d-status">STATUS: <span class="status-text">INITIALIZING...</span></div>'
          '</div>')

WIDGET_NOTE = ('<p><em>Interactive 3D as-built viewer</em> — drag to orbit, scroll to zoom. '
               'Loads <code>assets/models/facility-as-built.gltf</code> when present; '
               'otherwise renders a procedural mock-up.</p>')


def inject_widget(body):
    m = re.search(r"(<h2[^>]*>\s*5\.2[^<]*</h2>)", body, re.I | re.S)
    if m:
        return body[:m.start(1)] + m.group(1) + "\n" + WIDGET + "\n" + WIDGET_NOTE + body[m.end(1):]
    m = re.search(r"(<h2[^>]*>5\.0[^<]*</h2>)", body, re.I | re.S)
    if m:
        return body[:m.start(1)] + m.group(1) + "\n" + WIDGET + "\n" + WIDGET_NOTE + body[m.end(1):]
    return body + WIDGET


for c in chapters:
    c["body3d"] = inject_widget(c["body"]) if c["n"] == 5 else c["body"]

# ---------------------------------------------------------------------------- modular copies
os.makedirs(os.path.join(BASE, "chapters"), exist_ok=True)
for c in chapters:
    p = os.path.join(BASE, "chapters", "%02d-chapter.html" % c["n"])
    doc = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
           "<title>%s</title><style>%s</style></head><body>%s</body></html>"
           % (c["h1"], c["css"], c["body"]))
    io.open(p, "w", encoding="utf-8").write(doc)

manifest = [{"number": c["n"], "title": c["h1"], "content": c["body"]} for c in chapters]
io.open(os.path.join(BASE, "chapters.json"), "w", encoding="utf-8").write(
    json.dumps(manifest, indent=2, ensure_ascii=False))

# ---------------------------------------------------------------------------- master.html (print)
def master_html(chapters):
    pages = []
    for c in chapters:
        pages.append('<section class="chapter" id="ch%d">\n%s\n</section>\n' % (c["n"], c["body3d"]))
    css_common = r"""
    @page { size: A4; margin: 18mm 16mm 20mm 16mm; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #FFFFFF; }
    .cover { text-align: center; padding: 60mm 0 0; border-bottom: 3px double #E8E2D9; margin-bottom: 0; }
    .cover h1 { font-size: 26pt; letter-spacing: 2px; margin: 0; }
    .cover .sub { font-size: 11pt; color: #555; margin-top: 8pt; }
    .cover .rule { width: 40mm; border-top: 3px solid #0A0A0A; margin: 14px auto; }
    .chapter { break-before: page; page-break-before: always; padding-top: 6mm; }
    #ch1 { break-before: auto; page-break-before: auto; }
    .asbuilt-3d-widget, .hud-3d-overlay, .hud-3d-status, .hud-3d-btn { display: none !important; }
    """
    styles = [css_common] + [c["scss"] for c in chapters]
    body = '<header class="cover"><h1>YOU WELLNESS CLINIC</h1><div class="rule"></div>' \
           '<div class="sub">GLOBAL STANDARD FRANCHISE MANUAL &mdash; V2.1.4 ELITE &middot; Unified Document &middot; 10 Chapters</div></header>' + \
           "".join(pages)
    return ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>YOU WELLNESS CLINIC — Global Standard Franchise Manual (Unified)</title>"
            "<style>%s</style></head><body>%s</body></html>" % (" ".join(styles), body))

io.open(os.path.join(BASE, "master.html"), "w", encoding="utf-8").write(master_html(chapters))
print("master.html OK")

# ---------------------------------------------------------------------------- index.html (reader)
import json as _json


def reader_html(chapters):
    payload = _json.dumps([{"n": c["n"], "title": c["h1"], "css": c["scss"], "html": c["body3d"]}
                           for c in chapters], ensure_ascii=False)
    with io.open(os.path.join(BASE, "assets", "reader_template.html"), encoding="utf-8") as fh:
        template = fh.read()
    return template.replace("/*__CHAPTERS__*/", payload)


io.open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(reader_html(chapters))
print("index.html OK")
print("chapters:", len(chapters))
print("written to", BASE)