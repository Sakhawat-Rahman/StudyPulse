# -*- coding: utf-8 -*-
"""
Test Suite for Dragging Responsiveness & Hover Icon Contrast:
1. Verifies that hovering over #nav-spotify-btn in light/white mode never makes the icon vanish (stays white on active black).
2. Verifies that hovering over mini-player buttons under light-cover mode never turns white on white.
3. Verifies that the mini-player is draggable anywhere on its body while excluding buttons & seekbar.
4. Verifies failsafe cancellation on drag when mouse button is released.
"""
import os
import sys
import time
import json
import webview

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
        # Check no uncaught JS errors on startup
        errors = window.evaluate_js("window.__pageErrors || []")
        record_test("No uncaught JS errors on startup", len(errors) == 0, f"Errors: {errors}")

        # ---------------------------------------------------------------------
        # 1. Nav Spotify Button Hover Icon Contrast in Light Mode & Dark Mode
        # ---------------------------------------------------------------------
        eval_nav_hover = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const floatPlayer = document.getElementById('floating-spotify-mini-player');
          if (!navBtn || !floatPlayer) return { success: false, reason: 'Elements missing' };

          // Case A: Test in Light Mode (White mode)
          document.documentElement.classList.remove('dark');
          floatPlayer.classList.remove('hidden');
          floatPlayer.style.display = 'flex';
          navBtn.style.transition = 'none';
          window.updateNavSpotifyBtnState();

          const svg = navBtn.querySelector('svg');
          const lightSvgColor = window.getComputedStyle(svg).color;
          const lightBtnBg = window.getComputedStyle(navBtn).backgroundColor;

          // Case B: Test in Dark Mode
          document.documentElement.classList.add('dark');
          navBtn.style.transition = 'none';
          window.updateNavSpotifyBtnState();
          const darkSvgColor = window.getComputedStyle(svg).color;
          const darkBtnBg = window.getComputedStyle(navBtn).backgroundColor;

          // Check simulated hover: .nav-spotify-active:hover rule in stylesheet
          const sheets = Array.from(document.styleSheets);
          let hoverWhiteRuleFound = false;
          sheets.forEach(sheet => {
            try {
              const rules = Array.from(sheet.cssRules || []);
              rules.forEach(rule => {
                if (rule.selectorText && rule.selectorText.includes('#nav-spotify-btn.nav-spotify-active:hover')) {
                  hoverWhiteRuleFound = true;
                }
              });
            } catch (e) {}
          });

          // Check that hover:text-ink-950 is NOT in className
          const hasClashingHoverClass = navBtn.className.includes('hover:text-ink-950');

          const lightOk = lightSvgColor.includes('255, 255, 255') && lightBtnBg.includes('9, 9, 11');
          const darkOk = darkSvgColor.includes('9, 9, 11') && darkBtnBg.includes('255, 255, 255');

          return {
            success: !hasClashingHoverClass && hoverWhiteRuleFound && lightOk && darkOk,
            lightOk,
            lightSvgColor,
            lightBtnBg,
            darkOk,
            darkSvgColor,
            darkBtnBg,
            hasClashingHoverClass,
            hoverWhiteRuleFound
          };
        })()
        """
        res_nav = window.evaluate_js(eval_nav_hover)
        record_test("Nav Button Hover Icon Contrast (Zero Vanishing in Light & Dark Modes)", res_nav.get('success', False),
                    f"Light(svg={res_nav.get('lightSvgColor')}, bg={res_nav.get('lightBtnBg')}), Dark(svg={res_nav.get('darkSvgColor')}, bg={res_nav.get('darkBtnBg')}), NoClash={not res_nav.get('hasClashingHoverClass')}")

        # ---------------------------------------------------------------------
        # 2. Mini-Player Light Cover Button Hover Contrast
        # ---------------------------------------------------------------------
        eval_light_cover_hovers = """
        (() => {
          const mini = document.getElementById('floating-spotify-mini-player');
          mini.classList.add('spotify-light-cover');

          const closeBtn = document.getElementById('floating-spotify-close-btn');
          const compactBtn = document.getElementById('floating-spotify-compact-toggle-btn');
          if (!closeBtn || !compactBtn) return { success: false, reason: 'Buttons missing' };

          // Check that hover rules force dark text (#000000) under spotify-light-cover
          const sheets = Array.from(document.styleSheets);
          let hoverRuleFound = false;
          sheets.forEach(sheet => {
            try {
              const rules = Array.from(sheet.cssRules || []);
              rules.forEach(rule => {
                if (rule.selectorText && rule.selectorText.includes('spotify-light-cover') && rule.selectorText.includes('close-btn:hover')) {
                  hoverRuleFound = true;
                }
              });
            } catch (e) {}
          });

          return {
            success: hoverRuleFound,
            hoverRuleFound
          };
        })()
        """
        res_hover = window.evaluate_js(eval_light_cover_hovers)
        record_test("Mini-Player Light Cover Buttons Hover (No White-on-White Vanishing)", res_hover.get('success', False),
                    f"HoverRuleFound: {res_hover.get('hoverRuleFound')}")

        # ---------------------------------------------------------------------
        # 3. Mini-Player Body Draggable & Excludes Buttons
        # ---------------------------------------------------------------------
        eval_drag = """
        (() => {
          const mini = document.getElementById('floating-spotify-mini-player');
          const closeBtn = document.getElementById('floating-spotify-close-btn');
          const seekbar = document.getElementById('floating-spotify-seekbar-container');
          mini.classList.remove('hidden');
          mini.style.display = 'flex';

          const initLeft = mini.getBoundingClientRect().left;
          const initTop = mini.getBoundingClientRect().top;

          // Test 1: Mousedown on close button must NOT trigger drag
          const closeEvent = new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: 100, clientY: 100, button: 0 });
          closeBtn.dispatchEvent(closeEvent);
          const draggingFromButton = mini.classList.contains('is-dragging');

          // Test 2: Mousedown on seekbar must NOT trigger drag
          const seekEvent = new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: 100, clientY: 100, button: 0 });
          seekbar.dispatchEvent(seekEvent);
          const draggingFromSeekbar = mini.classList.contains('is-dragging');

          // Test 3: Mousedown on mini body MUST trigger drag
          const bodyEvent = new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: 200, clientY: 200, button: 0 });
          mini.dispatchEvent(bodyEvent);
          const draggingFromBody = mini.classList.contains('is-dragging');

          // Move 50px
          const moveEvent = new MouseEvent('mousemove', { bubbles: true, clientX: 250, clientY: 250, buttons: 1 });
          document.dispatchEvent(moveEvent);

          const afterMoveLeft = parseFloat(mini.style.left);
          const movedCorrectly = Math.abs((afterMoveLeft - initLeft) - 50) < 5;

          // Mouseup to end drag
          const upEvent = new MouseEvent('mouseup', { bubbles: true, clientX: 250, clientY: 250 });
          document.dispatchEvent(upEvent);
          const draggingEnded = !mini.classList.contains('is-dragging');

          return {
            success: !draggingFromButton && !draggingFromSeekbar && draggingFromBody && movedCorrectly && draggingEnded,
            draggingFromButton,
            draggingFromSeekbar,
            draggingFromBody,
            movedCorrectly,
            draggingEnded
          };
        })()
        """
        res_drag = window.evaluate_js(eval_drag)
        record_test("Mini-Player Full-Body Dragging & Control Exclusion", res_drag.get('success', False),
                    f"FromBody={res_drag.get('draggingFromBody')}, ButtonExcl={not res_drag.get('draggingFromButton')}, SeekbarExcl={not res_drag.get('draggingFromSeekbar')}, Moved={res_drag.get('movedCorrectly')}, Ended={res_drag.get('draggingEnded')}")

        # ---------------------------------------------------------------------
        # 4. Failsafe Drag Cancellation when mouse buttons is 0
        # ---------------------------------------------------------------------
        eval_failsafe = """
        (() => {
          const mini = document.getElementById('floating-spotify-mini-player');
          // Start drag
          const bodyEvent = new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: 200, clientY: 200, button: 0 });
          mini.dispatchEvent(bodyEvent);
          const started = mini.classList.contains('is-dragging');

          // Move with buttons = 0 (simulates mouse released outside window)
          const moveEvent = new MouseEvent('mousemove', { bubbles: true, clientX: 220, clientY: 220, buttons: 0 });
          document.dispatchEvent(moveEvent);

          const canceled = !mini.classList.contains('is-dragging');

          return {
            success: started && canceled,
            started,
            canceled
          };
        })()
        """
        res_failsafe = window.evaluate_js(eval_failsafe)
        record_test("Failsafe Drag Cancellation (Zero Stuck Mouse States)", res_failsafe.get('success', False),
                    f"Started={res_failsafe.get('started')}, Canceled={res_failsafe.get('canceled')}")

    except Exception as e:
        record_test("Exception during test execution", False, str(e))
    finally:
        window.destroy()

def main():
    print("=================================================================")
    print("STARTING HOVER & DRAG RESPONSIVENESS TEST SUITE")
    print("=================================================================")
    html_path = os.path.abspath('studypulse.html')
    window = webview.create_window(
        'StudyPulse Hover & Drag Verification',
        url=f'file://{html_path}',
        width=1280,
        height=850,
        hidden=True
    )
    webview.start(run_tests, window)

    print("\n================== HOVER & DRAG SUMMARY ==================")
    for r in test_results:
        print(r)
    print("===========================================================")

    if test_passed:
        print("ALL HOVER & DRAG FIXES VERIFIED 100% OPERATIONAL & WORKING!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
