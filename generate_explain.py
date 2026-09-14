from playwright.sync_api import sync_playwright
import tempfile
import argparse

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d1117;
      padding: 40px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
    }
    .card {
      background: #161b22;
      border-radius: 14px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
      width: 720px;
      overflow: hidden;
      border: 1px solid #30363d;
    }
    .header {
      background: #21262d;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid #30363d;
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .red { background: #ff5f56; }
    .yellow { background: #ffbd2e; }
    .green { background: #27c93f; }
    .title {
      margin-left: 10px;
      color: #e6edf3;
      font-size: 13px;
      font-weight: 600;
    }
    .body {
      padding: 24px 28px;
      color: #c9d1d9;
      font-size: 13.5px;
      line-height: 1.7;
      white-space: pre-wrap;
    }
    .slow { color: #f85149; font-weight: 600; }
    .fast { color: #3fb950; font-weight: 600; }
    .muted { color: #8b949e; }
    .highlight { background: #388bfd26; padding: 1px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="dot red"></div>
      <div class="dot yellow"></div>
      <div class="dot green"></div>
      <div class="title">{title}</div>
    </div>
    <div class="body">{content}</div>
  </div>
</body>
</html>
"""

def generate_explain(content: str, title: str = "EXPLAIN ANALYZE", output: str = "explain.png"):
    # Simple markdown-like replacements for colors
    content = content.replace("<slow>", '<span class="slow">').replace("</slow>", '</span>')
    content = content.replace("<fast>", '<span class="fast">').replace("</fast>", '</span>')
    content = content.replace("<muted>", '<span class="muted">').replace("</muted>", '</span>')
    content = content.replace("<hl>", '<span class="highlight">').replace("</hl>", '</span>')

    html = HTML_TEMPLATE.replace("{title}", title).replace("{content}", content)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 850, "height": 900}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(400)

        element = page.query_selector(".card")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ EXPLAIN image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, help="Use \\n for newlines. Supports <slow>, <fast>, <muted>, <hl> tags")
    parser.add_argument("--title", default="EXPLAIN ANALYZE")
    parser.add_argument("--output", default="explain.png")
    args = parser.parse_args()

    content = args.content.replace("\\n", "\n")
    generate_explain(content, args.title, args.output)