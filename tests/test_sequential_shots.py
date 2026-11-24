import subprocess, time, json, urllib.request, base64, os
import tornado.websocket, tornado.ioloop
from PIL import Image

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
html_path = r"file:///G:/ADHD app/studypulse.html"
out_dir = r"G:\ADHD app\scratch\test_inc"
user_data = r"G:\ADHD app\scratch\chrome_inc_profile"
os.makedirs(out_dir, exist_ok=True)

proc = subprocess.Popen([
    chrome_path,
    "--headless=new",
    f"--user-data-dir={user_data}",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-debugging-port=9222",
    "--disable-gpu",
    html_path
])

time.sleep(2.5)

async def run():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        tabs = json.loads(resp.read().decode())
    target = [t for t in tabs if "studypulse.html" in t.get("url", "")][0]
    ws = await tornado.websocket.websocket_connect(target["webSocketDebuggerUrl"])

    msg_id = 0
    async def send(method, params=None):
        nonlocal msg_id
        msg_id += 1
        req = {"id": msg_id, "method": method}
        if params: req["params"] = params
        await ws.write_message(json.dumps(req))
        while True:
            raw = await ws.read_message()
            res = json.loads(raw)
            if res.get("id") == msg_id:
                return res

    # 1. Light mode
    await send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 2, "mobile": False})
    await send("Runtime.evaluate", {"expression": "setDarkMode(false); if (typeof switchView === 'function') switchView('dashboard');"})
    await tornado.gen.sleep(0.5)
    r1 = await send("Page.captureScreenshot", {"format": "png"})
    b1 = base64.b64decode(r1["result"]["data"])
    p1 = os.path.join(out_dir, "01_light.png")
    with open(p1, "wb") as f: f.write(b1)
    im1 = Image.open(p1)
    print("Light screenshot:", im1.size, len(b1), "bytes, pixel (100, 100):", im1.getpixel((100, 100)))

    # 2. Dark mode
    await send("Runtime.evaluate", {"expression": "setDarkMode(true); if (typeof switchView === 'function') switchView('dashboard');"})
    await tornado.gen.sleep(0.5)
    r2 = await send("Page.captureScreenshot", {"format": "png"})
    b2 = base64.b64decode(r2["result"]["data"])
    p2 = os.path.join(out_dir, "02_dark.png")
    with open(p2, "wb") as f: f.write(b2)
    im2 = Image.open(p2)
    print("Dark screenshot:", im2.size, len(b2), "bytes, pixel (100, 100):", im2.getpixel((100, 100)))

    ws.close()

try:
    tornado.ioloop.IOLoop.current().run_sync(run)
finally:
    proc.terminate()
