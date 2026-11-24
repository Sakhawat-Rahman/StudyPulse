import subprocess, time, json, urllib.request
import tornado.websocket, tornado.ioloop

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
html = "file:///G:/ADHD app/studypulse.html"
user_data = r"G:\ADHD app\scratch\chrome_profile"

proc = subprocess.Popen([
    chrome,
    "--headless=new",
    f"--user-data-dir={user_data}",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-debugging-port=9222",
    "--disable-gpu",
    html
])

time.sleep(2.5)

async def check():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        tabs = json.loads(resp.read().decode())
    target = [t for t in tabs if "studypulse.html" in t.get("url", "")][0]
    ws = await tornado.websocket.websocket_connect(target["webSocketDebuggerUrl"])
    
    expr = """
    (() => {
        const appRoot = document.getElementById('app-root');
        const dash = document.getElementById('dashboard-view');
        return JSON.stringify({
            appRootRect: appRoot ? { w: appRoot.offsetWidth, h: appRoot.offsetHeight, top: appRoot.offsetTop } : null,
            dashRect: dash ? { w: dash.offsetWidth, h: dash.offsetHeight } : null,
            bodyH: document.body.offsetHeight,
            bodyW: document.body.offsetWidth,
            cardsCount: document.querySelectorAll('.glass-card').length,
            tailwindLoaded: typeof tailwind !== 'undefined',
            stateLoaded: typeof state !== 'undefined',
            goalsCount: (typeof state !== 'undefined' && state.goals) ? state.goals.length : -1
        });
    })()
    """
    req = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr}}
    await ws.write_message(json.dumps(req))
    msg = await ws.read_message()
    res = json.loads(msg)
    print("CDP Result:", res.get("result", {}).get("result", {}).get("value"))
    ws.close()

try:
    tornado.ioloop.IOLoop.current().run_sync(check)
finally:
    proc.terminate()
