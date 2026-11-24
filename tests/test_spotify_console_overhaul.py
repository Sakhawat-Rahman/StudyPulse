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

    # 1. Check no uncaught JS errors
    errors = window.evaluate_js("window.__errors || []")
    if not errors:
        passed.append("No uncaught JS errors after Spotify console overhaul")
    else:
        failed.append(f"Uncaught JS errors: {errors}")

    # 2. Check 4-Corner Snap Buttons were deleted
    corner_btns = window.evaluate_js("""(() => {
        return {
            tl: !!document.getElementById('snap-corner-tl'),
            tr: !!document.getElementById('snap-corner-tr'),
            bl: !!document.getElementById('snap-corner-bl'),
            br: !!document.getElementById('snap-corner-br')
        };
    })()""")
    if not (corner_btns['tl'] or corner_btns['tr'] or corner_btns['bl'] or corner_btns['br']):
        passed.append("4-Corner button cluster [ ⌜ ⌝ ⌞ ⌟ ] completely purged from header")
    else:
        failed.append(f"Corner buttons still exist in DOM: {corner_btns}")

    # 3. Check Green accents were purged from Spotify badges
    green_check = window.evaluate_js("""(() => {
        const powerLabel = document.getElementById('inbuilt-spotify-power-label');
        const liveBadge = document.getElementById('floating-spotify-live-badge');
        const libStatus = document.getElementById('spotify-library-status');
        return {
            powerClass: powerLabel ? powerLabel.className : '',
            liveClass: liveBadge ? liveBadge.className : '',
            statusClass: libStatus ? libStatus.className : ''
        };
    })()""")
    if 'emerald' not in green_check['powerClass'] and 'emerald' not in green_check['liveClass'] and 'emerald' not in green_check['statusClass']:
        passed.append("Green accents successfully purged; monochrome/zinc badges applied")
    else:
        failed.append(f"Residual green accents found: {green_check}")

    # 4. Check Complementary Deep Velvet-Slate theme on deck & 18px isolation on bar/mini
    surface_check = window.evaluate_js("""(() => {
        const bar = document.getElementById('inbuilt-spotify-bar');
        const deck = document.getElementById('inbuilt-spotify-deck');
        const mini = document.getElementById('floating-spotify-mini-player');
        const artImg = document.getElementById('floating-spotify-art');
        const grid = document.getElementById('spotify-favourite-playlists-grid');
        return {
            barStyle: bar ? bar.getAttribute('style') || '' : '',
            deckClass: deck ? deck.className : '',
            miniStyle: mini ? mini.getAttribute('style') || '' : '',
            artClass: artImg ? artImg.className : '',
            gridClass: grid ? grid.className : ''
        };
    })()""")
    if '#141418' in surface_check['deckClass'] and 'border-radius: 18px' in surface_check['barStyle'] and 'border-radius: 18px' in surface_check['miniStyle'] and 'grayscale' not in surface_check['artClass'] and 'md:grid-cols-2' in surface_check['gridClass']:
        passed.append("Complementary Deep Velvet-Slate deck, 18px isolation, 2-column playlist grid, and grayscale filter removal verified")
    else:
        failed.append(f"Surface or styling check mismatch: {surface_check}")

    # 5. Check In-App Search UI and execution
    search_test = window.evaluate_js("""(() => {
        const input = document.getElementById('inbuilt-spotify-search-input');
        const clearBtn = document.getElementById('inbuilt-spotify-search-clear-btn');
        const resSec = document.getElementById('spotify-search-results-section');
        const favSec = document.getElementById('spotify-favourite-playlists-section');
        
        // Mock data render directly to test frontend search presentation
        const mockData = {
            tracks: [
                { id: '1', name: 'Motion Picture Soundtrack', artist: 'Radiohead', album: 'Kid A', duration_ms: 200000, uri: 'spotify:track:test1' }
            ],
            playlists: [
                { id: 'p1', name: 'Radiohead Essentials', tracks_total: 25, uri: 'spotify:playlist:testp1' }
            ]
        };
        renderSpotifySearchResults(mockData, 'Radiohead');
        
        const isResVisible = resSec && !resSec.classList.contains('hidden');
        const isFavHidden = favSec && favSec.classList.contains('hidden');
        const trackRow = document.getElementById('spotify-search-tracks-list').querySelector('.group');
        const trackTitle = trackRow ? trackRow.querySelector('.text-white').textContent : '';

        // Test clear
        clearSpotifySearch();
        const isResHiddenAfter = resSec && resSec.classList.contains('hidden');
        const isFavRestored = favSec && !favSec.classList.contains('hidden');

        return {
            isResVisible,
            isFavHidden,
            trackTitle,
            isResHiddenAfter,
            isFavRestored
        };
    })()""")
    if search_test and search_test['isResVisible'] and search_test['isFavHidden'] and 'Motion Picture Soundtrack' in search_test['trackTitle'] and search_test['isResHiddenAfter'] and search_test['isFavRestored']:
        passed.append("In-dashboard search results view seamlessly displays songs and clears back to favourites")
    else:
        failed.append(f"In-dashboard search test failed: {search_test}")

    # 6. Check Edge-Relative Magnetic Corner Snapping
    snap_test = window.evaluate_js("""(() => {
        const mini = document.getElementById('floating-spotify-mini-player');
        mini.classList.remove('hidden');

        // Test tl
        applyMiniDockPos('tl');
        const tlStyle = { top: mini.style.top, left: mini.style.left, bottom: mini.style.bottom, right: mini.style.right };
        
        // Test br
        applyMiniDockPos('br');
        const brStyle = { top: mini.style.top, left: mini.style.left, bottom: mini.style.bottom, right: mini.style.right };
        
        // Test bl
        applyMiniDockPos('bl');
        const blStyle = { top: mini.style.top, left: mini.style.left, bottom: mini.style.bottom, right: mini.style.right };

        return { tlStyle, brStyle, blStyle };
    })()""")
    if snap_test and snap_test['tlStyle']['top'] == '64px' and snap_test['brStyle']['bottom'] == '24px' and snap_test['blStyle']['bottom'] == '24px' and snap_test['blStyle']['left'] == '88px':
        passed.append("Edge-relative CSS anchoring locks mini-player to viewport edges (bottom: 24px, left: 88px)")
    else:
        failed.append(f"Edge-relative snapping failed: {snap_test}")

    # 7. Check Dynamic Album Art Gradient function
    grad_test = window.evaluate_js("""(() => {
        applyAlbumArtGradient(null);
        const bar = document.getElementById('inbuilt-spotify-bar');
        const bg1 = bar ? bar.style.background : '';
        return { hasGrad: bg1.includes('linear-gradient') };
    })()""")
    if grad_test and grad_test['hasGrad']:
        passed.append("Adaptive Song-Cover gradient engine initializes with rich fallback gradient")
    else:
        failed.append(f"Gradient test failed: {grad_test}")

    time.sleep(0.5)
    window.destroy()

bridge = app.DesktopBridge()
server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42072)
app_url = f"http://127.0.0.1:{server.server_port}/"

import tempfile
test_cache_dir = tempfile.mkdtemp(prefix='studypulse_test_')

window = webview.create_window(
    "Spotify Console Overhaul Verification",
    url=app_url,
    js_api=bridge,
    width=1000,
    height=700,
    hidden=True
)
bridge.set_window(window)
webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
server.shutdown()

print("\n================== SPOTIFY OVERHAUL TEST RESULTS ==================")
for p in passed:
    print(f"  [PASS] {p}")
for f in failed:
    print(f"  [FAIL] {f}")
print("====================================================================")
assert len(failed) == 0, f"{len(failed)} tests failed!"
print("ALL SPOTIFY CONSOLE OVERHAUL TESTS PASSED 100%!")
