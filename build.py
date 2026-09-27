"""Builds index.html from the game's docs/privacy-policy.md.

Usage: python build.py path/to/privacy-policy.md
The markdown holds three sections separated by `---`, headed
`# ... {#uz}`, `{#ru}` and `{#en}`. Each becomes one tab.
"""

import re
import sys

import markdown

LANGS = [("uz", "O‘zbekcha", "uz"), ("ru", "Русский", "ru"), ("en", "English", "en")]

src = open(sys.argv[1], encoding="utf-8").read()
sections = {}
for part in re.split(r"\n---\n", src):
    m = re.search(r"^# (.+?) \{#(\w+)\}\s*$", part, re.M)
    if not m:
        continue
    body = part[m.end():]
    html = markdown.markdown(body)
    # Tashqi havolalar yangi oynada ochiladi.
    html = html.replace('<a href="http', '<a target="_blank" rel="noopener" href="http')
    sections[m.group(2)] = (m.group(1), html)

tabs = "\n".join(
    f'      <button role="tab" id="tab-{c}" '
    f'aria-controls="panel-{c}" aria-selected="false" data-lang="{c}">{name}</button>'
    for c, name, _ in LANGS
)
panels = "\n".join(
    f'    <section role="tabpanel" id="panel-{c}" lang="{hl}" aria-labelledby="tab-{c}">\n'
    f"      <h1>{sections[c][0]}</h1>\n{sections[c][1]}\n    </section>"
    for c, _, hl in LANGS
)

page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Eclipse: Shadow &amp; Light — Privacy Policy</title>
  <meta name="description" content="Privacy policy of the puzzle game Eclipse: Shadow &amp; Light.">
  <style>
    :root {{
      --bg: #faf8ff; --fg: #1d1a2b; --muted: #6b6680; --card: #ffffff;
      --border: #e3def0; --accent: #d63384; --accent-fg: #ffffff; --code: #f1eef8;
      color-scheme: light dark;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0e0a1a; --fg: #ece8f6; --muted: #9a93b0; --card: #171126;
        --border: #2c2342; --accent: #f06bb0; --accent-fg: #14091c; --code: #221a36;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--bg); color: var(--fg);
      font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    }}
    main {{ max-width: 760px; margin: 0 auto; padding: 24px 16px 64px; }}
    .brand {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }}
    .brand svg {{ flex: none; }}
    .brand b {{ letter-spacing: .28em; font-size: 18px; }}
    .brand span {{ display: block; color: var(--muted); font-size: 11px; letter-spacing: .2em; }}
    nav[role=tablist] {{
      position: sticky; top: 0; z-index: 1; display: flex; gap: 4px; padding: 4px;
      background: var(--card); border: 1px solid var(--border); border-radius: 999px;
      margin-bottom: 24px;
    }}
    nav button {{
      flex: 1; min-height: 40px; border: 0; border-radius: 999px; cursor: pointer;
      background: transparent; color: var(--muted); font: inherit; font-weight: 600;
    }}
    nav button[aria-selected=true] {{ background: var(--accent); color: var(--accent-fg); }}
    nav button:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
    section[hidden] {{ display: none; }}
    h1 {{ font-size: 26px; line-height: 1.25; margin: 0 0 4px; }}
    h2 {{ font-size: 20px; margin: 32px 0 8px; padding-top: 16px; border-top: 1px solid var(--border); }}
    h3 {{ font-size: 17px; margin: 20px 0 4px; }}
    p, li {{ overflow-wrap: anywhere; }}
    em {{ color: var(--muted); }}
    a {{ color: var(--accent); }}
    code {{ background: var(--code); padding: 1px 5px; border-radius: 4px; font-size: 14px; }}
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
    <nav role="tablist" aria-label="Language">
{tabs}
    </nav>
{panels}
  </main>
  <script>
    const codes = ["uz", "ru", "en"];
    const tabs = [...document.querySelectorAll("[role=tab]")];
    function show(code, focus) {{
      for (const t of tabs) {{
        const on = t.dataset.lang === code;
        t.setAttribute("aria-selected", on);
        t.tabIndex = on ? 0 : -1;
        document.getElementById("panel-" + t.dataset.lang).hidden = !on;
        if (on && focus) t.focus();
      }}
      document.documentElement.lang = code;
    }}
    function fromHash() {{
      const h = location.hash.slice(1);
      if (codes.includes(h)) return h;
      const nav = (navigator.language || "").toLowerCase();
      return nav.startsWith("uz") ? "uz" : nav.startsWith("ru") ? "ru" : "en";
    }}
    for (const t of tabs) {{
      t.addEventListener("click", () => {{
        history.replaceState(null, "", "#" + t.dataset.lang);
        show(t.dataset.lang);
        scrollTo(0, 0);
      }});
      t.addEventListener("keydown", (e) => {{
        const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        const next = tabs[(tabs.indexOf(t) + d + tabs.length) % tabs.length];
        next.click();
        next.focus();
      }});
    }}
    addEventListener("hashchange", () => show(fromHash()));
    show(fromHash());
    scrollTo(0, 0);
  </script>
</body>
</html>
"""
open("index.html", "w", encoding="utf-8").write(page)
print("index.html:", ", ".join(sections))
