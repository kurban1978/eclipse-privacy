"""Builds licenses.html from the game's Flutter NOTICES file.

Usage: python build_licenses.py path/to/flutter_assets/NOTICES.Z
(build/app/intermediates/flutter/release/flutter_assets/NOTICES.Z after
`flutter build`). Packages are grouped by license type like a store page:
names with their copyright lines, then the license text once per group.
Packages whose license doesn't match a common template keep their full text.
"""

import html
import re
import sys
import zlib
from collections import defaultdict
from datetime import date

raw = open(sys.argv[1], "rb").read()
text = zlib.decompress(raw, 47).decode() if sys.argv[1].endswith(".Z") else raw.decode()

MIT = """Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

BSD_HEAD = """Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution."""

BSD_3 = """

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission."""

BSD_TAIL = """

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

GROUPS = [
    ("apache", "Apache License 2.0", None),
    ("mit", "MIT License", MIT),
    ("bsd3", "BSD 3-Clause License", BSD_HEAD + BSD_3 + BSD_TAIL),
    ("bsd2", "BSD 2-Clause License", BSD_HEAD + BSD_TAIL),
    ("other", "Other licenses", None),
]


def kind(body):
    flat = " ".join(body.split())
    if "Apache License" in flat and "Version 2.0" in flat:
        return "apache"
    if "Permission is hereby granted, free of charge" in flat:
        return "mit"
    if "Redistribution and use in source and binary forms" in flat:
        if "Neither the name" in flat or "neither the name" in flat:
            return "bsd3"
        return "bsd2"
    if "BSD-style license" in flat:
        return "bsd3"
    return "other"


def copyrights(body):
    out = []
    for line in body.split("\n"):
        s = line.strip(" \t*#/;-")
        # Only real notices: "Copyright (c) 2014 Owner", "© 2020 Owner".
        if not re.match(r"(?i)(portions )?(copyright\s*(\(c\)|©)?|\(c\)|©)\s*\d{4}", s):
            continue
        owner = re.sub(r"(?i)^(portions )?copyright|\(c\)|©|all rights reserved\.?", "", s)
        owner = re.sub(r"(?i)^([\s\d,\-–]|present\b|by\b)+", "", owner)  # years
        owner = re.sub(r"\s+", " ", owner).strip(" .,;")
        owner = re.sub(r"(?i)\.? ?please see the authors file.*", "", owner)
        if owner and len(owner) < 120 and "yyyy" not in owner and owner not in out:
            out.append(owner)
    return out


groups = defaultdict(lambda: defaultdict(list))  # kind -> package -> [copyrights]
other_texts = defaultdict(list)  # package -> [full text]
apache_text = None
for block in text.split("\n" + "-" * 80 + "\n"):
    head, _, body = block.strip("\n").partition("\n\n")
    packages = [p.strip() for p in head.split("\n") if p.strip()]
    if not packages or not body.strip():
        continue
    k = kind(body)
    if k == "apache" and apache_text is None and "TERMS AND CONDITIONS" in body:
        start = body.find("Apache License")
        apache_text = body[start:].strip()
    for p in packages:
        cr = groups[k][p]
        for c in copyrights(body):
            if c not in cr:
                cr.append(c)
        if k == "other" and body.strip() not in other_texts[p]:
            other_texts[p].append(body.strip())

total = len({p for g in groups.values() for p in g})
e = html.escape


def package_row(name, crs, full=None):
    shown = crs[:3]
    more = f'<span class="more"> +{len(crs) - 3} more</span>' if len(crs) > 3 else ""
    notes = "".join(f"<span>© {e(c)}</span>" for c in shown)
    body = f'<b>{e(name)}</b>{" — " if shown else ""}{notes}{more}'
    if full:
        texts = "\n\n" + ("\n\n" + "·" * 12 + "\n\n").join(full)
        return f"<li><details><summary>{body}</summary><pre>{e(texts.strip())}</pre></details></li>"
    return f"<li>{body}</li>"


