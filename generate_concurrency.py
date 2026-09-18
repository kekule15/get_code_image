from playwright.sync_api import sync_playwright
import tempfile
import argparse
import html

STYLE = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; padding: 42px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.window { width: 920px; background: #161b22; border: 1px solid #30363d; border-radius: 16px; overflow: hidden; box-shadow: 0 24px 60px rgba(0,0,0,.5); }
.titlebar { height: 52px; background: #21262d; border-bottom: 1px solid #30363d; display: flex; align-items: center; padding: 0 18px; gap: 8px; }
.dot { width: 13px; height: 13px; border-radius: 50%; }.red { background:#ff5f56; }.yellow{background:#ffbd2e;}.green{background:#27c93f;}
.title { margin-left:12px; color:#e6edf3; font:700 14px "SF Mono","Fira Code",Menlo,monospace; }
.content { padding:32px; }.heading { color:#8b949e; font-size:13px; text-transform:uppercase; letter-spacing:1.4px; font-weight:700; margin-bottom:26px; }
.flow { display:grid; grid-template-columns:1fr 58px 1fr; align-items:center; gap:12px; }.card { min-height:245px; border:1px solid #30363d; border-radius:12px; padding:22px; background:#0d1117; }
.card-title { color:#e6edf3; font-size:18px; font-weight:750; margin-bottom:18px; }.step { color:#8b949e; font:13px/2 "SF Mono","Fira Code",Menlo,monospace; }
.highlight{color:#58a6ff}.warning{color:#d29922}.danger{color:#f85149}.success{color:#3fb950}.muted{color:#8b949e}.arrow{color:#8b949e;font-size:27px;text-align:center}
.bottom{margin-top:24px;border:1px solid #30363d;border-radius:12px;background:#0d1117;padding:22px}.bottom-title{color:#c9d1d9;font-size:14px;font-weight:700;margin-bottom:14px}.code{color:#c9d1d9;font:13px/1.8 "SF Mono","Fira Code",Menlo,monospace;white-space:pre-wrap}
.footer{padding:15px 22px;border-top:1px solid #30363d;color:#8b949e;text-align:center;font-size:12px}
'''

TIMEOUT_HTML='''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style}</style></head><body><div class="window"><div class="titlebar"><div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div><div class="title">{title}</div></div><div class="content"><div class="heading">Concurrency &amp; Async Control</div><div class="flow"><div class="card"><div class="card-title">Client</div><div class="step">1. Send request</div><div class="step">2. Wait <span class="highlight">5s</span></div><div class="step">3. <span class="warning">Timeout</span></div><div class="step">4. Stop waiting</div></div><div class="arrow">→</div><div class="card"><div class="card-title">Server</div><div class="step">1. Request already running</div><div class="step">2. Continue processing</div><div class="step">3. Database work</div><div class="step">4. <span class="danger">No cancellation signal</span></div></div></div><div class="bottom"><div class="bottom-title">The distinction</div><div class="code"><span class="warning">Timeout</span>      = <span class="muted">"I stopped waiting."</span>\n<span class="danger">Cancellation</span>  = <span class="muted">"Stop the work too."</span></div></div></div><div class="footer">A client timeout does not automatically cancel work already running on the server.</div></div></body></html>'''

OPTIMISTIC_HTML='''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style}</style></head><body><div class="window"><div class="titlebar"><div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div><div class="title">Optimistic Locking</div></div><div class="content"><div class="heading">Concurrency Control</div><div class="bottom"><div class="bottom-title">orders</div><div class="code">order_id   = ORD-4821\nstatus     = pending\nversion    = <span class="warning">{version}</span></div></div><div class="flow"><div class="card"><div class="card-title">Transaction A</div><div class="step">1. Read version <span class="highlight">{version}</span></div><div class="step">2. Modify order</div><div class="step">3. UPDATE WHERE version = <span class="highlight">{version}</span></div><div class="step"><span class="success">✓ Update succeeds</span></div></div><div class="arrow">→</div><div class="card"><div class="card-title">Transaction B</div><div class="step">1. Read version <span class="highlight">{version}</span></div><div class="step">2. Modify order</div><div class="step">3. Version changed</div><div class="step"><span class="danger">✕ Update affects 0 rows</span></div></div></div><div class="bottom"><div class="code"><span class="highlight">A succeeds</span> → version becomes {next_version}\n<span class="warning">B detects conflict</span> → retry or return conflict</div></div></div><div class="footer">Optimistic locking prevents a stale write from silently overwriting a newer one.</div></div></body></html>'''

RACE_HTML='''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style}</style></head><body><div class="window"><div class="titlebar"><div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div><div class="title">{title}</div></div><div class="content"><div class="heading">Concurrent Requests</div><div class="flow"><div class="card"><div class="card-title">{task_a}</div><div class="step">1. Read balance</div><div class="step">2. Balance = <span class="highlight">$100</span></div><div class="step">3. Calculate new value</div><div class="step">4. Write <span class="warning">$40</span></div></div><div class="arrow">↕</div><div class="card"><div class="card-title">{task_b}</div><div class="step">1. Read balance</div><div class="step">2. Balance = <span class="highlight">$100</span></div><div class="step">3. Calculate new value</div><div class="step">4. Write <span class="warning">$60</span></div></div></div><div class="bottom"><div class="bottom-title">What went wrong?</div><div class="code"><span class="highlight">Both requests read the same state.</span>\n<span class="danger">The last write wins.</span>\n<span class="muted">One update can silently overwrite the other.</span></div></div></div><div class="footer">Race conditions happen when concurrent operations access shared state without proper coordination.</div></div></body></html>'''

def render(source, output):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(source); filename=f.name
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1020,'height':800}, device_scale_factor=2)
        page.goto('file://' + filename); page.wait_for_timeout(250)
        page.query_selector('.window').screenshot(path=output)
        browser.close()

def main():
    parser=argparse.ArgumentParser(description='Generate concurrency diagrams')
    parser.add_argument('--mode', required=True, choices=['optimistic-lock','timeout','race'])
    parser.add_argument('--output', default='concurrency.png')
    parser.add_argument('--version', default='1')
    parser.add_argument('--title', default='Concurrency Control')
    parser.add_argument('--task', action='append', default=[])
    args=parser.parse_args()
    if args.mode=='timeout':
        source=TIMEOUT_HTML.format(style=STYLE, title=html.escape(args.title))
    elif args.mode=='optimistic-lock':
        v=int(args.version)
        source=OPTIMISTIC_HTML.format(style=STYLE, version=v, next_version=v+1)
    else:
        tasks=args.task[:2]
        while len(tasks)<2: tasks.append(f'Request {chr(65+len(tasks))}')
        source=RACE_HTML.format(style=STYLE, title=html.escape(args.title), task_a=html.escape(tasks[0]), task_b=html.escape(tasks[1]))
    render(source,args.output)
    print(f'✅ Concurrency image saved → {args.output}')

if __name__=='__main__': main()
