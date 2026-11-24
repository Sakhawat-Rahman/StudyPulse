import subprocess
import os
import re
import time
from PIL import Image

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
html_path = r"G:\ADHD app\studypulse.html"
out_dir = r"G:\ADHD app\showcase_pitch_deck"
scratch_dir = r"G:\ADHD app\scratch\pitch_deck_html"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(scratch_dir, exist_ok=True)

with open(html_path, "r", encoding="utf-8") as f:
    base_html = f.read()

def create_deck_variant_html(config):
    theme = config.get("theme", "dark")
    is_dark = (theme == "dark")
    view = config.get("view", "dashboard")
    show_mini = config.get("show_mini", False)
    mini_compact = config.get("mini_compact", False)
    modal = config.get("modal", None)
    widget_mode = config.get("widget_mode", False)
    expand_deck = config.get("expand_deck", False)
    music_playing = config.get("music_playing", False)

    html = base_html

    # 1. Clean root HTML tag & theme setup
    if is_dark:
        html = re.sub(r'<html[^>]*>', '<html lang="en" class="dark">', html, count=1)
    else:
        html = re.sub(r'<html[^>]*>', '<html lang="en">', html, count=1)

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

    # 2. View Selection (Direct HTML unhiding)
    if view == "timer":
        html = html.replace('<div id="dashboard-view" class="flex flex-col gap-6">', '<div id="dashboard-view" class="hidden flex flex-col gap-6">')
        html = html.replace('<section id="timer-studio-view" class="hidden flex-1', '<section id="timer-studio-view" class="flex-1')
    elif view == "calendar":
        html = html.replace('<div id="dashboard-view" class="flex flex-col gap-6">', '<div id="dashboard-view" class="hidden flex flex-col gap-6">')
        html = html.replace('<section id="calendar-view" class="hidden flex-1', '<section id="calendar-view" class="flex-1')

    # 3. Floating Mini-Player
    if show_mini:
        if mini_compact:
            # Compressed Mode (176px width, compact body visible)
            html = html.replace(
                'id="floating-spotify-mini-player" data-alias="spotify-floating-mini" style="border-radius: 18px !important; overflow: hidden !important; background-clip: padding-box !important; isolation: isolate !important; border: 1px solid rgba(255, 255, 255, 0.14) !important; box-shadow: 0 10px 28px -6px rgba(0, 0, 0, 0.22), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset !important;" class="hidden fixed bottom-6 left-20 z-50 w-[360px]',
                'id="floating-spotify-mini-player" data-alias="spotify-floating-mini" style="border-radius: 18px !important; overflow: hidden !important; background-clip: padding-box !important; isolation: isolate !important; border: 1px solid rgba(255, 255, 255, 0.14) !important; box-shadow: 0 10px 28px -6px rgba(0, 0, 0, 0.22), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset !important;" class="fixed bottom-8 right-8 z-50 w-[176px]'
            )
            html = html.replace('id="floating-spotify-standard-body" class="flex flex-col gap-2.5"', 'id="floating-spotify-standard-body" class="hidden flex-col gap-2.5"')
            html = html.replace('id="floating-spotify-compact-body" class="hidden flex-col gap-2"', 'id="floating-spotify-compact-body" class="flex flex-col gap-2"')
            html = html.replace('id="floating-spotify-focus-jump-btn" class="text-[10px]', 'id="floating-spotify-focus-jump-btn" class="hidden text-[10px]')
            html = html.replace('id="floating-spotify-compact-title" class="text-xs font-bold text-white truncate" style="text-shadow: 0 1px 3px rgba(0,0,0,0.7);">Spotify Player<', 'id="floating-spotify-compact-title" class="text-xs font-bold text-white truncate" style="text-shadow: 0 1px 3px rgba(0,0,0,0.7);">Teacher\'s Pet<')
            html = html.replace('id="floating-spotify-compact-artist" class="text-[10px] text-white/80 truncate mt-0.5">Focus Soundtrack<', 'id="floating-spotify-compact-artist" class="text-[10px] text-white/80 truncate mt-0.5">Melanie Martinez<')
        else:
            # Standard Pill Mode (360px width, standard body visible)
            html = html.replace(
                'id="floating-spotify-mini-player" data-alias="spotify-floating-mini" style="border-radius: 18px !important; overflow: hidden !important; background-clip: padding-box !important; isolation: isolate !important; border: 1px solid rgba(255, 255, 255, 0.14) !important; box-shadow: 0 10px 28px -6px rgba(0, 0, 0, 0.22), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset !important;" class="hidden fixed bottom-6 left-20 z-50 w-[360px]',
                'id="floating-spotify-mini-player" data-alias="spotify-floating-mini" style="border-radius: 18px !important; overflow: hidden !important; background-clip: padding-box !important; isolation: isolate !important; border: 1px solid rgba(255, 255, 255, 0.14) !important; box-shadow: 0 10px 28px -6px rgba(0, 0, 0, 0.22), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset !important;" class="fixed bottom-8 right-8 z-50 w-[360px]'
            )
            html = html.replace('id="floating-spotify-track-name" class="text-xs font-bold text-white truncate" style="text-shadow: 0 1px 2px rgba(0,0,0,0.4);">Spotify Player<', 'id="floating-spotify-track-name" class="text-xs font-bold text-white truncate" style="text-shadow: 0 1px 2px rgba(0,0,0,0.4);">Teacher\'s Pet<')
            html = html.replace('id="floating-spotify-artist-name" class="text-[10px] text-zinc-300 truncate font-medium">Focus Soundtrack<', 'id="floating-spotify-artist-name" class="text-[10px] text-zinc-300 truncate font-medium">Melanie Martinez<')
            html = html.replace('id="floating-spotify-time-current" class="tabular-nums">00:00<', 'id="floating-spotify-time-current" class="tabular-nums">01:08<')
            html = html.replace('id="floating-spotify-time-total" class="tabular-nums">00:00<', 'id="floating-spotify-time-total" class="tabular-nums">04:01<')
            html = html.replace('id="floating-spotify-progress" style="width: 0%;"', 'id="floating-spotify-progress" style="width: 28%;"')

    # 4. Modals
    if modal == "onething":
        html = html.replace(
            'id="onething-modal" data-alias="single-task-overlay" onclick="if(event.target===this)exitSingleTaskMode();" class="fixed inset-0 bg-ink-950/60 dark:bg-black/70 backdrop-blur-md z-[9999] hidden items-center justify-center p-4"',
            'id="onething-modal" data-alias="single-task-overlay" class="fixed inset-0 bg-ink-950/60 dark:bg-black/70 backdrop-blur-md z-[9999] flex items-center justify-center p-4"'
        )
    elif modal == "settings":
        html = html.replace(
            '<div id="settings-modal" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-ink-950/40 backdrop-blur-sm">',
            '<div id="settings-modal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-ink-950/40 backdrop-blur-sm">'
        )
    elif modal == "sync":
        html = html.replace(
            '<div id="sync-modal" class="fixed inset-0 bg-ink-950/40 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">',
            '<div id="sync-modal" class="fixed inset-0 bg-ink-950/40 backdrop-blur-md z-50 flex items-center justify-center p-4">'
        )

    # 5. Widget Mode
    if widget_mode:
        html = html.replace(
            '<body class="h-screen w-screen font-sans antialiased selection:bg-ink-950 selection:text-white p-0 m-0 bg-[#f4f4f6] text-ink-950 flex flex-col overflow-hidden">',
            '<body class="h-screen w-screen font-sans antialiased selection:bg-ink-950 selection:text-white p-0 m-0 bg-[#f4f4f6] text-ink-950 flex flex-col overflow-hidden widget-mode-active">'
        )
        html = html.replace(
            '<div id="app-root" class="w-full flex-1 flex flex-col p-3 sm:p-5 transition-all duration-300 overflow-y-auto">',
            '<div id="app-root" class="w-full flex-1 flex flex-col p-3 sm:p-5 transition-all duration-300 overflow-y-auto widget-container">'
        )

    # 6. DOM initialization bootstrap script
    post_script = f"""
    <script>
      document.addEventListener('DOMContentLoaded', () => {{
        try {{
          if (typeof setDarkMode === 'function') setDarkMode({str(is_dark).lower()});
          if ('{view}' !== 'dashboard' && typeof switchView === 'function') switchView('{view}');
          if ({str(widget_mode).lower()} && typeof enableWidgetModeUI === 'function') enableWidgetModeUI();
          if (typeof renderGoals === 'function') renderGoals();
          if (typeof renderEditorialMetrics === 'function') renderEditorialMetrics();
          if (typeof renderIroncladHabits === 'function') renderIroncladHabits();
          if (typeof renderHabitConsistencyChart === 'function') renderHabitConsistencyChart();
          if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
        }} catch(e) {{}}
      }});
    </script></body>"""
    html = html.replace("</body>", post_script, 1)

    return html

