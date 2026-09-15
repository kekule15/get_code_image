from playwright.sync_api import sync_playwright
from pathlib import Path
import argparse
import tempfile

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 48px;
      background: #0d1117;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .window {
      background: #161b22;
      border-radius: 14px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
      overflow: hidden;
      max-width: 920px;
    }
    .titlebar {
      background: #21262d;
      padding: 14px 18px;
      display: flex;
      gap: 9px;
      align-items: center;
    }
    .dot {
      width: 13px;
      height: 13px;
      border-radius: 50%;
    }
    .red { background: #ff5f56; }
    .yellow { background: #ffbd2e; }
    .green { background: #27c93f; }
    pre {
      margin: 0;
      padding: 28px 32px;
      font-size: 15.5px;
      line-height: 1.6;
      white-space: pre-wrap;
overflow-wrap: anywhere;
word-break: break-word;
color: #c9d1d9;
    }
    code {
      font-family: "SF Mono", "Fira Code", "JetBrains Mono", Menlo, monospace !important;
    }
  </style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dot red"></div>
      <div class="dot yellow"></div>
      <div class="dot green"></div>
    </div>
    <pre><code class="language-{lang}">{code}</code></pre>
  </div>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script>hljs.highlightAll();</script>
</body>
</html>
"""

def generate_image(code: str, lang: str = "sql", output: str = "code.png", width: int = 1000):
    html = HTML_TEMPLATE.replace("{code}", code.replace("<", "&lt;").replace(">", "&gt;"))
    html = html.replace("{lang}", lang)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=2)  # Retina quality
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(600)

        element = page.query_selector(".window")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ Image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate beautiful code images for X posts")
    parser.add_argument("--code", required=True, help="Your code (use \\n for new lines)")
    parser.add_argument("--lang", default="sql", help="Language: sql, python, javascript, go, etc.")
    parser.add_argument("--output", default="code.png", help="Output filename")
    args = parser.parse_args()

    code = args.code.replace("\\n", "\n")
    generate_image(code, args.lang, args.output)