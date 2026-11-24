import subprocess, time, json, urllib.request, base64, os
import tornado.websocket, tornado.ioloop
from PIL import Image
from generate_pitch_deck_showcase import pitch_deck_specs, create_deck_variant_html

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out_dir = r"G:\ADHD app\scratch\cdp_verify"
scratch_dir = r"G:\ADHD app\scratch\cdp_html"
user_data = r"G:\ADHD app\scratch\chrome_cdp_verify_profile"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(scratch_dir, exist_ok=True)

test_items = [pitch_deck_specs[0], pitch_deck_specs[1]] # 01 light and 02 dark

async def run_cdp():
    # Start Chrome with remote debugging
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        f"--user-data-dir={user_data}",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        "about:blank"
    ])
    try:
        await tornado.gen.sleep(2.0)
        with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
            tabs = json.loads(resp.read().decode())
        target = tabs[0]
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

        for item in test_items:
            file_id = item["id"]
            temp_file = os.path.join(scratch_dir, f"test_{file_id}.html")
            variant_html = create_deck_variant_html(item)
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(variant_html)

            file_url = "file:///" + os.path.abspath(temp_file).replace("\\", "/")

            # Set viewport metrics
            await send("Emulation.setDeviceMetricsOverride", {
                "width": item["width"],
                "height": item["height"],
                "deviceScaleFactor": 2,
                "mobile": False
            })

            # Navigate to page
            await send("Page.navigate", {"url": file_url})

            # Wait 1.0 second for DOMContentLoaded, Tailwind CDN, and initial layout
            await tornado.gen.sleep(1.2)

            # Capture screenshot
            shot_res = await send("Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(shot_res["result"]["data"])
            out_file = os.path.join(out_dir, f"{file_id}.png")
            with open(out_file, "wb") as f:
                f.write(img_bytes)

            im = Image.open(out_file)
            print(f"[OK] {file_id}.png: size={im.size}, bytes={len(img_bytes)}")
            # Verify card colors
            # In light mode (01), center of card is light (~250)
            # In dark mode (02), center of card is dark (~22)
            sample_pt = im.getpixel((600, 600))
            print(f"     Sample pixel at (600, 600): {sample_pt}")

        ws.close()
    finally:
        proc.terminate()

tornado.ioloop.IOLoop.current().run_sync(run_cdp)
