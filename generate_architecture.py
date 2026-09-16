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
      width: 1120px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.55);
    }

    .titlebar {
      background: #21262d;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid #30363d;
    }

    .dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }

    .red { background: #ff5f56; }
    .yellow { background: #ffbd2e; }
    .green { background: #27c93f; }

    .title {
      margin-left: 12px;
      color: #e6edf3;
      font-size: 15px;
      font-weight: 600;
    }

    .content {
      padding: 34px;
    }

    .panel {
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 12px;
      overflow: hidden;
    }

    .panel-header {
      padding: 18px 22px;
      background: #21262d;
      border-bottom: 1px solid #30363d;
      color: #e6edf3;
      font-size: 17px;
      font-weight: 700;
    }

    .panel-body {
      padding: 32px;
    }

    /* Event-driven layout */
    .event-layout {
      display: grid;
      grid-template-columns: 1fr 180px 1fr;
      grid-template-rows: auto auto auto;
      column-gap: 24px;
      row-gap: 18px;
      align-items: center;
    }

    .service {
      min-height: 82px;
      padding: 18px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      color: #e6edf3;
      text-align: center;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 7px;
    }

    .service-name {
      color: #e6edf3;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 14px;
      font-weight: 700;
    }

    .service-meta {
      color: #8b949e;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 12px;
    }

    .producer {
      grid-column: 1;
      grid-row: 1;
    }

    .publish-arrow {
      grid-column: 2;
      grid-row: 1;
      text-align: center;
      color: #58a6ff;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 13px;
      font-weight: 700;
    }

    .publish-arrow .arrow {
      color: #58a6ff;
      font-size: 28px;
      margin-top: 5px;
    }

    .broker {
      grid-column: 1 / 4;
      grid-row: 2;
      width: 68%;
      justify-self: center;
      padding: 22px;
      background: #21262d;
      border: 1px solid #58a6ff;
      border-radius: 11px;
      text-align: center;
    }

    .broker-title {
      color: #58a6ff;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 15px;
      font-weight: 700;
    }

    .broker-meta {
      margin-top: 7px;
      color: #8b949e;
      font-size: 12px;
    }

    .consumer-left {
      grid-column: 1;
      grid-row: 3;
    }

    .consumer-right {
      grid-column: 3;
      grid-row: 3;
    }

    .consume-arrow-left,
    .consume-arrow-right {
      grid-row: 3;
      color: #3fb950;
      text-align: center;
      font-size: 28px;
    }

    .consume-arrow-left {
      grid-column: 2;
    }

    .consume-arrow-right {
      display: none;
    }

    .consumers {
      grid-column: 1 / 4;
      grid-row: 3;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      position: relative;
    }

    .consumers .service {
      min-height: 82px;
    }

    .fanout {
      text-align: center;
      margin: 20px 0;
      color: #8b949e;
      font-size: 13px;
    }

    .description {
      margin-top: 24px;
      color: #8b949e;
      font-size: 12px;
      line-height: 1.7;
      text-align: center;
    }

    .footer {
      padding: 18px 24px;
      background: #0d1117;
      border-top: 1px solid #30363d;
      color: #8b949e;
      text-align: center;
      font-size: 12px;
    }

    /* Comparison layout */
    .comparison {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }

    .comparison .panel {
      background: #0d1117;
    }

    .comparison-body {
      padding: 24px;
    }

    .node {
      padding: 14px 16px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 9px;
      color: #c9d1d9;
      text-align: center;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 13px;
    }

    .comparison .arrow {
      text-align: center;
      color: #8b949e;
      font-size: 20px;
      padding: 8px 0;
    }

    .comparison-description {
      margin-top: 18px;
      color: #8b949e;
      font-size: 12px;
      line-height: 1.6;
      text-align: center;
    }

    .module-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }

    .module {
      padding: 20px 16px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      color: #c9d1d9;
      text-align: center;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 14px;
      font-weight: 600;
    }

    .distributed-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }

    .distributed-service {
      padding: 18px 14px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      color: #c9d1d9;
      text-align: center;
      font-family: "SF Mono", "Fira Code", Menlo, monospace;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="titlebar">
      <div class="dot red"></div>
      <div class="dot yellow"></div>
      <div class="dot green"></div>
      <div class="title">{title}</div>
    </div>

    {content}

    <div class="footer">{footer}</div>
  </div>
</body>
</html>
"""


def build_event_driven_content():
    return """
    <div class="content">
      <div class="panel">
        <div class="panel-header">Event-Driven Communication</div>

        <div class="panel-body">
          <div class="event-layout">

            <div class="service producer">
              <div class="service-name">Order Service</div>
              <div class="service-meta">produces OrderCreated</div>
            </div>

            <div class="publish-arrow">
              publish event
              <div class="arrow">→</div>
            </div>

            <div class="broker">
              <div class="broker-title">EVENT BUS / MESSAGE BROKER</div>
              <div class="broker-meta">OrderCreated</div>
            </div>

          </div>

          <div class="fanout">event delivered to interested consumers</div>

          <div class="consumers">
            <div class="service">
              <div class="service-name">Payment Service</div>
              <div class="service-meta">consumes OrderCreated</div>
            </div>

            <div class="service">
              <div class="service-name">Notification Service</div>
              <div class="service-meta">consumes OrderCreated</div>
            </div>
          </div>

          <div class="description">
            The producer does not need to know which services consume the event.
            Consumers can react independently.
          </div>
        </div>
      </div>
    </div>
    """


def build_comparison_content():
    return """
    <div class="content">
      <div class="comparison">
        <div class="panel">
          <div class="panel-header">Monolith</div>
          <div class="comparison-body">
            <div class="node">Users</div>
            <div class="arrow">↓</div>
            <div class="node">Orders</div>
            <div class="arrow">↓</div>
            <div class="node">Payments</div>
            <div class="arrow">↓</div>
            <div class="node">Database</div>
            <div class="comparison-description">
              One deployable application<br>
              Shared runtime and database
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">Microservices</div>
          <div class="comparison-body">
            <div class="node">Users Service → Users DB</div>
            <div class="node" style="margin-top:12px;">Orders Service → Orders DB</div>
            <div class="node" style="margin-top:12px;">Payments Service → Payments DB</div>
            <div class="comparison-description">
              Multiple deployable services<br>
              Services communicate over the network
            </div>
          </div>
        </div>
      </div>
    </div>
    """


def build_modular_monolith_content(nodes):
    modules = "".join(
        f'<div class="module">{html.escape(node)}</div>'
        for node in nodes
    )

    return f"""
    <div class="content">
      <div class="panel">
        <div class="panel-header">Modular Monolith</div>
        <div class="panel-body">
          <div class="module-grid">{modules}</div>
          <div class="description">
            One deployable application with clear internal module boundaries.
          </div>
        </div>
      </div>
    </div>
    """


def build_distributed_monolith_content():
    return """
    <div class="content">
      <div class="panel">
        <div class="panel-header">Distributed Monolith</div>
        <div class="panel-body">
          <div class="distributed-grid">
            <div class="distributed-service">Users Service</div>
            <div class="distributed-service">Orders Service</div>
            <div class="distributed-service">Payments Service</div>
          </div>

          <div class="arrow" style="text-align:center;color:#8b949e;font-size:20px;padding:14px;">↓</div>

          <div class="node">Synchronous Network Calls</div>

          <div class="arrow" style="text-align:center;color:#8b949e;font-size:20px;padding:14px;">↓</div>

          <div class="node">Shared Database</div>

          <div class="description">
            Multiple deployable services<br>
            Tightly coupled through synchronous calls and shared state
          </div>
        </div>
      </div>
    </div>
    """


def generate_architecture(
    title="Monolith vs Microservices",
    output="architecture.png",
    mode="comparison",
    nodes=None,
):
    if mode == "event-driven":
        content = build_event_driven_content()
        footer = "Publish events. Let interested consumers react independently."

    elif mode == "modular_monolith":
        content = build_modular_monolith_content(
            nodes or ["Orders", "Payments", "Users", "Catalog", "Billing"]
        )
        footer = "One application. Clear module boundaries. Independent internal domains."

    elif mode == "distributed-monolith":
        content = build_distributed_monolith_content()
        footer = "Distributed deployment does not automatically mean loosely coupled architecture."

    else:
        content = build_comparison_content()
        footer = "Different trade-offs. Neither architecture is automatically better."

    page_html = HTML_TEMPLATE
    page_html = page_html.replace("{title}", html.escape(title))
    page_html = page_html.replace("{content}", content)
    page_html = page_html.replace("{footer}", footer)

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
            viewport={"width": 1200, "height": 1000},
            device_scale_factor=2
        )

        page.goto(f"file://{html_path}")
        page.wait_for_timeout(300)

        element = page.query_selector(".card")
        element.screenshot(path=output)

        browser.close()

    print(f"✅ Architecture image saved → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate architecture images for X posts"
    )

    parser.add_argument(
        "--title",
        default="Monolith vs Microservices"
    )

    parser.add_argument(
        "--output",
        default="architecture.png"
    )

    parser.add_argument(
        "--mode",
        default="comparison",
        choices=[
            "comparison",
            "modular_monolith",
            "distributed-monolith",
            "event-driven"
        ]
    )

    parser.add_argument(
        "--nodes",
        default="Orders,Payments,Users,Catalog,Billing",
        help="Comma-separated module names for modular_monolith mode"
    )

    args = parser.parse_args()

    nodes = [node.strip() for node in args.nodes.split(",") if node.strip()]

    generate_architecture(
        args.title,
        args.output,
        args.mode,
        nodes
    )
