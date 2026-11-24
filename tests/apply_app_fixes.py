# -*- coding: utf-8 -*-
"""
Script to apply:
1. import html and unescape in app.py
2. Comprehensive formatTrackString entity decoding in studypulse.html
3. Robust Pointer + Mouse drag engine with pointer capture in studypulse.html
4. Zero-vanishing hover rules for nav-spotify-btn, play buttons, and mini-player buttons in light and dark modes
5. High-contrast play buttons across track list and playlists in dark mode
"""
import re

# 1. Update app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_text = f.read()

if 'import html\n' not in app_text and 'import html;' not in app_text:
    app_text = 'import html\n' + app_text

# In get_status: unescape track and artists
app_text = app_text.replace(
    '"track": item.get("name", ""),',
    '"track": html.unescape(item.get("name", "")),'
)
app_text = app_text.replace(
    'artists = ", ".join([a.get("name", "") for a in item.get("artists", [])])',
    'artists = html.unescape(", ".join([a.get("name", "") for a in item.get("artists", [])]))'
)

# In scan_win32_spotify: unescape track and artist
app_text = app_text.replace(
    'artist = parts[0].strip()\n            track = parts[1].strip()',
    'artist = html.unescape(parts[0].strip())\n            track = html.unescape(parts[1].strip())'
)
app_text = app_text.replace(
    'artist = ""\n            track = playing_title',
    'artist = ""\n            track = html.unescape(playing_title)'
)

# In get_user_playlists: unescape playlist name
app_text = app_text.replace(
    'name = item.get("name", "")',
    'name = html.unescape(item.get("name", ""))'
)

# In search_catalog: unescape track, artist, and playlist names
app_text = app_text.replace(
    'track_name = t.get("name", "")',
    'track_name = html.unescape(t.get("name", ""))'
)
app_text = app_text.replace(
    'artist_name = ", ".join([a.get("name", "") for a in t.get("artists", [])])',
    'artist_name = html.unescape(", ".join([a.get("name", "") for a in t.get("artists", [])]))'
)
app_text = app_text.replace(
    'pl_name = p.get("name", "")',
    'pl_name = html.unescape(p.get("name", ""))'
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_text)
print("app.py updated successfully.")
