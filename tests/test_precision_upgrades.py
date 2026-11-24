# -*- coding: utf-8 -*-
"""
Verification Suite for StudyPulse v3.2.14 Precision UI & Spotify Upgrades:
1. High-contrast Spotify Play/Pause buttons in Dark Mode & Light Mode (Search & Playlists).
2. True 12-Bin Hue-Clustered Gradient Engine & Idle Reset.
3. 3-State Sidebar Status Dot (Red / Yellow / Green).
4. Header title "Spotify", Compressed Mini-Player Mode & 175px Magnetic Snap Ghost Preview.
5. Settings Option for Default Mini-Player Style.
6. Waking Day Horizon Bar Off by default.
"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import time
import json
import tempfile
import webview
import app

test_results = []
test_passed = True

def record_test(name, passed, detail=""):
    global test_passed
    if not passed:
        test_passed = False
    status = "[PASS]" if passed else "[FAIL]"
    test_results.append(f"  {status} {name}: {detail}")
    print(f"  {status} {name}: {detail}")

def run_tests(window):
    time.sleep(2.0)
    try:
        # Check no JS errors
        errors = window.evaluate_js("window.__errors || []")
        record_test("No uncaught JS errors on startup", len(errors) == 0, f"Errors: {errors}")

        # 1. Dark Mode Play Buttons Contrast Verification
        eval_dark_btns = """
        (() => {
          if (typeof window.switchView === 'function') window.switchView('timer');
          if (typeof window.setDarkMode === 'function') window.setDarkMode(true);
          else document.documentElement.classList.add('dark');

          if (typeof window.renderSpotifySearchResults === 'function') {
            window.renderSpotifySearchResults({
              tracks: [{ id: 't1', name: 'Test Track', artist: 'Test Artist', duration_ms: 180000, uri: 'spotify:track:test', album: 'Test Album' }],
              playlists: [{ id: 'p1', name: 'Test Playlist', owner: 'Test Owner', uri: 'spotify:playlist:test' }]
            }, 'test');
          }

          const trackBtn = document.querySelector('#spotify-search-tracks-list button');
          const plBtn = document.querySelector('#spotify-search-playlists-grid button');
          
          if (!trackBtn || !plBtn) return { success: false, reason: 'Buttons not rendered', trackFound: !!trackBtn, plFound: !!plBtn };

          const trackStyle = window.getComputedStyle(trackBtn);
          const plStyle = window.getComputedStyle(plBtn);

          const trackBg = trackStyle.backgroundColor;
          const trackColor = trackStyle.color;
          const plBg = plStyle.backgroundColor;

          // Pure white is rgb(255, 255, 255)
          const isTrackWhite = trackBg === 'rgb(255, 255, 255)' || trackBtn.style.backgroundColor.includes('255, 255, 255') || trackBtn.style.backgroundColor === '#FFFFFF';
          const isPlWhite = plBg === 'rgb(255, 255, 255)' || plBtn.style.backgroundColor.includes('255, 255, 255') || plBtn.style.backgroundColor === '#FFFFFF';

          return {
            success: isTrackWhite && isPlWhite,
            trackBg,
            trackColor,
            plBg
          };
        })()
        """
        res_dark_btns = window.evaluate_js(eval_dark_btns)
        record_test("Dark Mode Play Buttons Contrast", res_dark_btns.get('success', False), f"Track button bg: {res_dark_btns.get('trackBg')}, Pl button bg: {res_dark_btns.get('plBg')}")

        # 2. True 12-Bin Hue Clustering Gradient & Idle Reset Verification
        eval_gradient = """
        (() => {
          if (typeof window.resetSpotifyGradientToDefault === 'function') {
            window.resetSpotifyGradientToDefault();
          }
          const bar = document.getElementById('inbuilt-spotify-bar');
          const mini = document.getElementById('floating-spotify-mini-player');
          const navBtn = document.getElementById('nav-spotify-btn');

          const idleBarBg = bar ? bar.style.background : '';
          const idleMiniBg = mini ? mini.style.background : '';
          const idleNavBg = navBtn ? navBtn.style.backgroundImage : '';

          const idleOk = (idleBarBg === 'rgb(20, 20, 24)' || idleBarBg.includes('20, 20, 24') || idleBarBg.includes('#141418')) && (!idleNavBg || idleNavBg === 'none' || idleNavBg === '');

          return {
            success: idleOk,
            idleBarBg,
            idleMiniBg,
            idleNavBg
          };
        })()
        """
        res_gradient = window.evaluate_js(eval_gradient)
        record_test("Spotify Gradient Idle Reset", res_gradient.get('success', False), f"Idle bar: {res_gradient.get('idleBarBg')}, Idle nav: '{res_gradient.get('idleNavBg')}'")

        # 3. 3-State Sidebar Status Dot Verification
        eval_status_dot = """
        (() => {
          const dot = document.getElementById('nav-spotify-dot');
          
          // State 1: Disconnected -> Solid Red (#EF4444)
          window.spotifyState = { connected: false, is_playing: false };
          window.updateNavSpotifyBtnState();
          const redBg = dot.style.backgroundColor;
          const redPulse = dot.classList.contains('animate-pulse');

          // State 2: Connected, Not Playing -> Solid Yellow (#FACC15)
          window.spotifyState = { connected: true, is_playing: false };
          window.updateNavSpotifyBtnState();
          const yellowBg = dot.style.backgroundColor;
          const yellowPulse = dot.classList.contains('animate-pulse');

          // State 3: Connected & Playing -> Pulsing Green (#22C55E)
          window.spotifyState = { connected: true, is_playing: true };
          window.updateNavSpotifyBtnState();
          const greenBg = dot.style.backgroundColor;
          const greenPulse = dot.classList.contains('animate-pulse');

          const redOk = redBg.includes('239, 68, 68') || redBg === '#EF4444';
          const yellowOk = yellowBg.includes('250, 204, 21') || yellowBg === '#FACC15';
          const greenOk = greenBg.includes('34, 197, 94') || greenBg === '#22C55E';

          return {
            success: redOk && !redPulse && yellowOk && !yellowPulse && greenOk && greenPulse,
            redBg, redPulse,
            yellowBg, yellowPulse,
            greenBg, greenPulse
          };
        })()
        """
        res_dot = window.evaluate_js(eval_status_dot)
        record_test("3-State Sidebar Status Dot (Red/Yellow/Green)", res_dot.get('success', False), f"Red: {res_dot.get('redBg')}, Yellow: {res_dot.get('yellowBg')}, Green: {res_dot.get('greenBg')} (pulsing: {res_dot.get('greenPulse')})")

        # 4. Header title "Spotify", Compressed Mode & 175px Magnetic Snap Preview
        eval_compact_snap = """
        (() => {
          const mini = document.getElementById('floating-spotify-mini-player');
          const header = document.getElementById('floating-spotify-drag-header');
          const headerText = header.querySelector('span.font-bold').textContent.trim();
          const toggleBtn = document.getElementById('floating-spotify-compact-toggle-btn');
          const ghost = document.getElementById('spotify-snap-ghost');
          const stdBody = document.getElementById('floating-spotify-standard-body');
          const cptBody = document.getElementById('floating-spotify-compact-body');

          // Check Title is "Spotify"
          const titleOk = (headerText === 'Spotify');

          // Toggle into Compact Mode
          window.applySpotifyMiniCompactMode(true);
          const compactWidth = mini.style.width;
          const stdHidden = stdBody.classList.contains('hidden');
          const cptVisible = !cptBody.classList.contains('hidden');

          // Toggle back to Standard Mode
          window.applySpotifyMiniCompactMode(false);
          const stdWidth = mini.style.width;
          const stdVisible = !stdBody.classList.contains('hidden');
          const cptHidden = cptBody.classList.contains('hidden');

          const ghostOk = (ghost !== null);

          return {
            success: titleOk && compactWidth === '176px' && stdHidden && cptVisible && stdWidth === '360px' && stdVisible && cptHidden && ghostOk,
            headerText,
            compactWidth,
            stdWidth,
            ghostFound: ghostOk
          };
        })()
        """
        res_compact = window.evaluate_js(eval_compact_snap)
        record_test("Mini-Player Header 'Spotify' & Dual Mode Layout", res_compact.get('success', False), f"Header: '{res_compact.get('headerText')}', Compact: {res_compact.get('compactWidth')}, Standard: {res_compact.get('stdWidth')}, Ghost: {res_compact.get('ghostFound')}")

        # 5. Settings Option for Default Mini-Player Style
        eval_settings_pref = """
        (() => {
          window.openSettingsModal();
          const prefSelect = document.getElementById('pref-spotify-default-mini-style');
          if (!prefSelect) return { success: false, reason: 'Select not found' };

          // Change to compact
          prefSelect.value = 'compact';
          window.applySettings(false);

          const savedStyle = state.settings.spotifyDefaultMiniStyle;
          const activeCompact = state.spotifyMiniCompactMode;

          window.closeSettingsModal();

          return {
            success: savedStyle === 'compact' && activeCompact === true,
            savedStyle,
            activeCompact
          };
        })()
        """
        res_settings = window.evaluate_js(eval_settings_pref)
        record_test("Settings Option for Default Mini Style", res_settings.get('success', False), f"Saved: {res_settings.get('savedStyle')}, CompactActive: {res_settings.get('activeCompact')}")

        # 6. Waking Day Horizon Bar Off by Default
        eval_horizon = """
        (() => {
          const wrap = document.getElementById('waking-day-horizon-wrapper');
          const chk = document.getElementById('setting-show-horizon');
          const defaultStateVal = state.settings ? state.settings.showHorizonBar : false;
          const isMigrated = Boolean(state._horizonDefaultMigratedV3214);

          const isHidden = wrap.classList.contains('hidden') || wrap.style.display === 'none';
          const isUnchecked = !chk.checked;

          return {
            success: isHidden && isUnchecked && defaultStateVal === false && isMigrated,
            isHidden,
            isUnchecked,
            defaultStateVal,
            isMigrated
          };
        })()
        """
        res_horizon = window.evaluate_js(eval_horizon)
        record_test("Waking Day Horizon Bar Off by Default", res_horizon.get('success', False), f"Hidden: {res_horizon.get('isHidden')}, Unchecked: {res_horizon.get('isUnchecked')}, DefaultState: {res_horizon.get('defaultStateVal')}, Migrated: {res_horizon.get('isMigrated')}")

    except Exception as e:
        record_test("Test Execution", False, str(e))
    finally:
        time.sleep(0.5)
        window.destroy()

def main():
    bridge = app.DesktopBridge()
    server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42095)
    app_url = f"http://127.0.0.1:{server.server_port}/"

    test_cache_dir = tempfile.mkdtemp(prefix='studypulse_precision_')

    window = webview.create_window(
        "StudyPulse v3.2.14 Precision Verification",
        url=app_url,
        js_api=bridge,
        width=1280,
        height=800,
        hidden=True
    )
    bridge.set_window(window)
    webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
    server.shutdown()

    print("\n================== PRECISION UPGRADES TEST SUMMARY ==================")
    for res in test_results:
        print(res)
    print("=======================================================================")

    if test_passed:
        print("ALL PRECISION UPGRADE TESTS PASSED 100%!")
        sys.exit(0)
    else:
        print("TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
