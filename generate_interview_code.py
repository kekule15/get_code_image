#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import argparse, tempfile, html, re

PRESETS = {
    "upload-streaming": ("javascript", "Backend Interview", '''app.post("/upload", async (req, res) => {
  const video = req.file;
  await processVideo(video.path);
  res.json({ message: "Upload complete" });
});''', "RED FLAG", "500 MB × 100 concurrent uploads = a memory problem."),
    "upload-streaming-fix": ("javascript", "Backend Interview", '''app.post("/upload", async (req, res) => {
  const key = await streamToObjectStorage(req);
  await enqueueVideoProcessing(key);
  res.status(202).json({ status: "processing" });
});''', "ALTERNATIVE", "Stream uploads, store them externally, and process asynchronously."),
    "parallel-fetch": ("javascript", "Backend Interview", '''async function fetchAllData(urls) {
  const results = [];
  for (const url of urls) {
    const response = await fetch(url);
    results.push(await response.json());
  }
  return results;
}''', "BOTTLENECK", "Independent I/O should not wait for the previous request."),
    "parallel-fetch-fix": ("javascript", "Senior Software Interview", '''async function fetchAllData(urls) {
  const responses = await Promise.all(
    urls.map(url => fetch(url))
  );
  return Promise.all(
    responses.map(response => response.json())
  );
}''', "OPTIMIZE", "Run independent I/O concurrently — with a concurrency limit when required."),
    "notification-batch": ("javascript", "Backend Interview", '''async function sendNotifications(users) {
  for (const user of users) {
    await sendNotification(user.id);
  }
}''', "BOTTLENECK", "5,000 × 200ms = 1,000 seconds when every job waits."),
    "notification-queue": ("typescript", "NestJS + BullMQ", '''await notificationQueue.add(
  "send-notification",
  { userId, templateId },
  {
    attempts: 3,
    backoff: { type: "exponential", delay: 1000 }
  }
);''', "ALTERNATIVE", "Move slow, retryable work out of the request-response path."),
    "race-condition": ("typescript", "Senior Software Interview", '''const account = await db.account.findUnique({
  where: { id: accountId }
});

if (account.balance >= amount) {
  await db.account.update({
    where: { id: accountId },
    data: { balance: account.balance - amount }
  });
}''', "RACE CONDITION", "Two requests can read the same state before either write."),
    "n-plus-one": ("typescript", "Database Interview", '''const users = await prisma.user.findMany();

for (const user of users) {
  const orders = await prisma.order.findMany({
    where: { userId: user.id }
  });
}''', "RED FLAG", "1 query for users + N queries for orders."),
    "prisma-include": ("typescript", "Prisma", '''const users = await prisma.user.findMany({
  include: {
    orders: true
  }
});''', "ALTERNATIVE", "Ask whether the ORM can fetch relations without a query per row."),
    "select-star": ("sql", "Database Interview", '''SELECT *
FROM users
WHERE status = 'active'
ORDER BY created_at DESC;''', "RED FLAG", "Do you really need every column?"),
    "indexed-function": ("sql", "Database Interview", '''SELECT *
FROM users
WHERE LOWER(email) = 'user@example.com';''', "RED FLAG", "You indexed the column. Then you wrapped it in a function."),
    "pagination": ("typescript", "API Design Interview", '''const users = await prisma.user.findMany({
  skip: page * limit,
  take: limit
});''', "QUESTION", "What happens when page becomes 100,000?"),
    "cursor-pagination": ("typescript", "API Design Interview", '''const users = await prisma.user.findMany({
  take: 50,
  skip: 1,
  cursor: { id: lastSeenId },
  orderBy: { id: "asc" }
});''', "ALTERNATIVE", "For large datasets, cursor pagination can avoid expensive offsets."),
    "jsonb": ("sql", "PostgreSQL Interview", '''CREATE TABLE events (
  id UUID PRIMARY KEY,
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);''', "DESIGN QUESTION", "What belongs in relational columns, and what belongs in JSONB?"),
    "foreign-key": ("sql", "Database Interview", '''CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);''', "DESIGN QUESTION", "A foreign key is a database-enforced integrity rule."),
    "unique-key": ("sql", "Database Interview", '''CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL
);''', "DESIGN QUESTION", "If email must be unique, should the database enforce it?"),
    "uuid": ("sql", "Database Interview", '''CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  amount BIGINT NOT NULL
);''', "QUESTION", "UUIDs have different trade-offs from sequential identifiers."),
    "http-timeout": ("typescript", "API Reliability", '''const response = await fetch(
  paymentServiceUrl,
  {
    method: "POST",
    body: JSON.stringify(payload)
  }
);''', "RED FLAG", "What happens when the dependency never responds?"),
    "idempotency": ("typescript", "Payments Interview", '''await payments.create({
  amount: 50000,
  currency: "NGN",
  idempotencyKey: requestId
});''', "SENIOR QUESTION", "If a client retries after a timeout, can the payment happen twice?"),
    "bullmq": ("typescript", "NestJS + BullMQ", '''await this.notificationQueue.add(
  "email",
  { userId, template: "welcome" }
);

// Worker handles delivery separately.''', "ARCHITECTURE", "The API should not wait for every notification provider."),
    "db-event": ("typescript", "Event-Driven Backend", '''await db.order.create({
  data: { userId, total }
});

// publish: OrderCreated
// consumers:
//   Payment
//   Notification
//   Analytics''', "ARCHITECTURE", "A database change can become an event other services react to."),
    "async-await": ("javascript", "Spot the Bug", '''users.forEach(async user => {
  await sendNotification(user.id);
});

console.log("Done");''', "RED FLAG", "forEach does not await your async callback."),
    "react-effect": ("tsx", "React Interview", '''useEffect(() => {
  fetchUser(userId);
}, []);''', "SPOT THE BUG", "What happens when userId changes?"),
    "flutter-build": ("dart", "Flutter Interview", '''Widget build(BuildContext context) {
  final future = api.fetchUsers();

  return FutureBuilder(
    future: future,
    builder: (_, snapshot) => UsersList(snapshot.data),
  );
}''', "RED FLAG", "Creating async work inside build() can trigger repeated work."),
    "python-mutable-default": ("python", "Python Interview", '''def add_item(item, items=[]):
    items.append(item)
    return items

print(add_item("A"))
print(add_item("B"))''', "SPOT THE BUG", "Mutable default arguments are shared between calls."),
    "node-event-loop": ("javascript", "Node.js Interview", '''app.get("/report", (req, res) => {
  const report = generateHugeReport();
  res.json(report);
});''', "RED FLAG", "CPU-heavy synchronous work blocks the event loop."),
    "distributed-chain": ("typescript", "Senior Architecture Interview", '''const order = await orders.create(data);
const payment = await payments.charge(order.id);
await notifications.send(payment.userId);
return order;''', "BOTTLENECK", "One slow dependency can increase the latency of the entire request."),
    "distributed-chain-fix": ("typescript", "Senior Architecture Interview", '''const order = await orders.create(data);

await events.publish("OrderCreated", {
  orderId: order.id
});

return { status: "accepted", orderId: order.id };''', "ALTERNATIVE", "Do not make users wait for work that does not need to be synchronous."),
}

