from playwright.sync_api import sync_playwright
import tempfile
import argparse
import html

HTML_TEMPLATE = """

<!DOCTYPE html>
<html>

<head>
    <meta charset='UTF-8'>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0
        }

        body {
            background: #0d1117;
            padding: 48px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
        }

        .card {
            width: 1120px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 25px 60px rgba(0, 0, 0, .55)
        }

        .titlebar {
            background: #21262d;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #30363d
        }

        .dot {
            width: 12px;
            height: 12px;
            border-radius: 50%
        }

        .red {
            background: #ff5f56
        }

        .yellow {
            background: #ffbd2e
        }

        .green {
            background: #27c93f
        }

        .title {
            margin-left: 12px;
            color: #e6edf3;
            font-size: 15px;
            font-weight: 600
        }

        .content {
            padding: 32px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px
        }

        .panel {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 12px;
            overflow: hidden
        }

        .panel-header {
            padding: 18px 20px;
            background: #21262d;
            border-bottom: 1px solid #30363d;
            color: #e6edf3;
            font-size: 17px;
            font-weight: 700
        }

        .panel-body {
            padding: 24px
        }

        .node {
            padding: 14px 16px;
            margin-bottom: 12px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 9px;
            color: #c9d1d9;
            text-align: center;
            font-family: 'SF Mono', 'Fira Code', Menlo, monospace;
            font-size: 13px
        }

        .arrow {
            text-align: center;
            color: #8b949e;
            font-size: 18px;
            margin: 4px 0 10px
        }

        .description {
            margin-top: 18px;
            color: #8b949e;
            font-size: 12px;
            line-height: 1.6;
            text-align: center
        }

        .footer {
            padding: 18px 24px;
            background: #0d1117;
            border-top: 1px solid #30363d;
            color: #8b949e;
            text-align: center;
            font-size: 12px
        }
    </style>
</head>

<body>
    <div class='card'>
        <div class='titlebar'>
            <div class='dot red'></div>
            <div class='dot yellow'></div>
            <div class='dot green'></div>
            <div class='title'>{title}</div>
        </div>
        <div class='content'>
            <div class='panel'>
                <div class='panel-header'>Monolith</div>
                <div class='panel-body'>
                    <div class='node'>Users</div>
                    <div class='arrow'>↓</div>
                    <div class='node'>Orders</div>
                    <div class='arrow'>↓</div>
                    <div class='node'>Payments</div>
                    <div class='arrow'>↓</div>
                    <div class='node'>Database</div>
                    <div class='description'>One deployable application<br>Shared runtime and database</div>
                </div>
            </div>
            <div class='panel'>
                <div class='panel-header'>Microservices</div>
                <div class='panel-body'>
                    <div class='node'>Users Service → Users DB</div>
                    <div class='node'>Orders Service → Orders DB</div>
                    <div class='node'>Payments Service → Payments DB</div>
                    <div class='description'>Multiple deployable services<br>Services communicate over the network</div>
                </div>
            </div>
        </div>
        <div class='footer'>Different trade-offs. Neither architecture is automatically better.</div>
    </div>
</body>

</html>


"""

def generate_architecture(title='Monolith vs Microservices', output='architecture.png', mode='comparison'):
    page_html = HTML_TEMPLATE.replace('{title}', html.escape(title))
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(page_html); html_path=f.name
    with sync_playwright() as p:
        browser=p.chromium.launch(); page=browser.new_page(viewport={'width':1200,'height':900},device_scale_factor=2)
        page.goto(f'file://{html_path}'); page.wait_for_timeout(300)
        page.query_selector('.card').screenshot(path=output); browser.close()
    print(f'✅ Architecture image saved → {output}')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Generate architecture comparison images for X posts')
    parser.add_argument('--title',default='Monolith vs Microservices'); parser.add_argument('--output',default='architecture.png'); parser.add_argument('--mode',default='comparison',choices=['comparison'])
    args=parser.parse_args(); generate_architecture(args.title,args.output,args.mode)
