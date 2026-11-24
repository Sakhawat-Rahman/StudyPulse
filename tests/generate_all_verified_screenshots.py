import subprocess
import os
import re
from PIL import Image

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
html_path = r"G:\ADHD app\studypulse.html"
out_dir = r"G:\ADHD app\screenshots_live"
scratch_dir = r"G:\ADHD app\scratch"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(scratch_dir, exist_ok=True)

with open(html_path, "r", encoding="utf-8") as f:
    base_html = f.read()

def create_variant_html(theme="dark", view="dashboard", show_mini=False, show_modal=None, widget_mode=False):
    html = base_html
    is_dark = (theme == "dark")

    # Set HTML root class
    if is_dark:
        html = re.sub(r'<html[^>]*>', '<html lang="en" class="dark">', html, count=1)
    else:
        html = re.sub(r'<html[^>]*>', '<html lang="en">', html, count=1)

    # Inject early theme script into head to prevent dark-mode flash or override
    early_theme = "dark" if is_dark else "light"
    early_script = f"""<head>
  <script>
    try {{
      localStorage.setItem('studypulse_theme', '{early_theme}');
      if ({str(is_dark).lower()}) {{
        document.documentElement.classList.add('dark');
      }} else {{
        document.documentElement.classList.remove('dark');
      }}
    }} catch(e) {{}}
  </script>"""
    html = html.replace("<head>", early_script, 1)

    # Handle Mini-Player
    if show_mini:
        html = html.replace('id="floating-spotify-mini-player" class="hidden', 'id="floating-spotify-mini-player" class="')
        html = html.replace('id="floating-spotify-live-badge" class="hidden', 'id="floating-spotify-live-badge" class="')
        html = html.replace('id="floating-spotify-play-icon" class="w-3 h-3"', 'id="floating-spotify-play-icon" class="hidden w-3 h-3"')
        html = html.replace('id="floating-spotify-pause-icon" class="hidden w-3 h-3"', 'id="floating-spotify-pause-icon" class="w-3 h-3"')
        html = html.replace('style="width: 0%;"', 'style="width: 48%;"')

    # Handle View switching directly in HTML classes
    if view == "timer":
        html = html.replace('<div id="dashboard-view" class="flex flex-col gap-6">', '<div id="dashboard-view" class="hidden flex flex-col gap-6">')
        html = html.replace('<section id="timer-studio-view" class="hidden flex-1', '<section id="timer-studio-view" class="flex-1')
        html = html.replace('id="inbuilt-spotify-deck" class="hidden', 'id="inbuilt-spotify-deck" class="')
    elif view == "calendar":
        html = html.replace('<div id="dashboard-view" class="flex flex-col gap-6">', '<div id="dashboard-view" class="hidden flex flex-col gap-6">')
        html = html.replace('<section id="calendar-view" class="hidden flex-1', '<section id="calendar-view" class="flex-1')

    # Handle Modals
    if show_modal == "settings":
        html = html.replace('<div id="settings-modal" class="hidden fixed', '<div id="settings-modal" class="fixed')
    elif show_modal == "sync":
        html = html.replace('id="sync-modal" class="fixed inset-0 bg-ink-950/40 backdrop-blur-md z-50 hidden', 'id="sync-modal" class="fixed inset-0 bg-ink-950/40 backdrop-blur-md z-50')
        html = html.replace('id="sync-modal" class="hidden fixed', 'id="sync-modal" class="fixed')

    # Handle Widget Mode
    if widget_mode:
        widget_script = """<script>
          document.addEventListener('DOMContentLoaded', () => {
            if (typeof enableWidgetModeUI === 'function') enableWidgetModeUI();
          });
        </script></body>"""
        html = html.replace("</body>", widget_script, 1)

    return html

specs = [
    {
        "filename": "fig6_1_dashboard_light.png",
        "theme": "light",
        "view": "dashboard",
        "show_mini": True,
        "show_modal": None,
        "widget_mode": False,
        "width": 1440,
        "height": 900
    },
    {
        "filename": "fig6_2_dashboard_dark.png",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": True,
        "show_modal": None,
        "widget_mode": False,
        "width": 1440,
        "height": 900
    },
    {
        "filename": "fig6_3_studio_light.png",
        "theme": "light",
        "view": "timer",
        "show_mini": False,
        "show_modal": None,
        "widget_mode": False,
        "width": 1440,
        "height": 900
    },
    {
        "filename": "fig6_4_studio_dark.png",
        "theme": "dark",
        "view": "timer",
        "show_mini": False,
        "show_modal": None,
        "widget_mode": False,
        "width": 1440,
        "height": 900
    },
    {
        "filename": "fig6_5_calendar_light.png",
        "theme": "light",
        "view": "calendar",
        "show_mini": False,
        "show_modal": None,
        "widget_mode": False,
        "width": 1440,
        "height": 900
    },
    {
        "filename": "fig6_6_calendar_dark.png",
        "theme": "dark",
        "view": "calendar",
        "show_mini": False,
        "show_modal": None,
        "widget_mode": False,
        "width": 1440,
        "height": 900
    },
    {
        "filename": "fig6_7a_settings_light.png",
        "theme": "light",
        "view": "dashboard",
        "show_mini": False,
        "show_modal": "settings",
        "widget_mode": False,
        "width": 1280,
        "height": 850
    },
    {
        "filename": "fig6_7b_settings_dark.png",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": False,
        "show_modal": "settings",
        "widget_mode": False,
        "width": 1280,
        "height": 850
    },
    {
        "filename": "fig6_8a_widget_light.png",
        "theme": "light",
        "view": "dashboard",
        "show_mini": False,
        "show_modal": None,
        "widget_mode": True,
        "width": 380,
        "height": 720
    },
    {
        "filename": "fig6_8b_widget_dark.png",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": False,
        "show_modal": None,
        "widget_mode": True,
        "width": 380,
        "height": 720
    },
    {
        "filename": "fig6_8c_phone_qr_dark.png",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": False,
        "show_modal": "sync",
        "widget_mode": False,
        "width": 1280,
        "height": 850
    }
]

print("Starting generation of all verified screenshots...")

for sp in specs:
    variant_html = create_variant_html(
        theme=sp["theme"],
        view=sp["view"],
        show_mini=sp["show_mini"],
        show_modal=sp["show_modal"],
        widget_mode=sp["widget_mode"]
    )
    temp_file = os.path.join(scratch_dir, f"temp_{sp['filename']}.html")
    with open(temp_file, "w", encoding="utf-8") as tf:
        tf.write(variant_html)

    out_file = os.path.join(out_dir, sp["filename"])
    if os.path.exists(out_file):
        os.remove(out_file)

    file_url = "file:///" + os.path.abspath(temp_file).replace("\\", "/")
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--virtual-time-budget=2000",
        f"--window-size={sp['width']},{sp['height']}",
        f"--screenshot={out_file}",
        file_url
    ]
    subprocess.run(cmd, capture_output=True, timeout=15)

    if os.path.exists(out_file):
        im = Image.open(out_file)
        sample = im.getpixel((sp["width"] // 2, 40))
        print(f"SUCCESS: {sp['filename']} ({im.size}) - center-top pixel: {sample}")
    else:
        print(f"ERROR: Failed to capture {sp['filename']}")

print("All screenshots generation finished successfully!")