KEYWORDS = set("const let var function async await return if else for while new throw try catch finally class extends import from export default of in interface type public private readonly implements def elif except with yield raise and or not is SELECT FROM WHERE INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE PRIMARY KEY FOREIGN REFERENCES UNIQUE NOT NULL ORDER BY GROUP LIMIT OFFSET JOIN LEFT RIGHT INNER ON AS AND OR DESC ASC DEFAULT ALTER INDEX final void required late true false null None True False using foreach static string int bool Task".split())

def highlight(code):
    pattern = r'(//[^\n]*|#[^\n]*|--[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b)'
    out=[]; last=0
    for m in re.finditer(pattern, code):
        out.append(html.escape(code[last:m.start()]))
        t=m.group(0); s=html.escape(t); c=None
        if t.startswith(("//","#","--","/*")): c="comment"
        elif t.startswith(("'",'"',"`")): c="string"
        elif t[0].isdigit(): c="number"
        elif t in KEYWORDS: c="keyword"
        elif t in {"Promise","JSON","Math","Array","Object","Task","Error","console"}: c="builtin"
        out.append(f'<span class="{c}">{s}</span>' if c else s)
        last=m.end()
    out.append(html.escape(code[last:])); return ''.join(out)

def render(code,title,badge,footer,output,width=980):
    rows=[]
    for i,line in enumerate(highlight(code).split("\\n"),1):
        rows.append(f'<div class="line"><span class="num">{i:>2}</span><span class="code">{line or "&nbsp;"}</span></div>')

    badge_html=f'<div class="badge">{html.escape(badge.upper())}</div>' if badge else ''

    template = """<!doctype html><html><head><meta charset=\"utf-8\"><style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#0d1117; padding:42px; font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif; }}
.window {{ width:{width}px; background:#161b22; border:1px solid #30363d; border-radius:16px; overflow:hidden; box-shadow:0 25px 60px rgba(0,0,0,.55); }}
.bar {{ height:62px; background:#21262d; border-bottom:1px solid #30363d; display:flex; align-items:center; padding:0 22px; gap:10px; }}
.dot {{ width:14px; height:14px; border-radius:50%; }}
.r {{ background:#ff5f56; }} .y {{ background:#ffbd2e; }} .g {{ background:#27c93f; }}
.title {{ margin-left:12px; color:#e6edf3; font:700 15px \"SF Mono\",\"Fira Code\",Menlo,monospace; }}
.badge {{ margin-left:auto; color:#f85149; border:1px solid #f85149; border-radius:7px; padding:7px 11px; font:700 10px \"SF Mono\",\"Fira Code\",Menlo,monospace; letter-spacing:.8px; }}
.editor {{ background:#0d1117; padding:30px 28px 34px; }}
.line {{ display:flex; min-height:32px; font:15px/1.55 \"SF Mono\",\"Fira Code\",\"JetBrains Mono\",Menlo,monospace; white-space:pre-wrap; overflow-wrap:anywhere; }}
.num {{ flex:0 0 42px; color:#484f58; text-align:right; padding-right:22px; }}
.code {{ color:#e6edf3; flex:1; min-width:0; }}
.keyword {{ color:#ff7b72; }} .string {{ color:#a5d6ff; }} .number {{ color:#79c0ff; }} .builtin {{ color:#d2a8ff; }} .comment {{ color:#8b949e; }}
.footer {{ background:#161b22; border-top:1px solid #30363d; padding:16px 24px; color:#8b949e; font-size:12px; line-height:1.5; text-align:center; }}
</style></head><body><div class=\"window\"><div class=\"bar\"><div class=\"dot r\"></div><div class=\"dot y\"></div><div class=\"dot g\"></div><div class=\"title\">{title}</div>{badge}</div><div class=\"editor\">{rows}</div><div class=\"footer\">{footer}</div></div></body></html>"""

    page=template.format(
        width=width,
        title=html.escape(title),
        badge=badge_html,
        rows="".join(rows),
        footer=html.escape(footer)
    )

    with tempfile.NamedTemporaryFile(mode='w',suffix='.html',delete=False,encoding='utf-8') as f:
        f.write(page)
        fn=f.name

    with sync_playwright() as p:
        browser=p.chromium.launch()
        page = browser.new_page(
        viewport={"width": width + 84, "height": 1000},
        device_scale_factor=2
       )
        page.goto('file://'+fn)
        page.wait_for_timeout(200)
        window = page.query_selector(".window")
        window.screenshot(path=output)
        browser.close()

    print(f'✅ Code image saved → {output}')

def main():
    ap=argparse.ArgumentParser(description='Generate X-ready engineering code images')
    ap.add_argument('--preset',choices=sorted(PRESETS)); ap.add_argument('--lang',default='javascript'); ap.add_argument('--title',default='Senior Software Interview'); ap.add_argument('--code'); ap.add_argument('--badge',default='QUESTION'); ap.add_argument('--footer',default=''); ap.add_argument('--output',default='code_snippet.png'); ap.add_argument('--width',type=int,default=980)
    args=ap.parse_args()
    if args.preset: lang,title,code,badge,footer=PRESETS[args.preset]
    elif args.code: lang,title,code,badge,footer=args.lang,args.title,args.code,args.badge,args.footer
    else: ap.error('Provide --code or use --preset.')
    render(code.replace('\\n','\n'),title,badge,footer,args.output,args.width)

if __name__=='__main__': main()
