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
    time.sleep(1.5)
    
    # 1. Check window.__errors
    errors = window.evaluate_js("window.__errors || []")
    if not errors:
        passed.append("No uncaught JS errors on startup")
    else:
        failed.append(f"Uncaught JS errors: {errors}")
        
    # 2. Check view switching
    v1 = window.evaluate_js("""(() => {
        const btn = document.getElementById('view-timer-btn');
        if (btn) btn.click();
        return state.activeView;
    })()""")
    if v1 == 'timer':
        passed.append("View switch to Focus Studio ('timer') works")
    else:
        failed.append(f"Expected activeView 'timer', got '{v1}'")

    # 3. Test Spotify power toggle in Focus Studio
    p1 = window.evaluate_js("""(() => {
        const powerBtn = document.getElementById('inbuilt-spotify-power-btn');
        if (powerBtn) powerBtn.click();
        const deck = document.getElementById('inbuilt-spotify-deck');
        return {
            active: spotifyPlayerActive,
            deckHidden: deck ? deck.classList.contains('hidden') : true
        };
    })()""")
    if p1 and p1.get('active') is False and p1.get('deckHidden') is True:
        passed.append("Spotify power toggle OFF works")
    else:
        failed.append(f"Spotify power toggle OFF failed: {p1}")

    p2 = window.evaluate_js("""(() => {
        const powerBtn = document.getElementById('inbuilt-spotify-power-btn');
        if (powerBtn) powerBtn.click();
        const deck = document.getElementById('inbuilt-spotify-deck');
        return {
            active: spotifyPlayerActive,
            deckHidden: deck ? deck.classList.contains('hidden') : true
        };
    })()""")
    if p2 and p2.get('active') is True and p2.get('deckHidden') is False:
        passed.append("Spotify power toggle ON works & expands deck")
    else:
        failed.append(f"Spotify power toggle ON failed: {p2}")

    # 4. Test Single-Task Focus Mode modal open & close via close button
    st_test = window.evaluate_js("""(() => {
        const modal = document.getElementById('onething-modal');
        // Open modal
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
        const opened = !modal.classList.contains('hidden') && modal.style.display === 'flex';
        
        // Click close button
        const closeBtn = document.getElementById('close-onething-btn');
        if (closeBtn) closeBtn.click();
        
        const closed = modal.classList.contains('hidden') || modal.style.display === 'none';
        return { opened, closed };
    })()""")
    if st_test and st_test.get('opened') and st_test.get('closed'):
        passed.append("Single-Task Focus Mode close button cleanly closes modal")
    else:
        failed.append(f"Single-Task modal close test failed: {st_test}")

    # 5. Test seeking on seekbar
    seek_test = window.evaluate_js("""(() => {
        updateSpotifySeekbar(45000, 180000);
        const curEl = document.getElementById('inbuilt-spotify-current-time');
        const floatTime = document.getElementById('floating-spotify-time');
        const floatProg = document.getElementById('floating-spotify-progress');
        return {
            studioTime: curEl ? curEl.textContent.trim() : '',
            floatTime: floatTime ? floatTime.textContent.trim() : '',
            floatPct: floatProg ? floatProg.style.width : ''
        };
    })()""")
    if seek_test and '45' in seek_test.get('studioTime') and '45' in seek_test.get('floatTime') and seek_test.get('floatPct') == '25%':
        passed.append("Seekbar & floating mini-player pill timestamps synchronize perfectly (25% progress)")
    else:
        failed.append(f"Seekbar sync failed: {seek_test}")

    # 6. Test switch back to dashboard
    v2 = window.evaluate_js("""(() => {
        const btn = document.getElementById('view-dashboard-btn');
        if (btn) btn.click();
        return state.activeView;
    })()""")
    if v2 == 'dashboard':
        passed.append("View switch back to Dashboard works")
    else:
        failed.append(f"Dashboard view switch failed: {v2}")

    time.sleep(0.5)
    window.destroy()

bridge = app.DesktopBridge()
server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42070)
app_url = f"http://127.0.0.1:{server.server_port}/"

window = webview.create_window(
    "StudyPulse Verification",
    url=app_url,
    js_api=bridge,
    width=1000,
    height=700,
    hidden=True
)
bridge.set_window(window)
webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=False)

server.shutdown()

print("\n================== LIVE INTERACTION TEST RESULTS ==================")
for p in passed:
    print(f"  [PASS] {p}")
for f in failed:
    print(f"  [FAIL] {f}")
print("====================================================================")
assert len(failed) == 0, f"{len(failed)} tests failed!"
print("ALL LIVE INTERACTION TESTS PASSED 100%!")
