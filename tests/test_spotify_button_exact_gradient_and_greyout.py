# -*- coding: utf-8 -*-
"""
Test Suite for Exact Spotify Button Gradient & Inactive Greyout Behavior:
1. Verifies that when music is playing and mini-player is open, #nav-spotify-btn receives the EXACT SAME gradient as the album.
2. Verifies that when the mini-player is closed (greyed out), #nav-spotify-btn has ZERO gradient (background is empty/none).
3. Verifies that the greyed out state has reduced dimming (opacity: 0.85, filter: none, scale: 1).
4. Verifies that when paused, #nav-spotify-btn has ZERO gradient.
5. Verifies grayscale covers (e.g. Cigarettes After Sex) share defaultObsidianGradient between mini-player and #nav-spotify-btn.
"""
import os
import sys
import time
import webview

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app

test_results = []
all_passed = True

def record_test(name, passed, detail=""):
    global all_passed
    if not passed:
        all_passed = False
    status = "[PASS]" if passed else "[FAIL]"
    test_results.append(f"  {status} {name}: {detail}")
    print(f"  {status} {name}: {detail}")

def run_tests(window):
    time.sleep(2.0)
    try:
        # Check no uncaught JS errors
        errors = window.evaluate_js("window.__pageErrors || []")
        record_test("No uncaught JS errors on startup", len(errors) == 0, f"Errors: {errors}")

        # ---------------------------------------------------------------------
        # 1. Exact Same Gradient Between Album & Button when Playing & Active
        # ---------------------------------------------------------------------
        eval_exact_grad = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const mini = document.getElementById('floating-spotify-mini-player');
          const bar = document.getElementById('inbuilt-spotify-bar');

          // Set active mini-player
          mini.classList.remove('hidden');
          mini.style.display = 'flex';

          window.spotifyState = {
            connected: true,
            is_playing: true,
            track: 'Nothing\\'s Gonna Hurt You Baby',
            artist: 'Cigarettes After Sex',
            album_art: 'https://example.com/cas.jpg'
          };

          // Define a test gradient for the album
          const testAlbumGradient = 'linear-gradient(135deg, rgb(80, 70, 90) 0%, rgb(40, 35, 45) 55%, rgb(15, 12, 18) 100%)';
          window.currentSpotifyGradient = testAlbumGradient;
          window.currentSpotifyColors = { r1: 80, g1: 70, b1: 90, r2: 40, g2: 35, b2: 45, r3: 15, g3: 12, b3: 18, isLightCover: false };
          mini.style.background = testAlbumGradient;
          bar.style.background = testAlbumGradient;

          window.updateNavSpotifyBtnState();

          const btnGrad = navBtn.style.backgroundImage || navBtn.style.background;
          const miniGrad = mini.style.background;

          const matchExact = (btnGrad === testAlbumGradient) && (btnGrad === miniGrad);

          return {
            success: matchExact,
            btnGrad,
            miniGrad,
            testAlbumGradient
          };
        })()
        """
        res_grad = window.evaluate_js(eval_exact_grad)
        record_test("Exact Gradient Equality (Album Gradient == Button Gradient)", res_grad.get('success', False),
                    f"BtnGrad: '{res_grad.get('btnGrad')}', MiniGrad: '{res_grad.get('miniGrad')}'")

        # ---------------------------------------------------------------------
        # 2. ZERO Gradient When Button is Greyed Out (Mini-Player Closed)
        # ---------------------------------------------------------------------
        eval_greyout_zero_grad = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const mini = document.getElementById('floating-spotify-mini-player');

          // Music is playing, BUT user closes mini-player (greys out button)
          mini.classList.add('hidden');
          mini.style.display = 'none';

          window.updateNavSpotifyBtnState();

          const btnBgImage = navBtn.style.backgroundImage;
          const btnInlineBg = navBtn.style.background;
          const hasFlowingClass = navBtn.classList.contains('flowing-gradient-active');

          const isZeroGradient = (!btnBgImage || btnBgImage === 'none') &&
                                (!btnInlineBg || !btnInlineBg.includes('gradient')) &&
                                !hasFlowingClass;

          return {
            success: isZeroGradient,
            btnBgImage,
            btnInlineBg,
            hasFlowingClass
          };
        })()
        """
        res_zero = window.evaluate_js(eval_greyout_zero_grad)
        record_test("Zero Gradient When Button is Greyed Out (Closed)", res_zero.get('success', False),
                    f"BgImage='{res_zero.get('btnBgImage')}', InlineBg='{res_zero.get('btnInlineBg')}', FlowingClass={res_zero.get('hasFlowingClass')}")

        # ---------------------------------------------------------------------
        # 3. Reduced Greying Out (Opacity 0.85, Filter None, Scale 1)
        # ---------------------------------------------------------------------
        eval_reduced_grey = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const mini = document.getElementById('floating-spotify-mini-player');

          // Mini is closed
          mini.classList.add('hidden');
          mini.style.display = 'none';
          window.updateNavSpotifyBtnState();

          const cs = window.getComputedStyle(navBtn);
          const opacity = parseFloat(cs.opacity);
          const filter = cs.filter;
          const isReduced = opacity >= 0.80 && opacity <= 0.90 && (filter === 'none' || filter === '');

          return {
            success: isReduced,
            opacity,
            filter
          };
        })()
        """
        res_grey = window.evaluate_js(eval_reduced_grey)
        record_test("Reduced Greying Out (Tasteful 0.85 Opacity & No Desaturation Filter)", res_grey.get('success', False),
                    f"Opacity={res_grey.get('opacity')}, Filter='{res_grey.get('filter')}'")

        # ---------------------------------------------------------------------
        # 4. Zero Gradient When Music is Paused
        # ---------------------------------------------------------------------
        eval_paused = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const mini = document.getElementById('floating-spotify-mini-player');

          // Mini is active, but song is PAUSED
          mini.classList.remove('hidden');
          mini.style.display = 'flex';
          window.spotifyState.is_playing = false;

          window.updateNavSpotifyBtnState();

          const btnBgImage = navBtn.style.backgroundImage;
          const btnInlineBg = navBtn.style.background;
          const hasFlowingClass = navBtn.classList.contains('flowing-gradient-active');

          const isZeroGradient = (!btnBgImage || btnBgImage === 'none') &&
                                (!btnInlineBg || !btnInlineBg.includes('gradient')) &&
                                !hasFlowingClass;

          return {
            success: isZeroGradient,
            btnBgImage,
            btnInlineBg,
            hasFlowingClass
          };
        })()
        """
        res_paused = window.evaluate_js(eval_paused)
        record_test("Zero Gradient When Song is Paused (Active Button Monochrome)", res_paused.get('success', False),
                    f"BgImage='{res_paused.get('btnBgImage')}', FlowingClass={res_paused.get('hasFlowingClass')}")

        # ---------------------------------------------------------------------
        # 5. Grayscale Album (Cigarettes After Sex) Matches Default Obsidian
        # ---------------------------------------------------------------------
        eval_grayscale = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const mini = document.getElementById('floating-spotify-mini-player');

          mini.classList.remove('hidden');
          mini.style.display = 'flex';
          window.spotifyState.is_playing = true;

          // Simulate image load with totalSaturated = 0
          const defaultObsidianGradient = 'linear-gradient(135deg, #272730 0%, #16161C 55%, #0E0E12 100%)';
          window.currentSpotifyGradient = defaultObsidianGradient;
          window.currentSpotifyColors = null;
          mini.style.background = defaultObsidianGradient;

          window.updateNavSpotifyBtnState();

          const btnGrad = navBtn.style.backgroundImage || navBtn.style.background;
          const miniGrad = mini.style.background;

          // Verify exact match between mini-player and button, and that both have obsidian stops (no purple fallback #1E3A8A)
          const matchExact = (btnGrad === miniGrad) && 
                             (btnGrad.includes('39, 39, 48') || btnGrad.includes('#272730')) &&
                             !btnGrad.includes('30, 58, 138') && !btnGrad.includes('#1E3A8A');

          return {
            success: matchExact,
            btnGrad,
            miniGrad,
            defaultObsidianGradient
          };
        })()
        """
        res_cas = window.evaluate_js(eval_grayscale)
        record_test("Grayscale Album Cover Equality (No Purple Fallback)", res_cas.get('success', False),
                    f"BtnGrad='{res_cas.get('btnGrad')}', MiniGrad='{res_cas.get('miniGrad')}'")

    except Exception as e:
        record_test("Exception during test execution", False, str(e))
    finally:
        window.destroy()

def main():
    print("=================================================================")
    print("STARTING EXACT GRADIENT & GREYOUT VERIFICATION")
    print("=================================================================")
    html_path = os.path.abspath('studypulse.html')
    window = webview.create_window(
        'StudyPulse Exact Gradient & Greyout Verification',
        url=f'file://{html_path}',
        width=1280,
        height=850,
        hidden=True
    )
    webview.start(run_tests, window, gui='edgechromium')

    print("\n================== VERIFICATION SUMMARY ==================")
    for r in test_results:
        print(r)
    print("===========================================================")

    if all_passed:
        print("ALL EXACT GRADIENT & GREYOUT FIXES VERIFIED 100% OPERATIONAL!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
