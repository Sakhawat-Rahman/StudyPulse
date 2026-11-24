# -*- coding: utf-8 -*-
"""
StudyPulse v3.2.16 Verification Suite
Tests the three precision fixes:
1. Mini-player close button actually hides element physically (display: none, .hidden, and state saved)
2. Opening settings in compact mode does NOT exit widget mode or fling native window to maximized
3. Floating mini-player scales down properly in compact mode without overflowing 380px width
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import time
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
        # Test 0: No JS startup errors
        errors = window.evaluate_js("window.__errors || window.jsErrors || []")
        record_test("No uncaught JS errors on startup", len(errors) == 0, f"Errors: {errors}")

        # Test 1: Mini-Player Close Button Actually Hides Element Physically
        eval_close_test = """
        (() => {
          if (typeof state === 'undefined') state = window.state;
          state.showSpotifyMini = true;
          const fp = window.getFloatingMiniPlayer ? window.getFloatingMiniPlayer() : document.getElementById('floating-spotify-mini-player');
          fp.classList.remove('hidden');
          fp.style.display = 'flex';
          if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();

          const closeBtn = document.getElementById('floating-spotify-close-btn');
          if (closeBtn) closeBtn.click();

          const isHiddenClass = fp.classList.contains('hidden');
          const computedDisplay = window.getComputedStyle(fp).display;
          const inlineDisplay = fp.style.display;
          const stateFlag = state.showSpotifyMini;
          const navActive = document.getElementById('nav-spotify-btn').classList.contains('bg-ink-950');

          return {
            success: isHiddenClass && (computedDisplay === 'none') && (inlineDisplay === 'none') && (stateFlag === false) && !navActive,
            isHiddenClass,
            computedDisplay,
            inlineDisplay,
            stateFlag,
            navActive
          };
        })()
        """
        res1 = window.evaluate_js(eval_close_test)
        record_test(
            "Mini-Player Close Button Actually Hides Physically",
            res1.get('success', False),
            f"hiddenClass: {res1.get('isHiddenClass')}, computedDisplay: '{res1.get('computedDisplay')}', inlineDisplay: '{res1.get('inlineDisplay')}', state.showSpotifyMini: {res1.get('stateFlag')}, navActive: {res1.get('navActive')}"
        )

        # Test 2: Compact/Widget Mode Settings Modal Does NOT Exit Widget Mode or Fling Window
        eval_settings_widget_test = """
        (() => {
          if (typeof state === 'undefined') state = window.state;
          // Enter widget mode
          window.toggleWidgetMode(true);

          const isWidgetBefore = state.isWidgetMode && document.body.classList.contains('widget-mode-active');

          // Click brand-home-btn (Settings trigger in widget mode)
          const brandBtn = document.getElementById('brand-home-btn');
          if (brandBtn) brandBtn.click();

          const isWidgetAfter = state.isWidgetMode && document.body.classList.contains('widget-mode-active');
          const modal = document.getElementById('settings-modal');
          const modalVisible = !modal.classList.contains('hidden');
          const hasCompactClass = modal.classList.contains('widget-settings-compact');
          const modalBox = modal.firstElementChild.getBoundingClientRect();
          const cardWidth = modalBox.width;

          // Close modal
          window.closeSettingsModal();
          const modalClosed = modal.classList.contains('hidden');
          const compactClassRemoved = !modal.classList.contains('widget-settings-compact');

          return {
            success: isWidgetBefore && isWidgetAfter && modalVisible && hasCompactClass && (cardWidth <= 360) && modalClosed && compactClassRemoved,
            isWidgetBefore,
            isWidgetAfter,
            modalVisible,
            hasCompactClass,
            cardWidth,
            modalClosed,
            compactClassRemoved
          };
        })()
        """
        res2 = window.evaluate_js(eval_settings_widget_test)
        record_test(
            "Opening Settings in Compact Mode Preserves Widget Mode & Compact Formfactor",
            res2.get('success', False),
            f"widgetBefore: {res2.get('isWidgetBefore')}, widgetAfter: {res2.get('isWidgetAfter')}, modalVisible: {res2.get('modalVisible')}, compactClass: {res2.get('hasCompactClass')}, cardWidth: {res2.get('cardWidth')}px, closedCleanly: {res2.get('modalClosed') and res2.get('compactClassRemoved')}"
        )

        # Test 3: Mini-Player Scales Properly in Compact Mode (Standard & Compressed Modes)
        # Step A: Standard mode in widget
        standard_info = window.evaluate_js("""
        (() => {
          if (typeof state === 'undefined') state = window.state;
          window.toggleWidgetMode(true);
          state.showSpotifyMini = true;
          const fp = window.getFloatingMiniPlayer ? window.getFloatingMiniPlayer() : document.getElementById('floating-spotify-mini-player');
          fp.classList.remove('hidden');
          fp.style.display = 'flex';
          window.applySpotifyMiniCompactMode(false);
          window.applyMiniDockPos('bl');
          return {
            width: fp.offsetWidth,
            left: window.getComputedStyle(fp).left
          };
        })()
        """)

        # Step B: Toggle compressed album mode (instant layout for headless/hidden test mode)
        window.evaluate_js("""
        (() => {
          const fp = window.getFloatingMiniPlayer ? window.getFloatingMiniPlayer() : document.getElementById('floating-spotify-mini-player');
          if (fp) fp.style.transition = 'none';
          window.applySpotifyMiniCompactMode(true);
        })()
        """)
        time.sleep(0.2)

        compact_info = window.evaluate_js("""
        (() => {
          const fp = window.getFloatingMiniPlayer ? window.getFloatingMiniPlayer() : document.getElementById('floating-spotify-mini-player');
          const hasClass = fp.classList.contains('mini-player-compact-active');
          const w = fp.offsetWidth;
          const compW = window.getComputedStyle(fp).width;
          const compWVal = parseFloat(compW) || w;

          // Clean up
          window.toggleWidgetMode(false);
          window.applySpotifyMiniCompactMode(false);
          fp.classList.add('hidden');
          fp.style.display = 'none';
          if (typeof state !== 'undefined' && state) state.showSpotifyMini = false;
          if (typeof window.state !== 'undefined' && window.state) window.state.showSpotifyMini = false;

          return {
            width: w,
            computedWidth: compW,
            compWVal: compWVal,
            hasCompactActiveClass: hasClass
          };
        })()
        """)

        standard_w = standard_info.get('width', 999)
        compact_w = compact_info.get('compWVal', compact_info.get('width', 999))
        has_active_class = compact_info.get('hasCompactActiveClass', False)
        test3_pass = (standard_w <= 360) and (compact_w <= 180) and has_active_class

        record_test(
            "Mini-Player Scales Down Properly in Compact Mode Without Bleed",
            test3_pass,
            f"standardWidth: {standard_w}px, compactWidth: {compact_w}px, compactActiveClass: {has_active_class}, standardLeft: {standard_info.get('left')}"
        )

    except Exception as e:
        record_test("Test Execution", False, str(e))
    finally:
        time.sleep(0.5)
        window.destroy()

def main():
    bridge = app.DesktopBridge()
    server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42150)
    app_url = f"http://127.0.0.1:{server.server_port}/"

    test_cache_dir = tempfile.mkdtemp(prefix='studypulse_patch16_')

    window = webview.create_window(
        "StudyPulse Patch 3.2.16 Verification",
        url=app_url,
        js_api=bridge,
        width=380,
        height=640,
        hidden=True
    )
    bridge.set_window(window)
    webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
    server.shutdown()

    print("\n================== PATCH 3.2.16 TEST SUMMARY ==================")
    for res in test_results:
        print(res)
    print("=================================================================")

    if test_passed:
        print("ALL PATCH 3.2.16 TESTS PASSED 100%!")
        sys.exit(0)
    else:
        print("TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