pitch_deck_specs = [
    {
        "id": "01_dashboard_command_center_light",
        "title": "Command Center Dashboard — Clean Light Mode",
        "theme": "light",
        "view": "dashboard",
        "show_mini": False,
        "width": 1440,
        "height": 900
    },
    {
        "id": "02_dashboard_command_center_dark",
        "title": "Command Center Dashboard — Carbon Obsidian Dark Mode",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": False,
        "width": 1440,
        "height": 900
    },
    {
        "id": "03_focus_timer_studio_light",
        "title": "Deep Focus Timer Studio — Clean Light Mode",
        "theme": "light",
        "view": "timer",
        "show_mini": False,
        "width": 1440,
        "height": 900
    },
    {
        "id": "04_focus_timer_studio_dark",
        "title": "Deep Focus Timer Studio — Carbon Obsidian Dark Mode",
        "theme": "dark",
        "view": "timer",
        "show_mini": False,
        "width": 1440,
        "height": 900
    },
    {
        "id": "05_spotify_hardware_console_deck",
        "title": "Integrated Spotify Hardware Deck & Web API Playlists Grid",
        "theme": "dark",
        "view": "timer",
        "expand_deck": True,
        "music_playing": True,
        "width": 1440,
        "height": 950
    },
    {
        "id": "06_mini_player_standard_pill",
        "title": "Magnetic Floating Mini-Player — Standard Pill Mode",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": True,
        "mini_compact": False,
        "music_playing": True,
        "width": 1440,
        "height": 900
    },
    {
        "id": "07_mini_player_compressed_album",
        "title": "Magnetic Floating Mini-Player — Compressed Album Mode",
        "theme": "dark",
        "view": "dashboard",
        "show_mini": True,
        "mini_compact": True,
        "music_playing": True,
        "width": 1440,
        "height": 900
    },
    {
        "id": "08_single_task_anti_paralysis",
        "title": "1-Thing Anti-Paralysis Mode — Instant Neurodivergent Focus",
        "theme": "dark",
        "view": "dashboard",
        "modal": "onething",
        "width": 1440,
        "height": 900
    },
    {
        "id": "09_monthly_study_calendar_dark",
        "title": "Visual Exam & Study Schedule Calendar — Dark Mode",
        "theme": "dark",
        "view": "calendar",
        "width": 1440,
        "height": 900
    },
    {
        "id": "10_monthly_study_calendar_light",
        "title": "Visual Exam & Study Schedule Calendar — Light Mode",
        "theme": "light",
        "view": "calendar",
        "width": 1440,
        "height": 900
    },
    {
        "id": "11_compact_desktop_widget_dark",
        "title": "Pinned Desktop Companion Widget — Dark Mode",
        "theme": "dark",
        "view": "dashboard",
        "widget_mode": True,
        "width": 380,
        "height": 740
    },
    {
        "id": "12_compact_desktop_widget_light",
        "title": "Pinned Desktop Companion Widget — Light Mode",
        "theme": "light",
        "view": "dashboard",
        "widget_mode": True,
        "width": 380,
        "height": 740
    },
    {
        "id": "13_two_way_phone_companion_qr",
        "title": "Two-Way Phone Companion Hub & Live QR Code Modal",
        "theme": "dark",
        "view": "dashboard",
        "modal": "sync",
        "width": 1440,
        "height": 900
    },
    {
        "id": "14_cognitive_ergonomics_preferences",
        "title": "Sensory Ergonomics & Local Neural AI Configuration",
        "theme": "dark",
        "view": "dashboard",
        "modal": "settings",
        "width": 1440,
        "height": 900
    }
]

