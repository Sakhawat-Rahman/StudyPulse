# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, os.path.abspath('.'))
import webview
sys.stdout.reconfigure(encoding='utf-8')

def test_all_hovers(window):
    time.sleep(2)
    js = """
    (function() {
        var results = [];
        document.documentElement.classList.remove('dark');
        var floatPlayer = document.getElementById('floating-spotify-mini-player');
        if (floatPlayer) {
            floatPlayer.classList.remove('hidden');
            floatPlayer.style.display = 'flex';
        }
        if (window.updateNavSpotifyBtnState) window.updateNavSpotifyBtnState();

        var targets = [
            { id: 'nav-spotify-btn', name: 'Nav Spotify Button' },
            { id: 'floating-spotify-compact-toggle-btn', name: 'Mini-Player Mode Toggle' },
            { id: 'floating-spotify-focus-jump-btn', name: 'Mini-Player Studio Jump' },
            { id: 'floating-spotify-close-btn', name: 'Mini-Player Close (X)' },
            { id: 'floating-spotify-play-btn', name: 'Mini-Player Play Button' },
            { id: 'floating-spotify-prev-btn', name: 'Mini-Player Prev Button' },
            { id: 'floating-spotify-next-btn', name: 'Mini-Player Next Button' }
        ];

        for (var i = 0; i < targets.length; i++) {
            var t = targets[i];
            var el = document.getElementById(t.id);
            if (!el) {
                results.push({ name: t.name, missing: true });
                continue;
            }
            var csNormal = window.getComputedStyle(el);
            var svgNormal = el.querySelector('svg');
            var svgColorNormal = svgNormal ? window.getComputedStyle(svgNormal).color : 'no-svg';
            var svgFillNormal = svgNormal ? window.getComputedStyle(svgNormal).fill : 'no-svg';

            results.push({
                name: t.name,
                id: t.id,
                normalBg: csNormal.backgroundColor,
                normalColor: csNormal.color,
                svgColorNormal: svgColorNormal,
                svgFillNormal: svgFillNormal,
                classes: el.className
            });
        }
        return results;
    })()
    """
    res = window.evaluate_js(js)
    for r in res:
        print(f"--- {r['name']} ({r.get('id', '')}) ---")
        print("  Normal: bg =", r.get('normalBg'), "color =", r.get('normalColor'), "svgColor =", r.get('svgColorNormal'), "svgFill =", r.get('svgFillNormal'))
        print("  LightCover: bg =", r.get('lightCoverBg'), "color =", r.get('lightCoverColor'), "svgColor =", r.get('svgColorLightCover'), "svgFill =", r.get('svgFillLightCover'))
    window.destroy()

html_path = os.path.abspath('studypulse.html')
w = webview.create_window('Hover Check', url=f'file://{html_path}', hidden=True)
webview.start(test_all_hovers, w)