sections = []
toc = []
n = 0
for key, title, canonical in GROUPS:
    pkgs = groups.get(key)
    if not pkgs:
        continue
    n += 1
    if key == "apache":
        canonical = apache_text
    toc.append(f'<a href="#{key}">{e(title)} <small>{len(pkgs)}</small></a>')
    items = "\n".join(
        package_row(p, pkgs[p], other_texts[p] if key == "other" else None)
        for p in sorted(pkgs, key=str.lower)
    )
    license_html = (
        f'<details class="license"><summary>License text</summary><pre>{e(canonical)}</pre></details>'
        if canonical
        else '<p class="hint">Each of these has its own terms — tap a name to read them.</p>'
    )
    sections.append(
        f'<section id="{key}"><h2>{n}. {e(title)}</h2>'
        f"<ul>{items}</ul>{license_html}</section>"
    )

page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Eclipse: Shadow &amp; Light — Licenses</title>
  <meta name="description" content="Open source software used in Eclipse: Shadow &amp; Light.">
  <style>
    :root {{
      --bg: #faf8ff; --fg: #1d1a2b; --muted: #6b6680; --card: #ffffff;
      --border: #e3def0; --accent: #d63384; --code: #f1eef8;
      color-scheme: light dark;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0e0a1a; --fg: #ece8f6; --muted: #9a93b0; --card: #171126;
        --border: #2c2342; --accent: #f06bb0; --code: #221a36;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--bg); color: var(--fg);
      font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    }}
    main {{ max-width: 760px; margin: 0 auto; padding: 24px 16px 64px; }}
    .brand {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }}
    .brand b {{ letter-spacing: .28em; font-size: 18px; }}
    .brand span {{ display: block; color: var(--muted); font-size: 11px; letter-spacing: .2em; }}
    h1 {{ font-size: 26px; line-height: 1.25; margin: 0 0 4px; }}
    .lead {{ color: var(--muted); margin: 8px 0 20px; }}
    nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }}
    nav a {{
      text-decoration: none; color: var(--fg); background: var(--card);
      border: 1px solid var(--border); border-radius: 999px; padding: 6px 14px; font-size: 14px;
    }}
    nav small {{ color: var(--accent); font-weight: 700; margin-left: 4px; }}
    h2 {{ font-size: 20px; margin: 36px 0 8px; padding-top: 16px; border-top: 1px solid var(--border); }}
    ul {{ padding-left: 20px; margin: 0; }}
    li {{ margin: 6px 0; overflow-wrap: anywhere; }}
    li span {{ color: var(--muted); }}
    li span + span::before {{ content: "; "; }}
    .more {{ color: var(--muted); font-size: 13px; }}
    details summary {{ cursor: pointer; }}
    details.license {{
      margin-top: 16px; background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 10px 14px;
    }}
    details.license > summary {{ color: var(--accent); font-weight: 600; }}
    pre {{
      white-space: pre-wrap; overflow-wrap: anywhere; font-size: 13px; line-height: 1.5;
      background: var(--code); border-radius: 8px; padding: 12px; margin: 10px 0 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .hint {{ color: var(--muted); font-size: 14px; }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <main>
    <div class="brand">
      <svg width="44" height="44" viewBox="0 0 44 44" aria-hidden="true">
        <circle cx="22" cy="22" r="13" fill="#fff" stroke="#d9d3ea"/>
        <circle cx="19.9" cy="23.3" r="12.6" fill="#171126"/>
      </svg>
      <div><b>ECLIPSE</b><span>SHADOW · LIGHT</span></div>
    </div>
    <h1>Licenses</h1>
    <p class="lead">Eclipse: Shadow &amp; Light is built with {total} open source components.
    Below they are grouped by license. Last updated {date.today():%-d %B %Y}.</p>
    <nav>{"".join(toc)}</nav>
    {"".join(sections)}
  </main>
</body>
</html>
"""
open("licenses.html", "w", encoding="utf-8").write(page)
print("licenses.html:", total, "packages;", {k: len(v) for k, v in groups.items()})
