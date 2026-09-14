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
      border-radius: 16px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
      width: 520px;
      overflow: hidden;
      border: 1px solid #30363d;
    }
    .header {
      background: #21262d;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #30363d;
    }
    .header-title {
      color: #e6edf3;
      font-size: 15px;
      font-weight: 600;
    }
    .status {
      background: #238636;
      color: white;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 20px;
    }
    .body {
      padding: 28px 24px;
    }
    .total {
      font-size: 42px;
      font-weight: 700;
      color: #58a6ff;
      margin-bottom: 6px;
    }
    .total-label {
      color: #8b949e;
      font-size: 13px;
      margin-bottom: 28px;
    }
    .bar-section {
      margin-bottom: 22px;
    }
    .bar-label {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 13px;
    }
    .bar-name { color: #e6edf3; }
    .bar-value { color: #8b949e; }
    .bar-bg {
      height: 10px;
      background: #21262d;
      border-radius: 6px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      border-radius: 6px;
    }
    .dns { background: #a371f7; }
    .connect { background: #3fb950; }
    .tls { background: #d29922; }
    .transfer { background: #58a6ff; }
    .wait { background: #f85149; }
    .footer {
      padding: 16px 24px;
      background: #0d1117;
      border-top: 1px solid #30363d;
      color: #8b949e;
      font-size: 12px;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="header-title">Response Timing</div>
      <div class="status">200 OK</div>
    </div>
    <div class="body">
      <div class="total">{total} ms</div>
      <div class="total-label">Total response time</div>

      <div class="bar-section">
        <div class="bar-label">
          <span class="bar-name">DNS Lookup</span>
          <span class="bar-value">{dns} ms</span>
        </div>
        <div class="bar-bg"><div class="bar-fill dns" style="width: {dns_pct}%"></div></div>
      </div>

      <div class="bar-section">
        <div class="bar-label">
          <span class="bar-name">TCP Connection</span>
          <span class="bar-value">{connect} ms</span>
        </div>
        <div class="bar-bg"><div class="bar-fill connect" style="width: {connect_pct}%"></div></div>
      </div>

      <div class="bar-section">
        <div class="bar-label">
          <span class="bar-name">TLS Handshake</span>
          <span class="bar-value">{tls} ms</span>
        </div>
        <div class="bar-bg"><div class="bar-fill tls" style="width: {tls_pct}%"></div></div>
      </div>

      <div class="bar-section">
        <div class="bar-label">
          <span class="bar-name">Server Processing (Wait)</span>
          <span class="bar-value">{wait} ms</span>
        </div>
        <div class="bar-bg"><div class="bar-fill wait" style="width: {wait_pct}%"></div></div>
      </div>

      <div class="bar-section">
        <div class="bar-label">
          <span class="bar-name">Content Transfer</span>
          <span class="bar-value">{transfer} ms</span>
        </div>
        <div class="bar-bg"><div class="bar-fill transfer" style="width: {transfer_pct}%"></div></div>
      </div>
    </div>
    <div class="footer">Simulated Postman / Thunder Client breakdown</div>
  </div>
</body>
</html>
"""

def generate_timing(dns, connect, tls, wait, transfer, output="timing.png"):
    total = dns + connect + tls + wait + transfer
    # Avoid division by zero
    total = max(total, 1)

    html = HTML_TEMPLATE
    html = html.replace("{total}", str(total))
    html = html.replace("{dns}", str(dns))
    html = html.replace("{connect}", str(connect))
    html = html.replace("{tls}", str(tls))
    html = html.replace("{wait}", str(wait))
    html = html.replace("{transfer}", str(transfer))

    html = html.replace("{dns_pct}", str(round(dns / total * 100, 1)))
    html = html.replace("{connect_pct}", str(round(connect / total * 100, 1)))
    html = html.replace("{tls_pct}", str(round(tls / total * 100, 1)))
    html = html.replace("{wait_pct}", str(round(wait / total * 100, 1)))
    html = html.replace("{transfer_pct}", str(round(transfer / total * 100, 1)))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 700, "height": 900}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(400)

        element = page.query_selector(".card")
        element.screenshot(path=output)
        browser.close()

    print(f"✅ Timing image saved → {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Postman-style timing image")
    parser.add_argument("--dns", type=int, default=12)
    parser.add_argument("--connect", type=int, default=28)
    parser.add_argument("--tls", type=int, default=45)
    parser.add_argument("--wait", type=int, default=210)
    parser.add_argument("--transfer", type=int, default=18)
    parser.add_argument("--output", default="timing.png")
    args = parser.parse_args()

    generate_timing(args.dns, args.connect, args.tls, args.wait, args.transfer, args.output)