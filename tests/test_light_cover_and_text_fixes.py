# -*- coding: utf-8 -*-
"""
Verification Suite for StudyPulse v3.2.15 Light Cover Gradient, Contrast Polarity & Unscrambled Text:
1. True Proportional Color Sampling & Light Cover Contrast Polarity (.spotify-light-cover).
2. Text Entity Decoding & Zero Scrambled Text (Teacher's Pet).
3. Sidebar Nav Toggle Inactive / Active Ring Behavior.
4. Cohesive Glassmorphic Elevation & Drop Shadows.
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

        # 1. Text Entity Decoding & Zero Scrambled Text (Teacher's Pet)
        eval_text = """
        (() => {
          window.spotifyState = {
            connected: true,
            is_playing: true,
            track: "Teacher&#039;s Pet",
            artist: "Melanie &amp; Martinez",
            album_art: ""
          };
          window.updateAllSpotifySurfaces();

          const studioTitle = document.getElementById('inbuilt-spotify-track-title').textContent;
          const studioArtist = document.getElementById('inbuilt-spotify-artist-label').textContent;
          const floatTitle = document.getElementById('floating-spotify-track').textContent;
          const floatArtist = document.getElementById('floating-spotify-artist').textContent;
          const compactTitle = document.getElementById('floating-spotify-compact-title').textContent;
          const compactArtist = document.getElementById('floating-spotify-compact-artist').textContent;

          const titleOk = (studioTitle === "Teacher's Pet") && (floatTitle === "Teacher's Pet") && (compactTitle === "Teacher's Pet");
          const artistOk = (studioArtist === "Melanie & Martinez") && (floatArtist === "Melanie & Martinez") && (compactArtist === "Melanie & Martinez");

          return {
            success: titleOk && artistOk,
            studioTitle,
            floatTitle,
            compactTitle,
            studioArtist,
            floatArtist,
            compactArtist
          };
        })()
        """
        res_text = window.evaluate_js(eval_text)
        record_test("Text Entity Decoding (Zero Scrambled Text)", res_text.get('success', False), f"Track: '{res_text.get('floatTitle')}', Artist: '{res_text.get('floatArtist')}'")

        # 2. Sidebar Nav Toggle Inactive / Active Ring Behavior
        eval_nav_ring = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const floatPlayer = document.getElementById('floating-spotify-mini-player');

          // Case 1: Inactive (Mini player closed/hidden)
          floatPlayer.classList.add('hidden');
          floatPlayer.style.display = 'none';
          window.updateNavSpotifyBtnState();

          const inactiveHasRing = navBtn.classList.contains('ring-2') || navBtn.classList.contains('ring-ink-950');
          const inactiveHasDarkRing = navBtn.classList.contains('dark:ring-[#EAEAE6]');
          const inactiveIsBgInk = navBtn.classList.contains('bg-ink-950');
          const inactiveHasBgWhite = navBtn.classList.contains('bg-white/90');

          // Case 2: Active (Mini player open/visible)
          floatPlayer.classList.remove('hidden');
          floatPlayer.style.display = 'flex';
          window.updateNavSpotifyBtnState();

          const activeIsBgInk = navBtn.classList.contains('bg-ink-950');
          const activeIsTextWhite = navBtn.classList.contains('text-white');
          const activeHasRing = navBtn.classList.contains('ring-2');

          const inactiveOk = !inactiveHasRing && !inactiveHasDarkRing && !inactiveIsBgInk && inactiveHasBgWhite;
          const activeOk = activeIsBgInk && activeIsTextWhite && !activeHasRing;

          return {
            success: inactiveOk && activeOk,
            inactiveOk,
            inactiveHasRing,
            inactiveHasBgWhite,
            activeOk,
            activeIsBgInk,
            activeIsTextWhite
          };
        })()
        """
        res_nav = window.evaluate_js(eval_nav_ring)
        record_test("Sidebar Nav Toggle Inactive/Active Styling", res_nav.get('success', False), f"Inactive Ok: {res_nav.get('inactiveOk')}, Active Ok: {res_nav.get('activeOk')}")

        # 3. Light Album Cover Contrast Polarity & Soft Shadows (.spotify-light-cover)
        # Trigger gradient with mock pastel cream/pink image
        window.evaluate_js("""
        (() => {
          const canvas = document.createElement('canvas');
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#F5EAE6'; // Soft pastel cream/pink
          ctx.fillRect(0, 0, 32, 32);
          const dataUrl = canvas.toDataURL();
          window.applyAlbumArtGradient(dataUrl);
        })()
        """)
        time.sleep(1.2)

        eval_light_verify = """
        (() => {
          const bar = document.getElementById('inbuilt-spotify-bar');
          const mini = document.getElementById('floating-spotify-mini-player');
          const navBtn = document.getElementById('nav-spotify-btn');

          const barHasLightClass = bar.classList.contains('spotify-light-cover');
          const miniHasLightClass = mini.classList.contains('spotify-light-cover');
          const navHasLightClass = navBtn.classList.contains('spotify-light-cover');

          const playBtn = document.getElementById('inbuilt-spotify-play-btn');
          const playStyle = window.getComputedStyle(playBtn);
          const playBg = playStyle.backgroundColor;
          const playColor = playStyle.color;

          const trackTitle = document.getElementById('inbuilt-spotify-track-title');
          const titleStyle = window.getComputedStyle(trackTitle);
          const titleColor = titleStyle.color;

          // Play button on light cover must be solid Jet Black: rgb(9, 9, 11)
          const playBlack = playBg === 'rgb(9, 9, 11)' || playBg.includes('9, 9, 11');
          // Title on light cover must be Deep Obsidian: rgb(9, 9, 11)
          const titleObsidian = titleColor === 'rgb(9, 9, 11)' || titleColor.includes('9, 9, 11');

          // Shadow check: must be soft glassmorphic
          const barShadow = bar.style.boxShadow;
          const softShadow = barShadow.includes('10px 28px -6px');

          return {
            success: barHasLightClass && miniHasLightClass && playBlack && titleObsidian && softShadow,
            barHasLightClass,
            miniHasLightClass,
            navHasLightClass,
            playBg,
            playColor,
            titleColor,
            barShadow
          };
        })()
        """
        res_light = window.evaluate_js(eval_light_verify)
        record_test("Light Album Cover Contrast Polarity & Soft Shadows", res_light.get('success', False), f"LightClass: {res_light.get('barHasLightClass')}, PlayBg: {res_light.get('playBg')}, TitleColor: {res_light.get('titleColor')}, Shadow: {res_light.get('barShadow')}")

        # 4. Mid-Tone / Dark Cover Mode & Class Reset
        # Trigger gradient with dark cover
        window.evaluate_js("""
        (() => {
          const canvas = document.createElement('canvas');
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#1A1B2F'; // Dark indigo cover
          ctx.fillRect(0, 0, 32, 32);
          const dataUrl = canvas.toDataURL();
          window.applyAlbumArtGradient(dataUrl);
        })()
        """)
        time.sleep(0.5)

        eval_dark_verify = """
        (() => {
          const bar = document.getElementById('inbuilt-spotify-bar');
          const mini = document.getElementById('floating-spotify-mini-player');

          const barHasLight = bar.classList.contains('spotify-light-cover');
          const miniHasLight = mini.classList.contains('spotify-light-cover');

          const playBtn = document.getElementById('inbuilt-spotify-play-btn');
          const playStyle = window.getComputedStyle(playBtn);
          const playBg = playStyle.backgroundColor;

          // Dark cover play button should be white rgb(255, 255, 255)
          const playWhite = playBg === 'rgb(255, 255, 255)' || playBg.includes('255, 255, 255');

          return {
            success: !barHasLight && !miniHasLight && playWhite,
            barHasLight,
            miniHasLight,
            playBg
          };
        })()
        """
        res_dark = window.evaluate_js(eval_dark_verify)
        record_test("Dark Cover Mode Contrast & Class Reset", res_dark.get('success', False), f"LightClassRemoved: {not res_dark.get('barHasLight')}, PlayBg: {res_dark.get('playBg')}")

    except Exception as e:
        record_test("Test Execution", False, str(e))
    finally:
        time.sleep(0.5)
        window.destroy()

def main():
    bridge = app.DesktopBridge()
    server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42210)
    app_url = f"http://127.0.0.1:{server.server_port}/"

    test_cache_dir = tempfile.mkdtemp(prefix='studypulse_contrast_')

    window = webview.create_window(
        "StudyPulse v3.2.15 Verification",
        url=app_url,
        js_api=bridge,
        width=1280,
        height=800,
        hidden=True
    )
    bridge.set_window(window)
    webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
    server.shutdown()

    print("\n================== PATCH 3.2.15 TEST SUMMARY ==================")
    for res in test_results:
        print(res)
    print("=================================================================")

    if test_passed:
        print("ALL PATCH 3.2.15 TESTS PASSED 100%!")
        sys.exit(0)
    else:
        print("TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
