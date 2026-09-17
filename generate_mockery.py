from playwright.sync_api import sync_playwright
import tempfile
import argparse
import html


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #0d1117;
      padding: 48px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .window {
      width: 760px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
    }

    .titlebar {
      background: #21262d;
      padding: 15px 18px;
      display: flex;
      align-items: center;
      gap: 9px;
      border-bottom: 1px solid #30363d;
    }

    .dot {
      width: 13px;
      height: 13px;
      border-radius: 50%;
    }

    .red { background: #ff5f56; }
    .yellow { background: #ffbd2e; }
    .green { background: #27c93f; }

    .title {
      margin-left: 12px;
      color: #e6edf3;
      font-size: 15px;
      font-weight: 700;
    }

    .badge {
      margin-left: auto;
      background: #da3633;
      color: white;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.4px;
    }

    .content {
      padding: 30px;
      background: #0d1117;
    }

    .terminal {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 24px 28px;
    }

    .line {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 7px 0;
      color: #c9d1d9;
      font-family: "SF Mono", "Fira Code", "JetBrains Mono",
                   Menlo, Consolas, monospace;
      font-size: 15px;
      line-height: 1.45;
    }

    .number {
      width: 28px;
      color: #6e7681;
      text-align: right;
      user-select: none;
    }

    .command {
      color: #79c0ff;
    }

    .final {
      color: #f85149;
      font-weight: 700;
    }

    .footer {
      padding: 16px 24px;
      background: #0d1117;
      border-top: 1px solid #30363d;
      color: #8b949e;
      text-align: center;
      font-size: 12px;
    }
  </style>
</head>

<body>
  <div class="window">

    <div class="titlebar">
      <div class="dot red"></div>
      <div class="dot yellow"></div>
      <div class="dot green"></div>

      <div class="title">{title}</div>

      <div class="badge">JUST ONE API</div>
    </div>

    <div class="content">
      <div class="terminal">
        {content}
      </div>
    </div>

    <div class="footer">
      When "simple" infrastructure starts needing its own infrastructure.
    </div>

  </div>
</body>
</html>
"""


def generate_mockery(
    content: str,
    title: str = "Just One API",
    output: str = "mockery.png"
):
    lines = content.splitlines()

    rendered = []

    for index, line in enumerate(lines, start=1):
        safe_line = html.escape(line)

        if "more YAML" in line or "more" in line.lower():
            rendered.append(
                f'<div class="line final">'
                f'<span class="number">{index}</span>'
                f'<span>{safe_line}</span>'
                f'</div>'
            )
        else:
            rendered.append(
                f'<div class="line">'
                f'<span class="number">{index}</span>'
                f'<span class="command">{safe_line}</span>'
                f'</div>'
            )

    page_html = (
        HTML_TEMPLATE
        .replace("{title}", html.escape(title))
        .replace("{content}", "\n".join(rendered))
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8"
    ) as f:
        f.write(page_html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()

        page = browser.new_page(
            viewport={"width": 850, "height": 1000},
            device_scale_factor=2
        )

        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)

        element = page.query_selector(".window")
        element.screenshot(path=output)

        browser.close()

    print(f"✅ Mockery image saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate humorous technical mockery images for X posts"
    )

    parser.add_argument(
        "--title",
        default="Just One API"
    )

    parser.add_argument(
        "--output",
        default="mockery.png"
    )

    parser.add_argument(
        "--content",
        required=True,
        help="Content lines. Use \\n for new lines."
    )

    args = parser.parse_args()

    content = args.content.replace("\\n", "\n")

    generate_mockery(
        content=content,
        title=args.title,
        output=args.output
    )
