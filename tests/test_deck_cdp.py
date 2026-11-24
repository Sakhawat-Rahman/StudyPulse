import subprocess, time, json, urllib.request, base64, os
import tornado.websocket, tornado.ioloop
from PIL import Image

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
html_path = r"file:///G:/ADHD app/studypulse.html"
out_dir = r"G:\ADHD app\showcase_pitch_deck"
user_data = r"G:\ADHD app\scratch\chrome_pitch_deck_profile"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(user_data, exist_ok=True)

specs = [
    {
        "id": "01_dashboard_command_center_light",
        "title": "Command Center Dashboard — Clean Daytime Light Mode",
        "theme": "light",
        "view": "dashboard",
        "width": 1440,
        "height": 900
    },
    {
        "id": "02_dashboard_command_center_dark",
        "title": "Command Center Dashboard — Carbon Obsidian Dark Mode",
        "theme": "dark",
        "view": "dashboard",
        "width": 1440,
        "height": 900
    }
]

async def run_test():
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
    try:
        await tornado.gen.sleep(2.5)
        with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
            tabs = json.loads(resp.read().decode())
        target = [t for t in tabs if "studypulse.html" in t.get("url", "")][0]
        ws = await tornado.websocket.websocket_connect(target["webSocketDebuggerUrl"])

        for sp in specs:
            # 1. Metrics override
            req_emul = {
                "id": 1,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {
                    "width": sp["width"],
                    "height": sp["height"],
                    "deviceScaleFactor": 2,
                    "mobile": False
                }
            }
            await ws.write_message(json.dumps(req_emul))
            await ws.read_message()

            # 2. Config JS
            is_dark = (sp["theme"] == "dark")
            js = f"""
            (() => {{
                setDarkMode({str(is_dark).lower()});
                if (typeof switchView === 'function') switchView('{sp["view"]}');
            }})()
            """
            req_js = {"id": 2, "method": "Runtime.evaluate", "params": {"expression": js}}
            await ws.write_message(json.dumps(req_js))
            await ws.read_message()

            # Wait for repaint
            await tornado.gen.sleep(0.5)

            # 3. Screenshot
            req_shot = {"id": 3, "method": "Page.captureScreenshot", "params": {"format": "png"}}
            await ws.write_message(json.dumps(req_shot))
            msg = await ws.read_message()
            res = json.loads(msg)
            img_bytes = base64.b64decode(res["result"]["data"])

            out_file = os.path.join(out_dir, f"{sp['id']}.png")
            with open(out_file, "wb") as f:
                f.write(img_bytes)

            im = Image.open(out_file)
            print(f"[OK] {sp['id']}.png ({im.size}) - {len(img_bytes)} bytes")

        ws.close()
    finally:
        proc.terminate()

tornado.ioloop.IOLoop.current().run_sync(run_test)
