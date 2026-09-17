from playwright.sync_api import sync_playwright
import tempfile
import argparse
import html

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background:#0d1117; padding:48px; display:flex; justify-content:center; align-items:center; min-height:100vh; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
.window { background:#161b22; border-radius:16px; border:1px solid #30363d; box-shadow:0 25px 60px rgba(0,0,0,.55); overflow:hidden; width:900px; }
.titlebar { background:#21262d; padding:15px 18px; display:flex; align-items:center; gap:9px; border-bottom:1px solid #30363d; }
.dot { width:13px; height:13px; border-radius:50%; }
.red { background:#ff5f56; } .yellow { background:#ffbd2e; } .green { background:#27c93f; }
.title { margin-left:12px; color:#e6edf3; font-size:15px; font-weight:700; }
.badge { margin-left:auto; background:#da3633; color:white; padding:6px 12px; border-radius:20px; font-size:11px; font-weight:800; letter-spacing:.5px; }
.code-wrapper { padding:30px; background:#0d1117; }
pre { margin:0; padding:26px 28px; background:#161b22; border:1px solid #30363d; border-radius:10px; overflow:hidden; white-space:pre-wrap; overflow-wrap:anywhere; }
code { font-family:"SF Mono","Fira Code","JetBrains Mono",Menlo,Consolas,monospace !important; font-size:15px; line-height:1.65; }
.hint { padding:14px 24px; background:#0d1117; border-top:1px solid #30363d; color:#8b949e; text-align:center; font-size:12px; }
</style>
</head>
<body>
<div class="window">
<div class="titlebar"><div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div><div class="title">{title}</div><div class="badge">SPOT THE BUG</div></div>
<div class="code-wrapper"><pre><code class="language-{lang}">{code}</code></pre></div>
<div class="hint">Something here will hurt in production.</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
</body>
</html>
"""

def generate_spot_the_bug(code: str, lang: str = "python", title: str = "Spot the Bug", output: str = "spot_the_bug.png"):
    page_html = HTML_TEMPLATE.replace("{title}", html.escape(title)).replace("{lang}", html.escape(lang)).replace("{code}", html.escape(code))
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page_html)
        html_path = f.name
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width":1000,"height":900}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(700)
        page.query_selector(".window").screenshot(path=output)
        browser.close()
    print(f"✅ Spot the Bug image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Spot the Bug code images for X posts")
    parser.add_argument("--lang", default="python")
    parser.add_argument("--title", default="Spot the Bug")
    parser.add_argument("--output", default="spot_the_bug.png")
    parser.add_argument("--code", required=True, help="Code snippet. Use \\n for new lines.")
    args = parser.parse_args()
    generate_spot_the_bug(args.code.replace("\\n", "\n"), args.lang, args.title, args.output)
