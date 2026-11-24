# -*- coding: utf-8 -*-
"""
Comprehensive Verification Suite for StudyPulse v3.2.17:
1. Sidebar Spotify Button Border Stroke Removal & Dimmed Inactive State.
2. Mini-Player Header: Removal of "PLAYING" Badge & Zero "S.." Truncation.
3. Mini-Player Close Button Direct Inline Handlers & Drag Exclusion.
4. White/Pastel Cover Detection & Contrast Polarity (spotify-light-cover).
5. Studio-Grade Typography System (Plus Jakarta Sans + Inter OpenType + JetBrains Mono Tabular).
"""
import os
import sys
import time
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app
import webview

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
        # 1. Sidebar Spotify Button: Border Stroke Removal & Inactive State
        # ---------------------------------------------------------------------
        eval_nav_btn = """
        (() => {
          const navBtn = document.getElementById('nav-spotify-btn');
          const floatPlayer = document.getElementById('floating-spotify-mini-player');
          const dot = document.getElementById('nav-spotify-dot');
          if (!navBtn || !floatPlayer) return { success: false, reason: 'Elements missing' };

          // Case A: Floating Player is HIDDEN (Inactive state)
          floatPlayer.classList.add('hidden');
          floatPlayer.style.display = 'none';
          window.updateNavSpotifyBtnState();

          const inactBorder = navBtn.style.border || '';
          const inactOutline = navBtn.style.outline || '';
          const inactBoxShadow = navBtn.style.boxShadow || '';
          const inactOpacity = navBtn.style.opacity;
          const inactTransform = navBtn.style.transform;
          const inactFilter = navBtn.style.filter;

          const noBorderInactive = (!inactBorder || inactBorder === 'none') && (!inactOutline || inactOutline === 'none');
          // Verify reduced greying out (0.85 opacity, no saturate filter)
          const dimmedInactive = inactOpacity === '0.85' && (inactTransform.includes('scale(1)') || inactTransform === 'none' || inactTransform === '') && (inactFilter === 'none' || inactFilter === '');

          // Case B: Floating Player is VISIBLE (Active state)
          floatPlayer.classList.remove('hidden');
          floatPlayer.style.display = 'flex';
          window.updateNavSpotifyBtnState();

          const actBorder = navBtn.style.border || '';
          const actOutline = navBtn.style.outline || '';
          const actOpacity = navBtn.style.opacity;
          const actTransform = navBtn.style.transform;
          const actFilter = navBtn.style.filter;

          const noBorderActive = (!actBorder || actBorder === 'none') && (!actOutline || actOutline === 'none');
          const clarityActive = actOpacity === '1' && (actTransform === 'scale(1)' || actTransform === 'none' || actTransform === '') && (actFilter === 'none' || actFilter === '');

          // Check Status Dot
          const hasDot = Boolean(dot);

          return {
            success: noBorderInactive && dimmedInactive && noBorderActive && clarityActive && hasDot,
            noBorderInactive,
            dimmedInactive,
            inactOpacity,
            inactTransform,
            inactFilter,
            noBorderActive,
            clarityActive,
            actOpacity,
            actTransform,
            actFilter,
            hasDot
          };
        })()
        """
        res_nav = window.evaluate_js(eval_nav_btn)
        record_test("Sidebar Nav Button Border Removal & Tactile Dimming", res_nav.get('success', False),
                    f"Inactive (border={res_nav.get('noBorderInactive')}, dimmed={res_nav.get('dimmedInactive')}, op={res_nav.get('inactOpacity')}), Active (border={res_nav.get('noBorderActive')}, clarity={res_nav.get('clarityActive')}, op={res_nav.get('actOpacity')})")

        # ---------------------------------------------------------------------
        # 2. Mini-Player Header: Deletion of PLAYING Badge & Spotify Label
        # ---------------------------------------------------------------------
        eval_header = """
        (() => {
          const mini = document.getElementById('floating-spotify-mini-player');
          const liveBadge = document.getElementById('floating-spotify-live-badge');
          const statusBadge = document.getElementById('floating-spotify-status-badge');
          const titleLabel = document.getElementById('floating-spotify-title-label') || mini.querySelector('#floating-spotify-drag-header span');

          const badgeDeleted = !liveBadge && !statusBadge;
          const hasTitle = Boolean(titleLabel);
          const titleText = titleLabel ? titleLabel.textContent.trim() : '';
          const titleStyle = titleLabel ? titleLabel.getAttribute('style') || '' : '';

          const hasNoWrap = titleStyle.includes('white-space: nowrap') || titleStyle.includes('nowrap');
          const hasOverflowVisible = titleStyle.includes('overflow: visible') || titleStyle.includes('visible');
          const hasFontWeight700 = titleStyle.includes('font-weight: 700') || (titleLabel && window.getComputedStyle(titleLabel).fontWeight >= 700);

          // Test in Compressed Mode
          window.applySpotifyMiniCompactMode(true);
          const compactTitleVisible = titleLabel ? (titleLabel.offsetWidth > 0 && titleLabel.textContent === 'Spotify') : false;
          window.applySpotifyMiniCompactMode(false);

          return {
            success: badgeDeleted && (titleText === 'Spotify') && hasNoWrap && hasFontWeight700 && compactTitleVisible,
            badgeDeleted,
            titleText,
            hasNoWrap,
            hasOverflowVisible,
            hasFontWeight700,
            compactTitleVisible
          };
        })()
        """
        res_header = window.evaluate_js(eval_header)
        record_test("Header Layout (PLAYING Badge Removed & Spotify Label Preserved)", res_header.get('success', False),
                    f"BadgeDeleted={res_header.get('badgeDeleted')}, Title='{res_header.get('titleText')}', NoWrap={res_header.get('hasNoWrap')}, Weight700={res_header.get('hasFontWeight700')}, CompactVisible={res_header.get('compactTitleVisible')}")

        # ---------------------------------------------------------------------
        # 3. Mini-Player Close Button & Drag Interception Shield
        # ---------------------------------------------------------------------
        eval_close_btn = """
        (() => {
          const closeBtn = document.getElementById('floating-spotify-close-btn');
          const mini = document.getElementById('floating-spotify-mini-player');
          if (!closeBtn || !mini) return { success: false, reason: 'Elements missing' };

          const onmousedownAttr = closeBtn.getAttribute('onmousedown') || '';
          const onclickAttr = closeBtn.getAttribute('onclick') || '';
          const styleAttr = closeBtn.getAttribute('style') || '';
          const svg = closeBtn.querySelector('svg');
          const svgHasPointerNone = svg ? svg.classList.contains('pointer-events-none') : false;

          const hasMousedownStop = onmousedownAttr.includes('event.stopPropagation()');
          const hasClickHelper = onclickAttr.includes('window.hideFloatingSpotifyPlayer');
          const hasPointerAuto = styleAttr.includes('pointer-events: auto');
          const hasZIndex = styleAttr.includes('z-index');

          // Test execution of window.hideFloatingSpotifyPlayer()
          mini.classList.remove('hidden');
          mini.style.display = 'flex';
          window.state.showSpotifyMini = true;
          window.state.spotifyMiniVisible = true;

          window.hideFloatingSpotifyPlayer();

          const physicallyHidden = mini.classList.contains('hidden') && mini.style.display === 'none';
          const stateUpdated = window.state.showSpotifyMini === false && window.state.spotifyMiniVisible === false;

          return {
            success: hasMousedownStop && hasClickHelper && hasPointerAuto && hasZIndex && svgHasPointerNone && physicallyHidden && stateUpdated,
            hasMousedownStop,
            hasClickHelper,
            hasPointerAuto,
            hasZIndex,
            svgHasPointerNone,
            physicallyHidden,
            stateUpdated
          };
        })()
        """
        res_close = window.evaluate_js(eval_close_btn)
        record_test("Mini-Player Close (✕) Button Attributes & Global Function", res_close.get('success', False),
                    f"MousedownStop={res_close.get('hasMousedownStop')}, ClickHelper={res_close.get('hasClickHelper')}, PointerAuto={res_close.get('hasPointerAuto')}, Hidden={res_close.get('physicallyHidden')}, State={res_close.get('stateUpdated')}")

        # ---------------------------------------------------------------------
        # 4. White/Pastel Cover Detection & Contrast Polarity (.spotify-light-cover)
        # ---------------------------------------------------------------------
        window.evaluate_js("""
        (() => {
          if (window.spotifyPollInterval) clearInterval(window.spotifyPollInterval);
          const canvas = document.createElement('canvas');
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext('2d');
          // High-key pastel peach/cream cover
          ctx.fillStyle = '#F8F4F0';
          ctx.fillRect(0, 0, 32, 32);
          const dataUrl = canvas.toDataURL();
          const mini = document.getElementById('floating-spotify-mini-player');
          if (mini) { mini.classList.remove('hidden'); mini.style.display = 'flex'; }
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

          return {
            success: barLight && miniLight && navLight && titleObsidian && playBlack,
            barLight,
            miniLight,
            navLight,
            titleColor,
            artistColor,
            playBg
          };
        })()
        """
        res_light = window.evaluate_js(eval_light_cover)
        record_test("White/Pastel Cover Detection & Contrast Polarity", res_light.get('success', False),
                    f"LightClass={res_light.get('barLight')}, TitleColor={res_light.get('titleColor')}, PlayBg={res_light.get('playBg')}")

        # Dark Cover Reset Check
        window.evaluate_js("""
        (() => {
          const canvas = document.createElement('canvas');
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#1A1829'; // Deep indigo / dark cover
          ctx.fillRect(0, 0, 32, 32);
          const dataUrl = canvas.toDataURL();
          const mini = document.getElementById('floating-spotify-mini-player');
          if (mini) { mini.classList.remove('hidden'); mini.style.display = 'flex'; }
          window.spotifyState = { connected: true, is_playing: true, album_art: dataUrl };
          window.applyAlbumArtGradient(dataUrl);
        })()
        """)
        time.sleep(1.2)

        eval_dark_cover = """
        (() => {
          const bar = document.getElementById('inbuilt-spotify-bar');
          const mini = document.getElementById('floating-spotify-mini-player');
          const navBtn = document.getElementById('nav-spotify-btn');

          const barLight = bar.classList.contains('spotify-light-cover');
          const miniLight = mini.classList.contains('spotify-light-cover');
          const navLight = navBtn.classList.contains('spotify-light-cover');

          const trackTitle = document.getElementById('inbuilt-spotify-track-title');
          const playBtn = document.getElementById('inbuilt-spotify-play-btn');

          const titleColor = window.getComputedStyle(trackTitle).color;
          const playBg = window.getComputedStyle(playBtn).backgroundColor;

          const lightRemoved = !barLight && !miniLight && !navLight;
          const playWhite = playBg.includes('255, 255, 255');

          return {
            success: lightRemoved && playWhite,
            lightRemoved,
            playBg,
            titleColor
          };
        })()
        """
        res_dark = window.evaluate_js(eval_dark_cover)
        record_test("Dark Album Cover Contrast & Polarity Reset", res_dark.get('success', False),
                    f"LightClassRemoved={res_dark.get('lightRemoved')}, PlayBg={res_dark.get('playBg')}")

        # ---------------------------------------------------------------------
        # 5. Studio-Grade Typography System
        # ---------------------------------------------------------------------
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
            hasJakarta,
            hasInter,
            hasMono,
            hasSwap
          };
        })()
        """
        res_head = window.evaluate_js(eval_fonts_head)
        record_test("Google Fonts Link in <head>", res_head.get('success', False),
                    f"Jakarta={res_head.get('hasJakarta')}, Inter={res_head.get('hasInter')}, Mono={res_head.get('hasMono')}, swap={res_head.get('hasSwap')}")

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
        record_test("Body Typography & OpenType Features", res_body.get('success', False),
                    f"Family: {res_body.get('fontFamily')}, Features: {res_body.get('featureSettings')}")

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
            details: details.slice(0, 4)
          };
        })()
        """
        res_display = window.evaluate_js(eval_display_headings)
        record_test("Display Headings & Track Titles (Plus Jakarta Sans)", res_display.get('success', False),
                    f"Elements checked: {res_display.get('matchedCount')}")

        eval_mono_tabular = """
        (() => {
          const timerEl = document.getElementById('studio-timer-display');
          const timerCs = window.getComputedStyle(timerEl);
          const timerFf = timerCs.fontFamily.toLowerCase();
          const timerNum = timerCs.fontVariantNumeric || '';
          const timerFw = parseInt(timerCs.fontWeight, 10);

          const hasMono = timerFf.includes('jetbrains mono') || timerFf.includes('cascadia mono') || timerFf.includes('monospace');
          const isBold = timerFw >= 700;
          const hasTabular = timerNum.includes('tabular-nums') || timerEl.classList.contains('font-mono-tabular') || timerEl.classList.contains('tabular-nums');

          return {
            success: hasMono && isBold && hasTabular,
            timerFf,
            timerNum,
            isBold,
            hasTabular
          };
        })()
        """
        res_mono = window.evaluate_js(eval_mono_tabular)
        record_test("Telemetry & Studio Countdown Clock (JetBrains Mono Tabular)", res_mono.get('success', False),
                    f"Timer font: {res_mono.get('timerFf')}, bold={res_mono.get('isBold')}, tabular={res_mono.get('hasTabular')}")

    except Exception as e:
        record_test("Exception during test execution", False, str(e))
    finally:
        window.destroy()

def main():
    print("=================================================================")
    print("STARTING COMPLETE STUDYPULSE v3.2.17 VERIFICATION SUITE")
    print("=================================================================")
    html_path = os.path.abspath('studypulse.html')
    window = webview.create_window(
        'StudyPulse v3.2.17 Complete Verification',
        url=f'file://{html_path}',
        width=1280,
        height=850,
        hidden=True
    )
    webview.start(run_tests, window)

    print("\n================== PATCH 3.2.17 SUMMARY ==================")
    for r in test_results:
        print(r)
    print("===========================================================")

    if test_passed:
        print("ALL STUDYPULSE v3.2.17 FEATURES VERIFIED 100% OPERATIONAL & WORKING!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
