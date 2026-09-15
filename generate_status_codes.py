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
    body { background:#0d1117; padding:48px; display:flex; justify-content:center; align-items:center; min-height:100vh; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .card { width:860px; background:#161b22; border:1px solid #30363d; border-radius:16px; overflow:hidden; box-shadow:0 25px 60px rgba(0,0,0,.55); }
    .titlebar { background:#21262d; padding:15px 18px; display:flex; align-items:center; gap:8px; border-bottom:1px solid #30363d; }
    .dot { width:12px; height:12px; border-radius:50%; }
    .red { background:#ff5f56; } .yellow { background:#ffbd2e; } .green { background:#27c93f; }
    .title { margin-left:12px; color:#8b949e; font-size:13px; font-weight:600; }
    .body { padding:28px; }
    .grid { display:grid; grid-template-columns:90px 1fr; gap:1px; background:#30363d; border:1px solid #30363d; border-radius:10px; overflow:hidden; }
    .code,.meaning { padding:17px 20px; background:#0d1117; }
    .code { color:#58a6ff; font-family:"SF Mono","Fira Code",Menlo,monospace; font-size:15px; font-weight:700; }
    .meaning { color:#c9d1d9; font-size:14px; }
    .footer { margin-top:20px; color:#8b949e; font-size:12px; text-align:center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="titlebar">
      <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
      <div class="title">{title}</div>
    </div>
    <div class="body">
      <div class="grid">{rows}</div>
      <div class="footer">Choose the status code that describes what actually happened.</div>
    </div>
  </div>
</body>
</html>
"""

DEFAULT_CODES = [
    ("200", "OK — request succeeded"),
    ("201", "Created — resource created"),
    ("204", "No Content — succeeded without a response body"),
    ("400", "Bad Request — invalid request"),
    ("401", "Unauthorized — authentication required"),
    ("403", "Forbidden — authenticated but not allowed"),
    ("404", "Not Found — resource does not exist"),
    ("409", "Conflict — request conflicts with current state"),
    ("422", "Unprocessable Content — validation failed"),
    ("500", "Internal Server Error — unexpected server failure"),
]


def generate_status_codes(codes, output="http_status_codes.png", title="HTTP STATUS CODES"):
    rows = "".join(
        f'<div class="code">{html.escape(code)}</div>'
        f'<div class="meaning">{html.escape(meaning)}</div>'
        for code, meaning in codes
    )

    page_html = HTML_TEMPLATE.replace("{rows}", rows).replace("{title}", html.escape(title))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page_html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width":1000,"height":1000}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)
        page.query_selector(".card").screenshot(path=output)
        browser.close()

    print(f"✅ HTTP status codes image saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTTP status code images for X posts")
    parser.add_argument("--output", default="http_status_codes.png")
    parser.add_argument("--title", default="HTTP STATUS CODES")
    parser.add_argument("--codes", help='Custom codes: "200|OK;201|Created;404|Not Found"')
    args = parser.parse_args()

    if args.codes:
        codes = [(item.split("|", 1)[0].strip(), item.split("|", 1)[1].strip()) for item in args.codes.split(";")]
    else:
        codes = DEFAULT_CODES

    generate_status_codes(codes, args.output, args.title)