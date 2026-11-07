#!/usr/bin/env python3
"""Builds the PIKO website (support + privacy pages) from privacy-policy.md.

Usage: python3 build.py   (no dependencies)
The privacy policy's source of truth is docs/privacy-policy.md in the PIKO app
repo; copy it here and rebuild whenever it changes.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent

CSS = """
:root{--red:#F70A0A;--yellow:#FFCC00;--blue:#2B60FF;--navy:#00238A;--ink:#2F3142;--soft:#5E6275;--bg:#F4F8FF;--card:#FFFFFF;--line:#E3E8F3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#EEF1FA;--soft:#B5BACB;--bg:#0E1328;--card:#171E3A;--line:#2A3357}}
*{box-sizing:border-box}
html,body{max-width:100%;overflow-x:hidden}
body{margin:0;overflow-wrap:anywhere;background:var(--bg);color:var(--ink);font:17px/1.6 ui-rounded,"SF Pro Rounded",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{background:var(--navy);padding:28px 16px 34px;text-align:center}
header img{width:min(320px,80vw);height:auto}
header p{color:#fff;margin:6px 0 0;font-weight:700;letter-spacing:.06em}
main{max-width:760px;margin:-18px auto 40px;padding:0 16px}
.card{background:var(--card);border-radius:24px;padding:24px clamp(18px,4vw,36px);box-shadow:0 6px 0 var(--line)}
h1{font-size:1.9rem;line-height:1.2;margin:.2em 0 .4em}
h2{font-size:1.25rem;margin:1.6em 0 .4em;color:var(--blue)}
@media (prefers-color-scheme:dark){h2{color:#8FB0FF}}
a{color:var(--blue);font-weight:700}
@media (prefers-color-scheme:dark){a{color:#8FB0FF}}
table{width:100%;border-collapse:collapse;margin:1em 0;font-size:.95rem;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:rgba(43,96,255,.08)}
ul{padding-left:1.2em}
.muted{color:var(--soft);font-size:.95rem}
.btns{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0 6px}
.btn{display:inline-block;padding:12px 22px;border-radius:18px;text-decoration:none;color:#fff;background:var(--blue);box-shadow:0 5px 0 #0A2590}
.btn.y{background:var(--yellow);color:#2F3142;box-shadow:0 5px 0 #8C6E00}
footer{text-align:center;color:var(--soft);font-size:.9rem;padding:0 16px 32px}
"""


def page(title, body, rel=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="PIKO – The Pinoy Game: the Filipino street hopscotch game for iPhone and Android.">
<link rel="icon" href="{rel}assets/icon.png">
<style>{CSS}</style>
</head>
<body>
<header><a href="{rel or './'}"><img src="{rel}assets/piko-logo.png" alt="PIKO"></a><p>THE PINOY GAME</p></header>
<main><div class="card">
{body}
</div></main>
<footer>© 2026 Kel Escueta · <a href="{rel}privacy/">Privacy Policy</a> · <a href="mailto:brandindigitalads@gmail.com">brandindigitalads@gmail.com</a></footer>
</body>
</html>
"""


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"(?<![\">])(https?://[^\s<]+[^\s<.,)])", r'<a href="\1">\1</a>', text)
    text = re.sub(r"([\w.+-]+@[\w-]+\.[\w.]+)", r'<a href="mailto:\1">\1</a>', text)
    return text


def md_to_html(md):
    out, para, lst, table = [], [], [], []

    def flush():
        if para:
            # Lines starting with a bold label ("**Contact:** …") stay on their own line.
            joined = para[0]
            for ln in para[1:]:
                joined += ("<br>" if ln.startswith("**") else " ") + ln
            out.append("<p>" + inline(joined).replace("&lt;br&gt;", "<br>") + "</p>")
            para.clear()
        if lst:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in lst) + "</ul>")
            lst.clear()
        if table:
            rows = [r for r in table if not re.match(r"^\|?\s*-{2,}", r.replace("|", "").strip() and r)]
            rows = [r for r in table if not set(r.replace("|", "").strip()) <= set("-: ")]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head, *rest = cells
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rest)
                       + "</tbody></table>")
            table.clear()

    for line in md.splitlines():
        s = line.rstrip()
        if not s.strip():
            flush()
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", s)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        elif s.lstrip().startswith("|"):
            if para or lst:
                flush()
            table.append(s)
        elif re.match(r"^\s*[-*]\s+", s):
            if para or table:
                flush()
            lst.append(re.sub(r"^\s*[-*]\s+", "", s))
        elif lst and s.startswith("  "):
            lst[-1] += " " + s.strip()
        else:
            if lst or table:
                flush()
            para.append(s.strip().rstrip("\\"))
    flush()
    return "\n".join(out)


SUPPORT = """
<h1>PIKO – The Pinoy Game</h1>
<p>Remember playing <strong>piko</strong> on the street after school? PIKO brings the classic Filipino hopscotch to your phone — chalk boxes, tsinelas and all. The street moves toward you; when a chalk box reaches your feet, tap it to land!</p>

<h2>How to play</h2>
<ul>
<li><strong>One box with a footprint:</strong> tap it with ONE finger.</li>
<li><strong>Two boxes joined by “=”:</strong> tap BOTH at the same time with two fingers.</li>
<li><strong>Numbered boxes:</strong> tap 1, then 2, then 3 — in order.</li>
<li>Land every row and hop all the way to <strong>LANGIT</strong> to clear the level. New to the game? Open <strong>Guide → Try it! Practice</strong> in the app.</li>
</ul>

<h2>Questions</h2>
<p><strong>Do I need an account?</strong><br>No. Just tap Play. There are no sign-ups, ads or in-app purchases.</p>
<p><strong>Why don't I see my ranking on the home screen?</strong><br>Rankings use Apple Game Center (iPhone) or Google Play Games (Android) and are optional. Sign in to Game Center in your iPhone's <em>Settings → Game Center</em> (or to Google Play Games on Android), then finish a level. New scores can take a few minutes to appear. The line under <em>Player</em> in PIKO's Settings tells you what's missing.</p>
<p><strong>How do I start over?</strong><br>In PIKO, open <em>Settings → Reset progress</em>.</p>
<p><strong>The two-finger boxes don't register.</strong><br>Touch both boxes at the same moment, with two separate fingers, when the boxes reach your feet. Try the practice course in the Guide — it has extra-generous timing.</p>

<h2>Contact</h2>
<p>Questions, feedback or a problem with the game? Email <a href="mailto:brandindigitalads@gmail.com">brandindigitalads@gmail.com</a> — we're happy to help.</p>

<div class="btns">
<a class="btn" href="mailto:brandindigitalads@gmail.com?subject=PIKO%20support">Email support</a>
<a class="btn y" href="privacy/">Privacy Policy</a>
</div>
"""

(ROOT / "index.html").write_text(page("PIKO – The Pinoy Game · Support", SUPPORT))
policy = md_to_html((ROOT / "privacy-policy.md").read_text())
(ROOT / "privacy").mkdir(exist_ok=True)
(ROOT / "privacy" / "index.html").write_text(page("PIKO – Privacy Policy", policy, rel="../"))
print("built index.html and privacy/index.html")
