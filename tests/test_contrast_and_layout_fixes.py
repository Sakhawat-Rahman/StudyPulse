import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import time
import json
import webview
import app

passed = []
failed = []

def run_tests(window):
    time.sleep(2.0)

    # 1. Check no JS errors
    errors = window.evaluate_js("window.__errors || []")
    if not errors:
        passed.append("No uncaught JS errors on startup")
    else:
        failed.append(f"Uncaught JS errors: {errors}")

    # 2. Test in Dark Mode
    window.evaluate_js("document.documentElement.classList.add('dark');")

    contrast_check = window.evaluate_js("""(() => {
        const studioPlayBtn = document.getElementById('inbuilt-spotify-play-btn');
        const studioSeekFill = document.getElementById('inbuilt-spotify-seekbar-fill');
        const studioEq = document.getElementById('inbuilt-spotify-equalizer');
        const eqSpan = studioEq ? studioEq.querySelector('span') : null;
        const studioPauseIcon = document.getElementById('inbuilt-spotify-pause-icon');

        const floatPlayBtn = document.getElementById('floating-spotify-play-btn');
        const floatSeekFill = document.getElementById('floating-spotify-progress');
        const floatPauseIcon = document.getElementById('floating-spotify-pause-icon');

        const getBg = (el) => el ? window.getComputedStyle(el).backgroundColor : '';
        const getColor = (el) => el ? window.getComputedStyle(el).color : '';
        const getFill = (el) => el ? window.getComputedStyle(el).fill : '';

        return {
            studioPlayBg: getBg(studioPlayBtn),
            studioPlayColor: getColor(studioPlayBtn),
            studioPauseFill: getFill(studioPauseIcon),
            studioSeekBg: getBg(studioSeekFill),
            eqSpanBg: getBg(eqSpan),
            floatPlayBg: getBg(floatPlayBtn),
            floatPlayColor: getColor(floatPlayBtn),
            floatPauseFill: getFill(floatPauseIcon),
            floatSeekBg: getBg(floatSeekFill)
        };
    })()""")

    # Pure white in rgb is 'rgb(255, 255, 255)'
    if contrast_check['studioPlayBg'] == 'rgb(255, 255, 255)' and contrast_check['floatPlayBg'] == 'rgb(255, 255, 255)':
        passed.append("Play/Pause buttons are 100% pure white (#FFFFFF) in dark mode")
    else:
        failed.append(f"Play/Pause button color mismatch: {contrast_check}")

    if contrast_check['studioSeekBg'] == 'rgb(255, 255, 255)' and contrast_check['floatSeekBg'] == 'rgb(255, 255, 255)':
        passed.append("Seekbar fills are 100% luminous pure white (#FFFFFF) in dark mode (not dark/black)")
    else:
        failed.append(f"Seekbar fill color mismatch: {contrast_check}")

    if contrast_check['eqSpanBg'] == 'rgb(255, 255, 255)':
        passed.append("Equalizer/waveform bars are 100% pure white (#FFFFFF) in dark mode")
    else:
        failed.append(f"Equalizer bar color mismatch: {contrast_check}")

    if '0, 0, 0' in contrast_check['studioPauseFill'] and '0, 0, 0' in contrast_check['floatPauseFill']:
        passed.append("Pause icons are jet black (#000000) for maximum contrast against white button")
    else:
        failed.append(f"Pause icon fill mismatch: {contrast_check}")

    # 3. Test Structured Studio Playbar Layout (Stacked Player: ON + Volume Slider)
    layout_check = window.evaluate_js("""(() => {
        const bar = document.getElementById('inbuilt-spotify-bar');
        const powerBtn = document.getElementById('inbuilt-spotify-power-btn');
        const volSlider = document.getElementById('inbuilt-spotify-volume-slider');
        const rightCol = powerBtn ? powerBtn.parentElement : null;
        
        return {
            rightColClasses: rightCol ? rightCol.className : '',
            powerParentIsRightCol: powerBtn && powerBtn.parentElement === rightCol,
            volParentIsNestedInRightCol: volSlider && volSlider.parentElement.parentElement === rightCol
        };
    })()""")

    if 'flex-col' in layout_check['rightColClasses'] and 'items-end' in layout_check['rightColClasses'] and layout_check['powerParentIsRightCol'] and layout_check['volParentIsNestedInRightCol']:
        passed.append("Studio playbar right column is cleanly structured with volume stacked under Player: ON")
    else:
        failed.append(f"Playbar right column layout mismatch: {layout_check}")

    # 4. Test Single-Task Focus Mode Overlay Contrast in Dark Mode
    onething_check = window.evaluate_js("""(() => {
        const card = document.getElementById('onething-card');
        const title = document.getElementById('onething-task-title');
        const goal = document.getElementById('onething-goal-title');
        const mins = document.getElementById('onething-mins-label');
        const priority = document.getElementById('onething-priority-label');

        const cardBg = card ? window.getComputedStyle(card).backgroundColor : '';
        const titleColor = title ? window.getComputedStyle(title).color : '';
        const goalColor = goal ? window.getComputedStyle(goal).color : '';
        const minsColor = mins ? window.getComputedStyle(mins).color : '';

        return { cardBg, titleColor, goalColor, minsColor };
    })()""")

    # Card must be dark velvet-slate (#18181E -> rgb(24, 24, 30)) NOT cream (#EAEAE6)
    # Title must be pure white (#FFFFFF -> rgb(255, 255, 255))
    if onething_check['cardBg'] == 'rgb(24, 24, 30)' and onething_check['titleColor'] == 'rgb(255, 255, 255)':
        passed.append("Single-Task Focus card is high-contrast dark velvet-slate with crystal-clear white text")
    else:
        failed.append(f"Single-task card contrast mismatch: {onething_check}")

    time.sleep(0.5)
    window.destroy()

bridge = app.DesktopBridge()
server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42078)
app_url = f"http://127.0.0.1:{server.server_port}/"

import tempfile
test_cache_dir = tempfile.mkdtemp(prefix='studypulse_contrast_')

window = webview.create_window(
    "Contrast & Layout Fixes Verification",
    url=app_url,
    js_api=bridge,
    width=1000,
    height=700,
    hidden=True
)
bridge.set_window(window)
webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
server.shutdown()

print("\n================== CONTRAST & LAYOUT FIX TEST RESULTS ==================")
for p in passed:
    print(f"  [PASS] {p}")
for f in failed:
    print(f"  [FAIL] {f}")
print("========================================================================")
assert len(failed) == 0, f"{len(failed)} tests failed!"
print("ALL CONTRAST & LAYOUT TESTS PASSED 100%!")
