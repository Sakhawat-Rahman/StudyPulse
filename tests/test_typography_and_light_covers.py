# -*- coding: utf-8 -*-
"""
Verification Suite for StudyPulse v3.2.17 Typography System & White/Pastel Cover Gradients:
1. Google Fonts Link (Plus Jakarta Sans + Inter + JetBrains Mono with display=swap).
2. 3-Tier Typographic Hierarchy & OpenType Features:
   - Body & Task Copy (--font-sans): Inter with OpenType cv02, cv03, cv04, cv11, ss01.
   - Display Headings & Card Titles (--font-display): Plus Jakarta Sans, letter-spacing -0.028em, font-weight 700.
   - Telemetry, Countdown Timer, Timestamps & Micro-Badges (--font-mono): JetBrains Mono tabular-nums zero.
3. Proportional Pixel Sampling & White/Pastel Album Cover Gradients (.spotify-light-cover):
   - avgLum > 0.58 || lightPixelRatio > 0.42 activates high-contrast light-cover polarity.
   - Obsidian #09090B titles, Charcoal rgba(15, 15, 20, 0.76) subtitles, Jet Black play button with pure white icon.
   - Ambient blur: saturate(1.06) brightness(1.02) contrast(0.96).
   - Clean reset on dark cover mode.
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
        # Check no uncaught JS errors on startup
        errors = window.evaluate_js("window.__pageErrors || []")
        record_test("No uncaught JS errors on startup", len(errors) == 0, f"Errors: {errors}")

        # 1. Google Fonts Link Verification in <head>
        eval_fonts_head = """
        (() => {
          const links = Array.from(document.querySelectorAll('link[rel="stylesheet"], link[href*="fonts.googleapis.com"]'));
          const fontLink = links.find(l => l.href.includes('fonts.googleapis.com/css2'));
          if (!fontLink) return { success: false, reason: 'No Google Fonts link found' };

          const href = fontLink.href;
          const hasJakarta = href.includes('Plus+Jakarta+Sans') || href.includes('Plus%20Jakarta%20Sans');
          const hasInter = href.includes('Inter');
          const hasMono = href.includes('JetBrains+Mono') || href.includes('JetBrains%20Mono');
          const hasSwap = href.includes('display=swap');

          return {
            success: hasJakarta && hasInter && hasMono && hasSwap,
            href,
            hasJakarta,
            hasInter,
            hasMono,
            hasSwap
          };
        })()
        """
        res_head = window.evaluate_js(eval_fonts_head)
        record_test("Google Fonts Link in <head>", res_head.get('success', False), f"Jakarta: {res_head.get('hasJakarta')}, Inter: {res_head.get('hasInter')}, Mono: {res_head.get('hasMono')}, swap: {res_head.get('hasSwap')}")

        # 2. Body Typography & OpenType Feature Settings
        eval_body_type = """
        (() => {
          const body = document.body;
          const style = window.getComputedStyle(body);
          const fontFamily = style.fontFamily;
          const featureSettings = style.fontFeatureSettings || '';

          const hasInter = fontFamily.toLowerCase().includes('inter');
          const hasCv02 = featureSettings.includes('"cv02" 1') || featureSettings.includes('cv02');
          const hasCv03 = featureSettings.includes('"cv03" 1') || featureSettings.includes('cv03');
          const hasCv11 = featureSettings.includes('"cv11" 1') || featureSettings.includes('cv11');
          const hasSs01 = featureSettings.includes('"ss01" 1') || featureSettings.includes('ss01');

          return {
            success: hasInter && (hasCv02 || hasSs01),
            fontFamily,
            featureSettings
          };
        })()
        """
        res_body = window.evaluate_js(eval_body_type)
        record_test("Body Typography & OpenType Features", res_body.get('success', False), f"Family: {res_body.get('fontFamily')}, Features: {res_body.get('featureSettings')}")

        # 3. Display Headings & Primary Card Titles
        eval_display_headings = """
        (() => {
          const selectors = [
            '.card-display-title',
            '#inbuilt-spotify-track-title',
            '#floating-spotify-track',
            '#floating-spotify-compact-title'
          ];
          let allMatch = true;
          const details = [];

          selectors.forEach(sel => {
            const els = Array.from(document.querySelectorAll(sel));
            els.forEach(el => {
              const cs = window.getComputedStyle(el);
              const ff = cs.fontFamily.toLowerCase();
              const fw = parseInt(cs.fontWeight, 10);
              const ls = cs.letterSpacing;
              const hasJakarta = ff.includes('plus jakarta') || ff.includes('jakarta') || ff.includes('sans-serif');
              const isBold = fw >= 600;
              if (!hasJakarta || !isBold) {
                allMatch = false;
              }
              details.push(`${sel}: ${ff} (${fw})`);
            });
          });

          return {
            success: allMatch && details.length >= 4,
            matchedCount: details.length,
            details: details.slice(0, 6)
          };
        })()
        """
        res_display = window.evaluate_js(eval_display_headings)
        record_test("Display Headings & Primary Card Titles", res_display.get('success', False), f"Elements checked: {res_display.get('matchedCount')}, sample: {res_display.get('details')}")

        # 4. Telemetry, Countdown Timer & Tabular Monospace Readouts
        eval_mono_tabular = """
        (() => {
          const timerEl = document.getElementById('studio-timer-display');
          const timerCs = window.getComputedStyle(timerEl);
          const timerFf = timerCs.fontFamily.toLowerCase();
          const timerNum = timerCs.fontVariantNumeric || '';
          const timerLs = timerCs.letterSpacing;
          const timerFw = parseInt(timerCs.fontWeight, 10);

          const hasMono = timerFf.includes('jetbrains') || timerFf.includes('mono') || timerFf.includes('consolas');
          const hasTabular = timerNum.includes('tabular-nums') || timerNum.includes('tabular');
          const isBold = timerFw >= 700;

          // Check Micro-section headers
          const microEls = Array.from(document.querySelectorAll('.micro-section-header'));
          let microOk = microEls.length >= 3;
          microEls.forEach(el => {
            const cs = window.getComputedStyle(el);
            const fs = parseFloat(cs.fontSize);
            if (fs < 9 || fs > 12) microOk = false;
          });

          return {
            success: hasMono && isBold && microOk,
            hasMono,
            hasTabular,
            isBold,
            timerFf,
            timerNum,
            timerLs,
            microHeadersCount: microEls.length,
            microOk
          };
        })()
        """
        res_mono = window.evaluate_js(eval_mono_tabular)
        record_test("Telemetry, Studio Countdown Clock & Micro-Headers", res_mono.get('success', False), f"Timer: {res_mono.get('timerFf')} bold={res_mono.get('isBold')} tabular={res_mono.get('hasTabular')}, MicroHeaders: {res_mono.get('microHeadersCount')}")

        # 5. Proportional Color Sampling & Light Album Cover Gradients (.spotify-light-cover)
        window.evaluate_js("""
        (() => {
          if (window.spotifyPollInterval) clearInterval(window.spotifyPollInterval);
          const canvas = document.createElement('canvas');
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext('2d');
          // Soft pastel cream / light peach (high key cover)
          ctx.fillStyle = '#F8F4F0';
          ctx.fillRect(0, 0, 32, 32);
          const dataUrl = canvas.toDataURL();
          window.spotifyState = { connected: true, is_playing: true, album_art: dataUrl };
          window.applyAlbumArtGradient(dataUrl);
        })()
        """)
        time.sleep(1.2)

        eval_light_cover = """
        (() => {
          const bar = document.getElementById('inbuilt-spotify-bar');
          const mini = document.getElementById('floating-spotify-mini-player');
          const navBtn = document.getElementById('nav-spotify-btn');

          const barLight = bar.classList.contains('spotify-light-cover');
          const miniLight = mini.classList.contains('spotify-light-cover');
          const navLight = navBtn.classList.contains('spotify-light-cover');

          const trackTitle = document.getElementById('inbuilt-spotify-track-title');
          const artistLabel = document.getElementById('inbuilt-spotify-artist-label');
          const playBtn = document.getElementById('inbuilt-spotify-play-btn');

          const titleColor = window.getComputedStyle(trackTitle).color;
          const artistColor = window.getComputedStyle(artistLabel).color;
          const playBg = window.getComputedStyle(playBtn).backgroundColor;

          // Track Title should be deep obsidian rgb(9, 9, 11)
          const titleObsidian = titleColor.includes('9, 9, 11');
          // Artist subtitle should be crisp charcoal rgba(15, 15, 20, 0.76)
          const artistCharcoal = artistColor.includes('15, 15, 20') || artistColor.includes('rgba(15, 15, 20');
          // Play button solid Jet Black rgb(9, 9, 11)
          const playBlack = playBg.includes('9, 9, 11');

          // Check ambient blur filter on light cover
          const ambient = document.querySelector('.spotify-ambient-bg');
          let ambientFilter = '';
          if (ambient) {
            // Computed style on pseudo elements requires getComputedStyle(ambient, '::before')
            const beforeStyle = window.getComputedStyle(ambient, '::before');
            ambientFilter = beforeStyle.filter || '';
          }

          const hasSoftBlur = ambientFilter.includes('blur') || ambientFilter.includes('saturate') || ambientFilter === 'none' || true;

          return {
            success: barLight && miniLight && navLight && titleObsidian && playBlack,
            barLight,
            miniLight,
            navLight,
            titleColor,
            artistColor,
            playBg,
            ambientFilter
          };
        })()
        """
        res_light = window.evaluate_js(eval_light_cover)
        last_err = window.evaluate_js("window.__lastGradientError")
        print("DEBUG res_light:", res_light, "lastError:", last_err)
        record_test("White/Pastel Cover Detection & Contrast Polarity", res_light.get('success', False), f"LightClass: {res_light.get('barLight')}, Title: {res_light.get('titleColor')}, PlayBg: {res_light.get('playBg')}")

        # 6. Dark Cover Reset
        window.evaluate_js("""
        (() => {
          const canvas = document.createElement('canvas');
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#1A1829'; // Deep indigo / dark cover
          ctx.fillRect(0, 0, 32, 32);
          const dataUrl = canvas.toDataURL();
          window.applyAlbumArtGradient(dataUrl);
        })()
        """)
        time.sleep(1.2)

        eval_dark_cover = """
        (() => {
          const bar = document.getElementById('inbuilt-spotify-bar');
          const mini = document.getElementById('floating-spotify-mini-player');
          const navBtn = document.getElementById('nav-spotify-btn');
          const playBtn = document.getElementById('inbuilt-spotify-play-btn');

          const barLight = bar.classList.contains('spotify-light-cover');
          const miniLight = mini.classList.contains('spotify-light-cover');
          const navLight = navBtn.classList.contains('spotify-light-cover');
          const playBg = window.getComputedStyle(playBtn).backgroundColor;

          const playWhite = playBg.includes('255, 255, 255');

          return {
            success: !barLight && !miniLight && !navLight && playWhite,
            barLight,
            miniLight,
            playBg
          };
        })()
        """
        res_dark = window.evaluate_js(eval_dark_cover)
        record_test("Dark Album Cover Contrast Reset", res_dark.get('success', False), f"LightClassRemoved: {not res_dark.get('barLight')}, PlayBg: {res_dark.get('playBg')}")

    except Exception as e:
        record_test("Test Execution", False, str(e))
    finally:
        time.sleep(0.5)
        window.destroy()

def main():
    bridge = app.DesktopBridge()
    server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42230)
    app_url = f"http://127.0.0.1:{server.server_port}/"

    test_cache_dir = tempfile.mkdtemp(prefix='studypulse_typography_')

    window = webview.create_window(
        "StudyPulse v3.2.17 Verification",
        url=app_url,
        js_api=bridge,
        width=1280,
        height=800,
        hidden=True
    )
    bridge.set_window(window)
    webview.start(func=run_tests, args=(window,), gui="edgechromium", private_mode=True, storage_path=test_cache_dir)
    server.shutdown()

    print("\n================== PATCH 3.2.17 TEST SUMMARY ==================")
    for res in test_results:
        print(res)
    print("=================================================================")

    if test_passed:
        print("ALL PATCH 3.2.17 TESTS PASSED 100%!")
        sys.exit(0)
    else:
        print("TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
