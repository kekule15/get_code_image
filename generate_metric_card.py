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
  padding: 48px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

.card {{
  width: 760px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 18px;
  padding: 34px 38px;
  box-shadow: 0 25px 60px rgba(0,0,0,.45);
}}

.header {{
  color: #8b949e;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 20px;
}}

.metric {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;
}}

.label {{
  color: #c9d1d9;
  font-size: 20px;
  font-weight: 600;
}}

.value {{
  color: #3fb950;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: .5px;
}}

.status {{
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid #30363d;
  color: #f85149;
  font-family: "SF Mono", "Fira Code", Menlo, monospace;
  font-size: 17px;
  font-weight: 700;
}}

.indicator {{
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #f85149;
  display: inline-block;
  margin-right: 10px;
  vertical-align: middle;
}}
</style>
</head>

<body>
  <div class="card">
    <div class="header">{title}</div>

    <div class="metric">
      <div class="label">{metric}</div>
      <div class="value">{value}</div>
    </div>

    <div class="status">
      <span class="indicator"></span>{status}
    </div>
  </div>
</body>
</html>
"""


def generate_metric_card(
    title: str,
    metric: str,
    value: str,
    status: str,
    output: str
):
    page_html = HTML_TEMPLATE.format(
        title=html.escape(title),
        metric=html.escape(metric),
        value=html.escape(value),
        status=html.escape(status)
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
            viewport={"width": 860, "height": 500},
            device_scale_factor=2
        )

        page.goto(f"file://{html_path}")
        page.wait_for_timeout(250)

        card = page.query_selector(".card")
        card.screenshot(path=output)

        browser.close()

    print(f"✅ Metric card saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a dark technical metric card"
    )

    parser.add_argument("--title", default="Metric")
    parser.add_argument("--output", default="metric_card.png")
    parser.add_argument("--metric", required=True)
    parser.add_argument("--value", required=True)
    parser.add_argument("--status", required=True)

    args = parser.parse_args()

    generate_metric_card(
        title=args.title,
        metric=args.metric,
        value=args.value,
        status=args.status,
        output=args.output
    )
