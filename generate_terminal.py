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
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

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
      width: 820px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.55);
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

    .red {
      background: #ff5f56;
    }

    .yellow {
      background: #ffbd2e;
    }

    .green {
      background: #27c93f;
    }

    .title {
      margin-left: 12px;
      color: #e6edf3;
      font-size: 14px;
      font-weight: 700;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
    }

    .terminal {
      padding: 28px 30px;
      background: #0d1117;
    }

    .terminal-header {
      color: #8b949e;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 13px;
      margin-bottom: 18px;
    }

    .line {
      display: flex;
      align-items: center;
      min-height: 34px;
      font-family: "SF Mono", "Fira Code", "JetBrains Mono",
                   Menlo, Consolas, monospace;
      font-size: 15px;
      line-height: 1.5;
    }

    .prompt {
      color: #3fb950;
      margin-right: 10px;
      font-weight: 700;
    }

    .hash {
      color: #8b949e;
      margin-right: 12px;
      font-size: 12px;
    }

    .message {
      color: #c9d1d9;
    }

    .footer {
      padding: 15px 24px;
      background: #161b22;
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
    </div>

    <div class="terminal">
      <div class="terminal-header">$ git log --oneline</div>

      {content}
    </div>

    <div class="footer">
      Clean history makes future debugging easier.
    </div>

  </div>
</body>
</html>
"""


def generate_terminal(
    content: str,
    title: str = "git log",
    output: str = "terminal.png"
):
    lines = content.splitlines()
    rendered_lines = []

    for index, line in enumerate(lines):
        safe_line = html.escape(line)

        # Generate a deterministic-looking commit hash.
        commit_hash = f"{(index + 1) * 0x3a7b1:07x}"[-7:]

        rendered_lines.append(
            f"""
            <div class="line">
              <span class="prompt">●</span>
              <span class="hash">{commit_hash}</span>
              <span class="message">{safe_line}</span>
            </div>
            """
        )

    page_html = (
        HTML_TEMPLATE
        .replace("{title}", html.escape(title))
        .replace("{content}", "\n".join(rendered_lines))
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
            viewport={"width": 900, "height": 900},
            device_scale_factor=2
        )

        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)

        element = page.query_selector(".window")
        element.screenshot(path=output)

        browser.close()

    print(f"✅ Terminal image saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate terminal-style images for X posts"
    )

    parser.add_argument(
        "--title",
        default="Terminal"
    )

    parser.add_argument(
        "--output",
        default="terminal.png"
    )

    parser.add_argument(
        "--content",
        required=True,
        help="Terminal lines. Use \\n for new lines."
    )

    args = parser.parse_args()

    content = args.content.replace("\\n", "\n")

    generate_terminal(
        content=content,
        title=args.title,
        output=args.output
    )
