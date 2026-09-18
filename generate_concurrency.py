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
* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  background: #0d1117;
  padding: 42px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

.window {{
  width: 900px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0,0,0,.5);
}}

.titlebar {{
  height: 52px;
  background: #21262d;
  border-bottom: 1px solid #30363d;
  display: flex;
  align-items: center;
  padding: 0 18px;
  gap: 8px;
}}

.dot {{
  width: 13px;
  height: 13px;
  border-radius: 50%;
}}

.red {{ background: #ff5f56; }}
.yellow {{ background: #ffbd2e; }}
.green {{ background: #27c93f; }}

.title {{
  margin-left: 12px;
  color: #e6edf3;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 14px;
  font-weight: 700;
}}

.content {{
  padding: 32px;
}}

.heading {{
  color: #8b949e;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1.4px;
  font-weight: 700;
  margin-bottom: 26px;
}}

.db {{
  border: 1px solid #30363d;
  border-radius: 12px;
  background: #0d1117;
  padding: 22px;
  margin-bottom: 24px;
}}

.db-title {{
  color: #58a6ff;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 16px;
}}

.row {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 14px;
}}

.field {{
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 15px;
}}

.field-name {{
  color: #8b949e;
  font-size: 12px;
  margin-bottom: 7px;
}}

.field-value {{
  color: #e6edf3;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 16px;
  font-weight: 700;
}}

.version {{
  color: #d29922;
}}

.flow {{
  display: grid;
  grid-template-columns: 1fr 60px 1fr;
  align-items: center;
  gap: 10px;
}}

.transaction {{
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 20px;
  background: #0d1117;
}}

.transaction-title {{
  color: #c9d1d9;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 14px;
}}

.step {{
  color: #8b949e;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 13px;
  line-height: 1.8;
}}

.highlight {{
  color: #58a6ff;
}}

.arrow {{
  color: #8b949e;
  font-size: 27px;
  text-align: center;
}}

.result {{
  margin-top: 24px;
  padding: 18px 20px;
  border: 1px solid #238636;
  background: rgba(35, 134, 54, .10);
  border-radius: 10px;
  color: #3fb950;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 14px;
  font-weight: 700;
}}

.footer {{
  padding: 15px 22px;
  border-top: 1px solid #30363d;
  color: #8b949e;
  text-align: center;
  font-size: 12px;
}}
</style>
</head>

<body>
<div class="window">

  <div class="titlebar">
    <div class="dot red"></div>
    <div class="dot yellow"></div>
    <div class="dot green"></div>
    <div class="title">Optimistic Locking</div>
  </div>

  <div class="content">
    <div class="heading">Concurrency Control</div>

    <div class="db">
      <div class="db-title">orders</div>
      <div class="row">
        <div class="field">
          <div class="field-name">order_id</div>
          <div class="field-value">ORD-4821</div>
        </div>
        <div class="field">
          <div class="field-name">status</div>
          <div class="field-value">pending</div>
        </div>
        <div class="field">
          <div class="field-name">version</div>
          <div class="field-value version">{version}</div>
        </div>
      </div>
    </div>

    <div class="flow">
      <div class="transaction">
        <div class="transaction-title">Transaction A</div>
        <div class="step">1. Read version <span class="highlight">{version}</span></div>
        <div class="step">2. Modify order</div>
        <div class="step">3. UPDATE ... WHERE version = <span class="highlight">{version}</span></div>
      </div>

      <div class="arrow">→</div>

      <div class="transaction">
        <div class="transaction-title">Transaction B</div>
        <div class="step">1. Read version <span class="highlight">{version}</span></div>
        <div class="step">2. Modify order</div>
        <div class="step">3. Version changed</div>
      </div>
    </div>

    <div class="result">
      ✓ A succeeds → version increments to {next_version}
      &nbsp;&nbsp; | &nbsp;&nbsp;
      B affects 0 rows → retry / conflict
    </div>
  </div>

  <div class="footer">
    Don't overwrite someone else's update just because you read the same row.
  </div>

</div>
</body>
</html>
"""


def generate_concurrency(mode, version, output):
    if mode != "optimistic-lock":
        raise ValueError(
            "This generator currently supports only: optimistic-lock"
        )

    try:
        version = int(version)
    except ValueError:
        raise ValueError("--version must be an integer")

    next_version = version + 1

    page_html = HTML_TEMPLATE.format(
        version=html.escape(str(version)),
        next_version=html.escape(str(next_version))
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
            viewport={"width": 1000, "height": 720},
            device_scale_factor=2
        )

        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)

        window = page.query_selector(".window")
        window.screenshot(path=output)

        browser.close()

    print(f"✅ Concurrency image saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate concurrency-control diagrams"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["optimistic-lock"]
    )

    parser.add_argument(
        "--output",
        default="concurrency.png"
    )

    parser.add_argument(
        "--version",
        default="1"
    )

    args = parser.parse_args()

    generate_concurrency(
        mode=args.mode,
        version=args.version,
        output=args.output
    )
