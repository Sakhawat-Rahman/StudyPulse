# -*- coding: utf-8 -*-
new_rows = """| BUG-066 | Mini-player dragging glitched and unresponsive to mouse button inputs due to document `mouseleave` and window `blur` aborts and native Windows tooltip interference | P1 | High | Engineered unified Pointer Capture engine (`setPointerCapture`), mouse fallbacks with window mouseup capture, `cursor: grab` feedback, and removed tooltip `title` attributes |
| BUG-067 | Hovering over Spotify nav button or play buttons in white/light mode caused icons to vanish (black-on-black or white-on-white) | P1 | High | Replaced inline icon fills with `fill: currentColor !important; color: inherit !important;`, added dedicated `:hover` rules enforcing white icon on active black button in light mode, and high contrast under `.spotify-light-cover` |
| BUG-068 | Track titles, artist labels, and playlist names displayed raw HTML entities (`Teacher&#039;s Pet`) | P2 | Medium | Upgraded `formatTrackString()` to decode decimal entities (`&#(\\d+);`), hex entities, quotes, apostrophes, and integrated `import html; html.unescape()` across all Spotify API endpoints in `app.py` |
| BUG-069 | Stale PyInstaller executable running bundled assets rather than live disk changes | P1 | High | Updated `app.py:get_asset_path()` to prioritize `studypulse.html` beside `sys.executable`, rebuilt `dist/StudyPulse.exe` via PyInstaller, and synchronized root `StudyPulse.exe` |
"""

with open('docs/StudyPulse_Comprehensive_Manual.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.strip() + '\n' + new_rows

with open('docs/StudyPulse_Comprehensive_Manual.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated StudyPulse_Comprehensive_Manual.md successfully.")
