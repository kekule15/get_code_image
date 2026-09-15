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

    .card {
      width: 900px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
    }

    .header {
      background: #21262d;
      padding: 18px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #30363d;
    }

    .title {
      color: #e6edf3;
      font-size: 17px;
      font-weight: 700;
    }

    .subtitle {
      color: #8b949e;
      font-size: 12px;
    }

    .body {
      padding: 30px;
    }

    .total {
      color: #58a6ff;
      font-size: 42px;
      font-weight: 700;
      margin-bottom: 5px;
    }

    .total-label {
      color: #8b949e;
      font-size: 13px;
      margin-bottom: 30px;
    }

    .timeline {
      position: relative;
    }

    .row {
      display: grid;
      grid-template-columns: 190px 1fr 90px;
      align-items: center;
      gap: 16px;
      margin-bottom: 22px;
    }

    .name {
      color: #e6edf3;
      font-size: 14px;
      font-weight: 600;
    }

    .bar-area {
      height: 32px;
      background: #21262d;
      border-radius: 7px;
      overflow: hidden;
      position: relative;
    }

    .bar {
      height: 100%;
      border-radius: 7px;
    }

    .dns { background: #a371f7; }
    .connect { background: #3fb950; }
    .tls { background: #d29922; }
    .wait { background: #f85149; }
    .transfer { background: #58a6ff; }

    .value {
      color: #8b949e;
      font-size: 13px;
      text-align: right;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
    }

    .ttfb {
      margin-top: 8px;
      padding: 18px 20px;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .ttfb-label {
      color: #c9d1d9;
      font-size: 14px;
      font-weight: 600;
    }

    .ttfb-value {
      color: #f85149;
      font-size: 20px;
      font-weight: 700;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
    }

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
      <div class="title">API Request Waterfall</div>
      <div class="subtitle">TIME TO FIRST BYTE</div>
    </div>

    <div class="body">
      <div class="total">{ttfb} ms</div>
      <div class="total-label">Time to First Byte (TTFB)</div>

      <div class="timeline">
        <div class="row">
          <div class="name">DNS Lookup</div>
          <div class="bar-area"><div class="bar dns" style="width:{dns_pct}%"></div></div>
          <div class="value">{dns} ms</div>
        </div>

        <div class="row">
          <div class="name">TCP Connection</div>
          <div class="bar-area"><div class="bar connect" style="width:{connect_pct}%"></div></div>
          <div class="value">{connect} ms</div>
        </div>

        <div class="row">
          <div class="name">TLS Handshake</div>
          <div class="bar-area"><div class="bar tls" style="width:{tls_pct}%"></div></div>
          <div class="value">{tls} ms</div>
        </div>

        <div class="row">
          <div class="name">Server Wait / Processing</div>
          <div class="bar-area"><div class="bar wait" style="width:{wait_pct}%"></div></div>
          <div class="value">{wait} ms</div>
        </div>

        <div class="row">
          <div class="name">Content Transfer</div>
          <div class="bar-area"><div class="bar transfer" style="width:{transfer_pct}%"></div></div>
          <div class="value">{transfer} ms</div>
        </div>

        <div class="ttfb">
          <div class="ttfb-label">TTFB (through server processing)</div>
          <div class="ttfb-value">{ttfb} ms</div>
        </div>
      </div>
    </div>

    <div class="footer">
      TTFB ends when the first byte of the response arrives.
    </div>
  </div>
</body>
</html>
"""


def generate_waterfall(
    dns,
    connect,
    tls,
    wait,
    transfer,
    output="waterfall.png"
):
    ttfb = dns + connect + tls + wait
    total = ttfb + transfer

    scale_total = max(total, 1)

    values = {
        "dns": dns,
        "connect": connect,
        "tls": tls,
        "wait": wait,
        "transfer": transfer,
    }

    percentages = {
        key: round(value / scale_total * 100, 2)
        for key, value in values.items()
    }

    page_html = HTML_TEMPLATE

    page_html = page_html.replace("{ttfb}", str(ttfb))
    page_html = page_html.replace("{dns}", str(dns))
    page_html = page_html.replace("{connect}", str(connect))
    page_html = page_html.replace("{tls}", str(tls))
    page_html = page_html.replace("{wait}", str(wait))
    page_html = page_html.replace("{transfer}", str(transfer))

    page_html = page_html.replace("{dns_pct}", str(percentages["dns"]))
    page_html = page_html.replace("{connect_pct}", str(percentages["connect"]))
    page_html = page_html.replace("{tls_pct}", str(percentages["tls"]))
    page_html = page_html.replace("{wait_pct}", str(percentages["wait"]))
    page_html = page_html.replace("{transfer_pct}", str(percentages["transfer"]))

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
            viewport={"width": 1000, "height": 900},
            device_scale_factor=2
        )

        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)

        element = page.query_selector(".card")
        element.screenshot(path=output)

        browser.close()

    print(f"✅ Waterfall image saved → {output}")
    print(f"   TTFB: {ttfb} ms")
    print(f"   Total response time: {total} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate API waterfall / TTFB images for X posts"
    )

    parser.add_argument("--dns", type=int, default=12)
    parser.add_argument("--connect", type=int, default=28)
    parser.add_argument("--tls", type=int, default=45)
    parser.add_argument("--wait", type=int, default=1400)
    parser.add_argument("--transfer", type=int, default=20)
    parser.add_argument("--output", default="waterfall.png")

    args = parser.parse_args()

    generate_waterfall(
        args.dns,
        args.connect,
        args.tls,
        args.wait,
        args.transfer,
        args.output
    )
