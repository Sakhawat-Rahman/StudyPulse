# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, os.path.abspath('.'))
import webview
sys.stdout.reconfigure(encoding='utf-8')
import app

def check(window):
    time.sleep(2)
    js = """
    (() => {
        const btn = document.getElementById('nav-spotify-btn');
        document.documentElement.classList.remove('dark');
        const floatPlayer = document.getElementById('floating-spotify-mini-player');
        floatPlayer.classList.remove('hidden');
        floatPlayer.style.display = 'flex';
        btn.style.transition = 'none';
        window.updateNavSpotifyBtnState();

        const cs = window.getComputedStyle(btn);
        return {
            computedBg: cs.backgroundColor,
            computedColor: cs.color
        };
    })()
    """
    res = window.evaluate_js(js)
    print("Computed BG:", res['computedBg'])
    print("Computed Color:", res['computedColor'])
    window.destroy()

html_path = os.path.abspath('studypulse.html')
w = webview.create_window('Test Nav Style', url=f'file://{html_path}', hidden=True)
webview.start(check, w)
