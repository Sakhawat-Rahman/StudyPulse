# -*- coding: utf-8 -*-
with open('studypulse.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace Light theme inactive
old_light = """    /* Light Theme Nav Spotify Button (Zero Vanishing Icon) */
    #nav-spotify-btn.nav-spotify-inactive {
      background-color: #FFFFFF !important;
      color: #3F3F46 !important;
      opacity: 0.48 !important;
      transform: scale(0.95) !important;
      filter: saturate(0.7) !important;
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
    }"""

new_light = """    /* Light Theme Nav Spotify Button (Zero Vanishing Icon) */
    #nav-spotify-btn.nav-spotify-inactive {
      background-color: #FFFFFF !important;
      color: #52525B !important;
      opacity: 0.85 !important;
      transform: scale(1) !important;
      filter: none !important;
      border: 1px solid rgba(0, 0, 0, 0.08) !important;
      outline: none !important;
      box-shadow: none !important;
    }"""

old_dark = """    /* Dark Theme Nav Spotify Button */
    html.dark #nav-spotify-btn.nav-spotify-inactive {
      background-color: #1C1C1F !important;
      color: #A1A1AA !important;
      opacity: 0.48 !important;
      transform: scale(0.95) !important;
      filter: saturate(0.7) !important;
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
    }"""

new_dark = """    /* Dark Theme Nav Spotify Button */
    html.dark #nav-spotify-btn.nav-spotify-inactive {
      background-color: #1C1C1F !important;
      color: #A1A1AA !important;
      opacity: 0.85 !important;
      transform: scale(1) !important;
      filter: none !important;
      border: 1px solid rgba(255, 255, 255, 0.08) !important;
      outline: none !important;
      box-shadow: none !important;
    }"""

# Normalize \r\n to \n for replacement
norm_text = text.replace('\r\n', '\n')
old_light_n = old_light.replace('\r\n', '\n')
new_light_n = new_light.replace('\r\n', '\n')
old_dark_n = old_dark.replace('\r\n', '\n')
new_dark_n = new_dark.replace('\r\n', '\n')

assert old_light_n in norm_text, "old_light not found!"
assert old_dark_n in norm_text, "old_dark not found!"

norm_text = norm_text.replace(old_light_n, new_light_n)
norm_text = norm_text.replace(old_dark_n, new_dark_n)

# Write back with CRLF
with open('studypulse.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(norm_text)

print("Successfully replaced inactive CSS rules in studypulse.html")
