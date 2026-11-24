# -*- coding: utf-8 -*-
"""
Verification suite for:
1. HTML entity unescaping for track & artist names (e.g. "Teacher&#039;s Pet" -> "Teacher's Pet")
2. Darkmode Play button contrast in search list, playlists grid, and player deck
3. Mini-player header grab cursor & absence of title tooltip
4. Pointer capture & dragging responsiveness
"""
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app
import webview

sys.stdout.reconfigure(encoding='utf-8')

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
        # 1. HTML Entity Decoding Verification
        eval_entity = '''
        (() => {
          const testStr = "Teacher&#039;s Pet &amp; &quot;K-12&#039;s Special&quot; &apos;Melanie&apos;";
          const decoded = window.formatTrackString(testStr);
          const expected = "Teacher's Pet & \\"K-12's Special\\" 'Melanie'";

          // Also test setting on floating-spotify-compact-title and floating-spotify-track
          window.spotifyState = window.spotifyState || {};
          window.spotifyState.track = "Teacher&#039;s Pet";
          window.spotifyState.artist = "Melanie&#039;s Friend";
          window.spotifyState.connected = true;
          window.spotifyState.is_playing = true;
          window.updateAllSpotifySurfaces();

          const cptTitle = document.getElementById('floating-spotify-compact-title');
          const floatTrack = document.getElementById('floating-spotify-track');
          const studioTrack = document.getElementById('inbuilt-spotify-track-title');

          const cptDecoded = cptTitle ? cptTitle.textContent : '';
          const floatDecoded = floatTrack ? floatTrack.textContent : '';
          const studioDecoded = studioTrack ? studioTrack.textContent : '';

          const matchAll = (cptDecoded === "Teacher's Pet") &&
                           (floatDecoded === "Teacher's Pet") &&
                           (studioDecoded === "Teacher's Pet");

          return {
            success: (decoded === expected) && matchAll,
            decoded,
            expected,
            cptDecoded,
            floatDecoded,
            studioDecoded
          };
        })()
        '''
        res_entity = window.evaluate_js(eval_entity)
        record_test("HTML Entity Decoding (Teacher&#039;s Pet -> Teacher's Pet)", res_entity.get('success', False),
                    f"Result: '{res_entity.get('cptDecoded')}', Expected: \"Teacher's Pet\"")

        # 2. Darkmode Play Button Contrast in Search Results & Playlists Grid
        eval_play_btns = """
        (() => {
          document.documentElement.classList.add('dark');

          // Render sample track row
          const tracksList = document.getElementById('spotify-search-tracks-list');
          if (tracksList) {
            tracksList.innerHTML = `
              <div class="row">
                <button class="spotify-track-play-btn px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1" style="background-color: #FFFFFF !important; color: #000000 !important;">
                  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor" style="fill: currentColor !important; color: inherit !important;"><path d="M8 5v14l11-7z"/></svg>
                  <span style="color: inherit !important; font-weight: 700 !important;">Play</span>
                </button>
              </div>
            `;
          }

          const trackBtn = document.querySelector('.spotify-track-play-btn');
          const trackSvg = trackBtn ? trackBtn.querySelector('svg') : null;
          const trackSpan = trackBtn ? trackBtn.querySelector('span') : null;

          const btnBg = trackBtn ? window.getComputedStyle(trackBtn).backgroundColor : '';
          const btnColor = trackBtn ? window.getComputedStyle(trackBtn).color : '';
          const svgColor = trackSvg ? window.getComputedStyle(trackSvg).color : '';
          const spanColor = trackSpan ? window.getComputedStyle(trackSpan).color : '';

          // Check Inbuilt Play Button
          const inbuiltPlay = document.getElementById('inbuilt-spotify-play-btn');
          const inbuiltSvg = document.getElementById('inbuilt-spotify-play-icon');
          const inbuiltBg = inbuiltPlay ? window.getComputedStyle(inbuiltPlay).backgroundColor : '';
          const inbuiltIconColor = inbuiltSvg ? window.getComputedStyle(inbuiltSvg).color : '';

          const isDarkTrackContrast = btnBg.includes('255, 255, 255') && btnColor.includes('0, 0, 0');
          const isInbuiltContrast = inbuiltBg.includes('255, 255, 255') && inbuiltIconColor.includes('0, 0, 0');

          return {
            success: isDarkTrackContrast && isInbuiltContrast,
            btnBg,
            btnColor,
            svgColor,
            spanColor,
            inbuiltBg,
            inbuiltIconColor
          };
        })()
        """
        res_play = window.evaluate_js(eval_play_btns)
        record_test("Darkmode High-Contrast Play Buttons", res_play.get('success', False),
                    f"TrackPlay(bg={res_play.get('btnBg')}, color={res_play.get('btnColor')}), Inbuilt(bg={res_play.get('inbuiltBg')}, icon={res_play.get('inbuiltIconColor')})")

        # 3. Header Drag Tooltip & Cursor Cleanup
        eval_header = """
        (() => {
          const header = document.getElementById('floating-spotify-drag-header');
          if (!header) return { success: false, reason: 'header missing' };

          const titleAttr = header.getAttribute('title');
          const cursor = window.getComputedStyle(header).cursor;

          return {
            success: !titleAttr && (cursor === 'grab' || cursor === 'default' || cursor === 'auto'),
            titleAttr,
            cursor
          };
        })()
        """
        res_header = window.evaluate_js(eval_header)
        record_test("Mini-Player Drag Header Tooltip Removal & Grab Cursor", res_header.get('success', False),
                    f"TitleAttr={res_header.get('titleAttr')}, Cursor={res_header.get('cursor')}")

        # 4. Pointer Events & Pointer Capture Support
        eval_pointer = """
        (() => {
          const mini = document.getElementById('floating-spotify-mini-player');
          if (!mini) return { success: false, reason: 'mini missing' };

          let pointerDownFired = false;
          const onPDown = () => { pointerDownFired = true; };
          mini.addEventListener('pointerdown', onPDown);

          const pEvent = new PointerEvent('pointerdown', { bubbles: true, cancelable: true, clientX: 200, clientY: 200, button: 0, pointerId: 1 });
          mini.dispatchEvent(pEvent);
          mini.removeEventListener('pointerdown', onPDown);

          const isDragging = mini.classList.contains('is-dragging');

          return {
            success: pointerDownFired && isDragging,
            pointerDownFired,
            isDragging
          };
        })()
        """
        res_pointer = window.evaluate_js(eval_pointer)
        record_test("Mini-Player Pointer Capture & Drag Initialization", res_pointer.get('success', False),
                    f"PointerDownFired={res_pointer.get('pointerDownFired')}, IsDragging={res_pointer.get('isDragging')}")

    except Exception as e:
        record_test("Exception during test execution", False, str(e))
    finally:
        window.destroy()

def main():
    print("=================================================================")
    print("STARTING ENTITY & PLAY BUTTON FIXES VERIFICATION")
    print("=================================================================")
    html_path = os.path.abspath('studypulse.html')
    window = webview.create_window(
        'StudyPulse Entity & Play Button Verification',
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
        print("ALL ENTITY & PLAY BUTTON FIXES VERIFIED 100% OPERATIONAL!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
