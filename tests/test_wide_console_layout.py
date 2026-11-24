import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import time
import webview
import app

passed = []
failed = []

def run_tests(window):
    time.sleep(2.0)

    # 1. Check no uncaught JS errors
    errors = window.evaluate_js("window.__errors || []")
    if not errors:
        passed.append("No uncaught JS errors on startup")
    else:
        failed.append(f"Uncaught JS errors: {errors}")

    # 2. Check #timer-studio-view width & classes
    view_check = window.evaluate_js("""(() => {
        const timerView = document.getElementById('timer-studio-view');
        return timerView ? timerView.className : '';
    })()""")
    if 'max-w-5xl' in view_check and '2xl:max-w-7xl' in view_check:
        passed.append("Timer studio view container expanded to wide footprint (max-w-5xl xl:max-w-6xl 2xl:max-w-7xl)")
    else:
        failed.append(f"Timer studio view class mismatch: {view_check}")

    # 3. Check #spotify-favourite-playlists-grid classes
    grid_check = window.evaluate_js("""(() => {
        const favGrid = document.getElementById('spotify-favourite-playlists-grid');
        const searchGrid = document.getElementById('spotify-search-playlists-grid');
        return {
            favClass: favGrid ? favGrid.className : '',
            searchClass: searchGrid ? searchGrid.className : ''
        };
    })()""")
    if 'xl:grid-cols-4' in grid_check['favClass'] and 'md:grid-cols-2' in grid_check['favClass'] and 'max-h-[580px]' in grid_check['favClass']:
        passed.append("Favourite playlists grid upgraded to 4-column wide grid with max-height bounding")
    else:
        failed.append(f"Favourite playlists grid class mismatch: {grid_check['favClass']}")

    if 'xl:grid-cols-4' in grid_check['searchClass'] and 'md:grid-cols-2' in grid_check['searchClass']:
        passed.append("Search playlists grid upgraded to 4-column wide grid")
    else:
        failed.append(f"Search playlists grid class mismatch: {grid_check['searchClass']}")

    # 4. Check seekbar center column max-w
    seekbar_check = window.evaluate_js("""(() => {
        const playBtn = document.getElementById('inbuilt-spotify-play-btn');
        const centerCol = playBtn ? playBtn.parentElement.parentElement : null;
        return centerCol ? centerCol.className : '';
    })()""")
    if 'max-w-2xl' in seekbar_check:
        passed.append("Playbar center column widened to max-w-2xl for expansive seekbar scrubbing")
    else:
        failed.append(f"Playbar center column mismatch: {seekbar_check}")

    # 5. Check no orphaned connect buttons
    orphan_check = window.evaluate_js("""(() => {
        const deck = document.getElementById('inbuilt-spotify-deck');
        const loginBtns = deck ? deck.querySelectorAll('button[onclick*="openSpotifyAccountLogin"]') : [];
        return loginBtns.length;
    })()""")
    if orphan_check <= 1:
        passed.append("Orphaned duplicate connect buttons completely eliminated from DOM")
    else:
        failed.append(f"Duplicate connect buttons still found in DOM: {orphan_check}")

    time.sleep(0.5)
    window.destroy()

bridge = app.DesktopBridge()
server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42080)
app_url = f"http://127.0.0.1:{server.server_port}/"

import tempfile
test_cache_dir = tempfile.mkdtemp(prefix='studypulse_wide_')

window = webview.create_window(
    "Wide Console Layout Verification",
    url=app_url,
    js_api=bridge,
    width=1400,
    height=800,
    hidden=True
)
bridge.set_window(window)
webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
server.shutdown()

print("\n================== WIDE CONSOLE LAYOUT TEST RESULTS ==================")
for p in passed:
    print(f"  [PASS] {p}")
for f in failed:
    print(f"  [FAIL] {f}")
print("=======================================================================")
assert len(failed) == 0, f"{len(failed)} tests failed!"
print("ALL WIDE CONSOLE LAYOUT TESTS PASSED 100%!")