def generate_screenshots():
    print(f"Generating {len(pitch_deck_specs)} pitch deck showcase screenshots...")
    results = []

    for item in pitch_deck_specs:
        file_id = item["id"]
        out_filename = f"{file_id}.png"
        out_file = os.path.join(out_dir, out_filename)
        temp_file = os.path.join(scratch_dir, f"temp_{file_id}.html")

        # Generate custom variant
        variant_html = create_deck_variant_html(item)
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(variant_html)

        if os.path.exists(out_file):
            try: os.remove(out_file)
            except Exception: pass

        file_url = "file:///" + os.path.abspath(temp_file).replace("\\", "/")
        cmd = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--virtual-time-budget=2000",
            f"--window-size={item['width']},{item['height']}",
            f"--screenshot={out_file}",
            file_url
        ]

        t0 = time.time()
        res = subprocess.run(cmd, capture_output=True, timeout=20)
        dur = round(time.time() - t0, 2)

        if os.path.exists(out_file):
            im = Image.open(out_file)
            print(f"[OK] {out_filename} ({im.size[0]}x{im.size[1]}) in {dur}s — {item['title']} ({os.path.getsize(out_file)} bytes)")
            results.append({
                "id": file_id,
                "file": out_filename,
                "path": out_file,
                "size": im.size,
                "title": item["title"]
            })
        else:
            print(f"[ERR] Failed to capture {out_filename}")

    print(f"\nCompleted! {len(results)} of {len(pitch_deck_specs)} screenshots generated in {out_dir}")
    return results

if __name__ == "__main__":
    generate_screenshots()
