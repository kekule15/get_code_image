from playwright.sync_api import sync_playwright
import tempfile
import argparse

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d1117;
      padding: 48px;
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
      max-width: 780px;
      border: 1px solid #30363d;
    }
    .titlebar {
      background: #21262d;
      padding: 13px 18px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .red { background: #ff5f56; }
    .yellow { background: #ffbd2e; }
    .green { background: #27c93f; }
    .badge {
      margin-left: auto;
      background: #da3633;
      color: white;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 20px;
      letter-spacing: 0.3px;
    }
    pre {
      margin: 0;
      padding: 26px 30px;
      font-size: 14.5px;
      line-height: 1.6;
      overflow-x: auto;
    }
    code {
      font-family: "SF Mono", "Fira Code", Menlo, monospace !important;
    }
  </style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dot red"></div>
      <div class="dot yellow"></div>
      <div class="dot green"></div>
      <div class="badge">RED FLAG</div>
    </div>
    <pre><code class="language-{lang}">{code}</code></pre>
  </div>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script>hljs.highlightAll();</script>
</body>
</html>
"""

def generate_red_flag(code: str, lang: str = "sql", output: str = "red_flag.png"):
    html = HTML_TEMPLATE.replace("{code}", code.replace("<", "&lt;").replace(">", "&gt;"))
    html = html.replace("{lang}", lang)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 800}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(600)

        element = page.query_selector(".window")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ Red Flag image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    parser.add_argument("--lang", default="sql")
    parser.add_argument("--output", default="red_flag.png")
    args = parser.parse_args()

    code = args.code.replace("\\n", "\n")
    generate_red_flag(code, args.lang, args.output)