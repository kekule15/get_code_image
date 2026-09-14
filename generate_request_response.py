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
    .container {
      width: 900px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
    }
    .titlebar {
      background: #21262d;
      padding: 14px 18px;
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
      margin-left: 12px;
      color: #8b949e;
      font-size: 13px;
      font-weight: 600;
    }
    .section { padding: 26px 28px; }
    .section + .section { border-top: 1px solid #30363d; }
    .section-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    .method, .status {
      font-size: 12px;
      font-weight: 700;
      color: #ffffff;
      background: #238636;
      padding: 5px 9px;
      border-radius: 6px;
    }
    .endpoint {
      color: #e6edf3;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 14px;
      font-weight: 600;
    }
    .label {
      color: #8b949e;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
    }
    pre {
      margin: 0;
      padding: 20px;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 10px;
      color: #c9d1d9;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .arrow {
      text-align: center;
      color: #8b949e;
      font-size: 20px;
      padding: 4px 0;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="titlebar">
      <div class="dot red"></div>
      <div class="dot yellow"></div>
      <div class="dot green"></div>
      <div class="title">API REQUEST / RESPONSE</div>
    </div>
    <div class="section">
      <div class="section-header">
        <span class="method">{method}</span>
        <span class="endpoint">{endpoint}</span>
      </div>
      <div class="label">Request</div>
      <pre>{request}</pre>
    </div>
    <div class="arrow">↓</div>
    <div class="section">
      <div class="section-header">
        <span class="status">{status}</span>
      </div>
      <div class="label">Response</div>
      <pre>{response}</pre>
    </div>
  </div>
</body>
</html>
"""


def generate_request_response(method, endpoint, request, status, response, output="request_response.png"):
    content = HTML_TEMPLATE
    content = content.replace("{method}", html.escape(method))
    content = content.replace("{endpoint}", html.escape(endpoint))
    content = content.replace("{status}", html.escape(status))
    content = content.replace("{request}", html.escape(request))
    content = content.replace("{response}", html.escape(response))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(content)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 1100}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)
        element = page.query_selector(".container")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ Request/Response image saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate API request/response images for X posts")
    parser.add_argument("--method", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--output", default="request_response.png")
    args = parser.parse_args()

    request = args.request.replace("\\n", "\n")
    response = args.response.replace("\\n", "\n")

    generate_request_response(
        args.method,
        args.endpoint,
        request,
        args.status,
        response,
        args.output,
    )
