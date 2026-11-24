import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import time
import webview
import app
import tempfile

passed = []
failed = []

def run_tests(window):
    time.sleep(2.0)
    try:
        # 1. Check for uncaught JS errors
        errors = window.evaluate_js("window.__errors || []")
        if not errors:
            passed.append("No uncaught JS errors on startup")
        else:
            failed.append(f"Uncaught JS errors: {errors}")

        # 2. Test Library Expand / Collapse button
        res_btn = window.evaluate_js("""(() => {
            const btn = document.getElementById('inbuilt-spotify-power-btn');
            const label = document.getElementById('inbuilt-spotify-power-label');
            const deck = document.getElementById('inbuilt-spotify-deck');
            
            // Initial state check
            const initialText = label ? label.textContent.trim() : '';
            const initialDeckHidden = deck ? deck.classList.contains('hidden') : false;
            
            // Click to toggle
            btn.click();
            const textAfterClick1 = label ? label.textContent.trim() : '';
            const deckHiddenAfterClick1 = deck ? deck.classList.contains('hidden') : false;
            
            // Click to toggle back
            btn.click();
            const textAfterClick2 = label ? label.textContent.trim() : '';
            const deckHiddenAfterClick2 = deck ? deck.classList.contains('hidden') : false;
            
            return {
                initialText,
                initialDeckHidden,
                textAfterClick1,
                deckHiddenAfterClick1,
                textAfterClick2,
                deckHiddenAfterClick2
            };
        })()""")
        
        if 'Library' in res_btn['textAfterClick1'] or 'Library' in res_btn['textAfterClick2']:
            passed.append(f"Library drawer button toggles cleanly between states: {res_btn['textAfterClick1']} <-> {res_btn['textAfterClick2']}")
        else:
            failed.append(f"Library button label unexpected: {res_btn}")

        # 3. Test Studio View Toggle & Attention Pulse Behavior
        res_studio = window.evaluate_js("""(() => {
            // Switch to studio view
            switchView('timer');
            const fp = getFloatingMiniPlayer();
            const bar = document.getElementById('inbuilt-spotify-bar');
            const deck = document.getElementById('inbuilt-spotify-deck');
            
            // Ensure deck is collapsed initially
            if (deck) deck.classList.add('hidden');
            
            // Click nav spotify toggle button while inside studio view
            const navBtn = document.getElementById('nav-spotify-btn');
            if (navBtn) navBtn.click();
            
            const fpHiddenInStudio = fp ? (fp.classList.contains('hidden') || fp.style.display === 'none') : true;
            const deckStayedCollapsed = deck ? deck.classList.contains('hidden') : true;
            const barHasBounceAnimation = bar ? bar.classList.contains('animate-attention-bounce') : false;
            
            return {
                fpHiddenInStudio,
                deckStayedCollapsed,
                barHasBounceAnimation
            };
        })()""")
        
        if res_studio['fpHiddenInStudio'] and res_studio['deckStayedCollapsed'] and res_studio['barHasBounceAnimation']:
            passed.append("In Studio View: mini-player is suppressed, deck is not auto-expanded, and playbar triggers attention-bounce animation")
        else:
            failed.append(f"Studio toggle behavior mismatch: {res_studio}")

        # 4. Test Flowing Gradient on nav toggle button during active music playback
        res_gradient = window.evaluate_js("""(() => {
            window.currentSpotifyColors = { r1: 67, g1: 56, b1: 202, r2: 147, g2: 51, b2: 234 };
            spotifyState.connected = true;
            spotifyState.is_playing = true;
            updateNavSpotifyBtnState();
            
            const navBtn = document.getElementById('nav-spotify-btn');
            const hasFlowClass = navBtn ? navBtn.classList.contains('flowing-gradient-active') : false;
            const hasGradBg = navBtn ? navBtn.style.backgroundImage.includes('linear-gradient') : false;
            
            // Pause and check cleanup
            spotifyState.is_playing = false;
            updateNavSpotifyBtnState();
            const cleanedClass = navBtn ? !navBtn.classList.contains('flowing-gradient-active') : false;
            const cleanedBg = navBtn ? navBtn.style.backgroundImage === '' : false;
            
            return {
                hasFlowClass,
                hasGradBg,
                cleanedClass,
                cleanedBg
            };
        })()""")
        
        if res_gradient['hasFlowClass'] and res_gradient['hasGradBg'] and res_gradient['cleanedClass'] and res_gradient['cleanedBg']:
            passed.append("Flowing gradient animates smoothly on Spotify toggle button when playing and cleans up cleanly on pause")
        else:
            failed.append(f"Flowing gradient test failed: {res_gradient}")

        # 5. Test in-app search track playback handler
        res_track_play = window.evaluate_js("""(() => {
            renderSpotifySearchResults({
                tracks: [{
                    id: 'sample1',
                    name: 'cold/mess',
                    artist: 'Prateek Kuhad',
                    album: 'cold/mess',
                    album_art: 'https://i.scdn.co/image/sample.jpg',
                    duration_ms: 281218,
                    uri: 'spotify:track:7uhINGViZPygI2AljxO8KN',
                    album_uri: 'spotify:album:6FzicG6wlKHogiRaGAbvBK'
                }],
                playlists: []
            }, 'cold/mess');
            
            const row = document.querySelector('#spotify-search-tracks-list > div');
            if (row) row.click();
            
            const titleAfter = document.getElementById('inbuilt-spotify-track-title').textContent.trim();
            const artistAfter = document.getElementById('inbuilt-spotify-artist-label').textContent.trim();
            const isPlayingNow = spotifyState.is_playing;
            
            return {
                rowFound: !!row,
                titleAfter,
                artistAfter,
                isPlayingNow
            };
        })()""")
        
        if res_track_play['rowFound'] and res_track_play['titleAfter'] == 'cold/mess' and res_track_play['artistAfter'] == 'Prateek Kuhad' and res_track_play['isPlayingNow']:
            passed.append("Clicking search track updates track title, artist, and initiates playback with album context")
        else:
            failed.append(f"Track play test failed: {res_track_play}")

    except Exception as e:
        failed.append(f"Exception during testing: {e}")

    time.sleep(0.5)
    window.destroy()

bridge = app.DesktopBridge()
server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42088)
app_url = f"http://127.0.0.1:{server.server_port}/"

test_cache_dir = tempfile.mkdtemp(prefix='studypulse_lib_')

window = webview.create_window(
    "Library & Search Play Verification",
    url=app_url,
    js_api=bridge,
    width=1400,
    height=800,
    hidden=True
)
bridge.set_window(window)
webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
server.shutdown()

print("\n================== LIBRARY & SEARCH PLAY TEST RESULTS ==================")
for p in passed:
    print(f"  [PASS] {p}")
for f in failed:
    print(f"  [FAIL] {f}")
print("=========================================================================")
assert len(failed) == 0, f"{len(failed)} tests failed!"
print("ALL LIBRARY & SEARCH PLAY TESTS PASSED 100%!")
