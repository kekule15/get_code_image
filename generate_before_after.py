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
      padding: 50px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .card {
      background: #161b22;
      border-radius: 18px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
      width: 560px;
      overflow: hidden;
      border: 1px solid #30363d;
    }
    .header {
      background: #21262d;
      padding: 16px 24px;
      color: #e6edf3;
      font-size: 15px;
      font-weight: 600;
      border-bottom: 1px solid #30363d;
    }
    .body {
      padding: 32px 28px;
      display: flex;
      gap: 20px;
    }
    .box {
      flex: 1;
      background: #0d1117;
      border-radius: 12px;
      padding: 24px 16px;
      text-align: center;
      border: 1px solid #30363d;
    }
    .label {
      font-size: 13px;
      color: #8b949e;
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .value {
      font-size: 36px;
      font-weight: 700;
    }
    .before .value { color: #f85149; }
    .after .value { color: #3fb950; }
    .improvement {
      margin-top: 28px;
      text-align: center;
      padding: 0 28px 32px;
    }
    .badge {
      display: inline-block;
      background: #238636;
      color: white;
      font-size: 18px;
      font-weight: 700;
      padding: 10px 22px;
      border-radius: 30px;
    }
    .subtitle {
      margin-top: 12px;
      color: #8b949e;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">{title}</div>
    <div class="body">
      <div class="box before">
        <div class="label">Before</div>
        <div class="value">{before}</div>
      </div>
      <div class="box after">
        <div class="label">After</div>
        <div class="value">{after}</div>
      </div>
    </div>
    <div class="improvement">
      <div class="badge">{improvement}</div>
      <div class="subtitle">{subtitle}</div>
    </div>
  </div>
</body>
</html>
"""

def generate_before_after(before, after, unit="ms", title="API Response Time", output="before_after.png"):
    before_val = float(before)
    after_val = float(after)
    
    if after_val == 0:
        improvement = "∞× faster"
    else:
        times = round(before_val / after_val, 1)
        percent = round((1 - after_val / before_val) * 100)
        improvement = f"{times}× faster  •  {percent}% improvement"

    html = HTML_TEMPLATE
    html = html.replace("{title}", title)
    html = html.replace("{before}", f"{before} {unit}")
    html = html.replace("{after}", f"{after} {unit}")
    html = html.replace("{improvement}", improvement)
    html = html.replace("{subtitle}", "Same endpoint • Same data • One change")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 700, "height": 700}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(400)

        element = page.query_selector(".card")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ Before/After image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--unit", default="ms")
    parser.add_argument("--title", default="API Response Time")
    parser.add_argument("--output", default="before_after.png")
    args = parser.parse_args()

    generate_before_after(args.before, args.after, args.unit, args.title, args.output)