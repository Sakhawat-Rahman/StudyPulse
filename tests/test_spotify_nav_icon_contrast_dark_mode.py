import os
import sys
import time

sys.path.insert(0, r'G:\ADHD app')
import app
import webview

def run_tests():
    html_path = r'G:\ADHD app\studypulse.html'
    assert os.path.exists(html_path), 'studypulse.html not found'

    test_results = {}
    js_errors = []

    def on_loaded(window):
        try:
            time.sleep(1.2)
            eval_res = window.evaluate_js("""
                (() => {
                    const btn = document.getElementById('nav-spotify-btn');
                    const fp = document.getElementById('floating-spotify-mini-player');
                    const svg = btn.querySelector('svg');
                    const svgPath = btn.querySelector('svg path');
                    const results = {};

                    // Disable transitions during evaluation for instantaneous steady-state sampling
                    btn.style.transition = 'none';

                    // 1. Dark Mode Active (Mini-player Open, Idle/Paused with no gradient)
                    document.documentElement.classList.add('dark');
                    fp.classList.remove('hidden');
                    fp.style.display = 'flex';
                    window.spotifyState = { connected: true, is_playing: false };
                    window.updateNavSpotifyBtnState();

                    const darkActiveBg = window.getComputedStyle(btn).backgroundColor;
                    const darkActiveFill = window.getComputedStyle(svgPath).fill;
                    const darkActiveColor = window.getComputedStyle(svgPath).color;
                    results.darkActive = {
                        btnBg: darkActiveBg,
                        pathFill: darkActiveFill,
                        pathColor: darkActiveColor,
                        passed: darkActiveBg === 'rgb(255, 255, 255)' && (darkActiveFill === 'rgb(9, 9, 11)' || darkActiveFill === '#09090b')
                    };

                    // 2. Dark Mode Inactive (Mini-player Closed)
                    fp.classList.add('hidden');
                    fp.style.display = 'none';
                    window.updateNavSpotifyBtnState();
                    const darkInactiveBg = window.getComputedStyle(btn).backgroundColor;
                    const darkInactiveFill = window.getComputedStyle(svgPath).fill;
                    results.darkInactive = {
                        btnBg: darkInactiveBg,
                        pathFill: darkInactiveFill,
                        passed: darkInactiveBg === 'rgb(28, 28, 31)' && darkInactiveFill === 'rgb(161, 161, 170)'
                    };

                    // 3. Light Mode Active (Mini-player Open, Idle/Paused with no gradient)
                    document.documentElement.classList.remove('dark');
                    fp.classList.remove('hidden');
                    fp.style.display = 'flex';
                    window.updateNavSpotifyBtnState();
                    const lightActiveBg = window.getComputedStyle(btn).backgroundColor;
                    const lightActiveFill = window.getComputedStyle(svgPath).fill;
                    results.lightActive = {
                        btnBg: lightActiveBg,
                        pathFill: lightActiveFill,
                        passed: lightActiveBg === 'rgb(9, 9, 11)' && lightActiveFill === 'rgb(255, 255, 255)'
                    };

                    // 4. Light Mode Inactive (Mini-player Closed)
                    fp.classList.add('hidden');
                    fp.style.display = 'none';
                    window.updateNavSpotifyBtnState();
                    const lightInactiveBg = window.getComputedStyle(btn).backgroundColor;
                    const lightInactiveFill = window.getComputedStyle(svgPath).fill;
                    results.lightInactive = {
                        btnBg: lightInactiveBg,
                        pathFill: lightInactiveFill,
                        passed: lightInactiveBg === 'rgb(255, 255, 255)' && (lightInactiveFill === 'rgb(82, 82, 91)' || lightInactiveFill === '#52525b' || lightInactiveFill === 'currentColor')
                    };

                    // 5. Active Playback with Dark/Vibrant Gradient (Both Themes)
                    document.documentElement.classList.add('dark');
                    fp.classList.remove('hidden');
                    fp.style.display = 'flex';
                    window.spotifyState = { connected: true, is_playing: true };
                    window.currentSpotifyGradient = 'linear-gradient(135deg, rgb(39, 39, 48) 0%, rgb(22, 22, 28) 55%, rgb(14, 14, 18) 100%)';
                    window.currentSpotifyColors = { isLightCover: false };
                    window.updateNavSpotifyBtnState();
                    results.playingVibrantDark = {
                        flowingClass: btn.classList.contains('flowing-gradient-active'),
                        pathFill: window.getComputedStyle(svgPath).fill,
                        passed: btn.classList.contains('flowing-gradient-active') && window.getComputedStyle(svgPath).fill === 'rgb(255, 255, 255)'
                    };

                    // 6. Active Playback with Light Pastel Cover (spotify-light-cover)
                    window.currentSpotifyColors = { isLightCover: true };
                    window.updateNavSpotifyBtnState();
                    results.playingLightCoverDark = {
                        lightCoverClass: btn.classList.contains('spotify-light-cover'),
                        pathFill: window.getComputedStyle(svgPath).fill,
                        passed: btn.classList.contains('spotify-light-cover') && window.getComputedStyle(svgPath).fill === 'rgb(9, 9, 11)'
                    };

                    // Restore transition
                    btn.style.transition = '';

                    return results;
                })()
            """)
            test_results.update(eval_res)
        except Exception as e:
            test_results['error'] = str(e)
        finally:
            window.destroy()

    window = webview.create_window(
        'StudyPulse Contrast Verification',
        html_path,
        width=1280,
        height=800,
        hidden=True
    )
    webview.start(on_loaded, window, gui='edgechromium')

    print('=================================================================')
    print('STARTING SPOTIFY TOGGLE ICON CONTRAST VERIFICATION')
    print('=================================================================')
    all_passed = True
    for test_name, res in test_results.items():
        if isinstance(res, dict) and 'passed' in res:
            passed = res['passed']
            if not passed:
                all_passed = False
            status = '[PASS]' if passed else '[FAIL]'
            print(f'  {status} {test_name}: {res}')
        else:
            print(f'  [INFO] {test_name}: {res}')

    print('================== VERIFICATION SUMMARY ==================')
    if all_passed and 'error' not in test_results:
        print('ALL SPOTIFY TOGGLE ICON CONTRAST TESTS PASSED 100%!')
        return 0
    else:
        print('SOME TESTS FAILED!')
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
