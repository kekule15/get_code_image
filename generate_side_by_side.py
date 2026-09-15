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
    .container {
      display: flex;
      gap: 24px;
      max-width: 1200px;
    }
    .window {
      background: #161b22;
      border-radius: 14px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.5);
      overflow: hidden;
      flex: 1;
      min-width: 0;
    }
    .titlebar {
      background: #21262d;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .red { background: #ff5f56; }
    .yellow { background: #ffbd2e; }
    .green { background: #27c93f; }
    .label {
      margin-left: 12px;
      color: #8b949e;
      font-size: 13px;
      font-weight: 500;
    }
    pre {
     padding: 24px 28px;
  font-size: 14.5px;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  color: #c9d1d9;
    }
    code {
      font-family: "SF Mono", "Fira Code", Menlo, monospace !important;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="window">
      <div class="titlebar">
        <div class="dot red"></div>
        <div class="dot yellow"></div>
        <div class="dot green"></div>
        <div class="label">{label1}</div>
      </div>
      <pre><code class="language-{lang}">{code1}</code></pre>
    </div>
    <div class="window">
      <div class="titlebar">
        <div class="dot red"></div>
        <div class="dot yellow"></div>
        <div class="dot green"></div>
        <div class="label">{label2}</div>
      </div>
      <pre><code class="language-{lang}">{code2}</code></pre>
    </div>
  </div>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script>hljs.highlightAll();</script>
</body>
</html>
"""

def generate_side_by_side(code1, code2, lang="sql", label1="Before", label2="After", output="comparison.png"):
    html = HTML_TEMPLATE
    html = html.replace("{code1}", code1.replace("<", "&lt;").replace(">", "&gt;"))
    html = html.replace("{code2}", code2.replace("<", "&lt;").replace(">", "&gt;"))
    html = html.replace("{lang}", lang)
    html = html.replace("{label1}", label1)
    html = html.replace("{label2}", label2)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1300, "height": 900}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(700)

        element = page.query_selector(".container")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ Side-by-side image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code1", required=True)
    parser.add_argument("--code2", required=True)
    parser.add_argument("--lang", default="sql")
    parser.add_argument("--label1", default="Version A")
    parser.add_argument("--label2", default="Version B")
    parser.add_argument("--output", default="comparison.png")
    args = parser.parse_args()

    code1 = args.code1.replace("\\n", "\n")
    code2 = args.code2.replace("\\n", "\n")
    generate_side_by_side(code1, code2, args.lang, args.label1, args.label2, args.output)