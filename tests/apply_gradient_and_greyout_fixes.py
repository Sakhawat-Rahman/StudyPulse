# -*- coding: utf-8 -*-
import re

with open('studypulse.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update resetSpotifyGradientToDefault to clear window.currentSpotifyGradient
content = content.replace(
    """    function resetSpotifyGradientToDefault() {
      _lastGradientArtUrl = '__unset__';
      window.currentSpotifyColors = null;""",
    """    function resetSpotifyGradientToDefault() {
      _lastGradientArtUrl = '__unset__';
      window.currentSpotifyColors = null;
      window.currentSpotifyGradient = null;"""
)

# 2. Update applyAlbumArtGradient to store window.currentSpotifyGradient on every branch
# Case A: High-Key / Light Cover
content = content.replace(
    """            // Luminous Pearl / Pastel Mesh Gradient
            const lightGradient = `linear-gradient(135deg, rgb(${r1}, ${g1}, ${b1_rgb}) 0%, rgb(${r2}, ${g2}, ${b2_rgb}) 52%, rgb(${r3}, ${g3}, ${b3_rgb}) 100%)`;
            window.currentSpotifyColors = {
              r1, g1, b1: b1_rgb,
              r2, g2, b2: b2_rgb,
              r3, g3, b3: b3_rgb,
              isLightCover: true
            };
            setBg(lightGradient, true);""",
    """            // Luminous Pearl / Pastel Mesh Gradient
            const lightGradient = `linear-gradient(135deg, rgb(${r1}, ${g1}, ${b1_rgb}) 0%, rgb(${r2}, ${g2}, ${b2_rgb}) 52%, rgb(${r3}, ${g3}, ${b3_rgb}) 100%)`;
            window.currentSpotifyColors = {
              r1, g1, b1: b1_rgb,
              r2, g2, b2: b2_rgb,
              r3, g3, b3: b3_rgb,
              isLightCover: true
            };
            window.currentSpotifyGradient = lightGradient;
            setBg(lightGradient, true);"""
)

# Case B: Grayscale / Low Saturated (< 4)
content = content.replace(
    """          // Case B – Mid-Tone / Vibrant / Dark Cover
          if (totalSaturated < 4) {
            window.currentSpotifyColors = null;
            setBg(defaultObsidianGradient, false);
            if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
            return;
          }""",
    """          // Case B – Mid-Tone / Vibrant / Dark Cover
          if (totalSaturated < 4) {
            window.currentSpotifyColors = null;
            window.currentSpotifyGradient = defaultObsidianGradient;
            setBg(defaultObsidianGradient, false);
            if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
            return;
          }"""
)

# Case B: Populated == 0
content = content.replace(
    """          if (populated.length === 0) {
            window.currentSpotifyColors = null;
            setBg(defaultObsidianGradient, false);
            if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
            return;
          }""",
    """          if (populated.length === 0) {
            window.currentSpotifyColors = null;
            window.currentSpotifyGradient = defaultObsidianGradient;
            setBg(defaultObsidianGradient, false);
            if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
            return;
          }"""
)

# Case B: Vibrant Gradient
content = content.replace(
    """          const vibrantGradient = `linear-gradient(135deg, rgb(${r1}, ${g1}, ${b1_rgb}) 0%, rgb(${r2}, ${g2}, ${b2_rgb}) 55%, rgb(${r3}, ${g3}, ${b3_rgb}) 100%)`;
          window.currentSpotifyColors = {
            r1, g1, b1: b1_rgb,
            r2, g2, b2: b2_rgb,
            r3, g3, b3: b3_rgb,
            isLightCover: false
          };
          setBg(vibrantGradient, false);""",
    """          const vibrantGradient = `linear-gradient(135deg, rgb(${r1}, ${g1}, ${b1_rgb}) 0%, rgb(${r2}, ${g2}, ${b2_rgb}) 55%, rgb(${r3}, ${g3}, ${b3_rgb}) 100%)`;
          window.currentSpotifyColors = {
            r1, g1, b1: b1_rgb,
            r2, g2, b2: b2_rgb,
            r3, g3, b3: b3_rgb,
            isLightCover: false
          };
          window.currentSpotifyGradient = vibrantGradient;
          setBg(vibrantGradient, false);"""
)

# If no imgUrl or img onerror
content = content.replace(
    """      if (!imgUrl) {
        setBg(defaultObsidianGradient, false);
        return;
      }""",
    """      if (!imgUrl) {
        window.currentSpotifyGradient = defaultObsidianGradient;
        setBg(defaultObsidianGradient, false);
        return;
      }"""
)

content = content.replace(
    """      img.onerror = function() {
        console.error('applyAlbumArtGradient img onerror:', imgUrl);
        window.__lastGradientError = 'img onerror';
        window.currentSpotifyColors = null;
        setBg(defaultObsidianGradient, false);
        if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
      };""",
    """      img.onerror = function() {
        console.error('applyAlbumArtGradient img onerror:', imgUrl);
        window.__lastGradientError = 'img onerror';
        window.currentSpotifyColors = null;
        window.currentSpotifyGradient = defaultObsidianGradient;
        setBg(defaultObsidianGradient, false);
        if (typeof updateNavSpotifyBtnState === 'function') updateNavSpotifyBtnState();
      };"""
)

# 3. Update CSS for flowing-gradient-active: remove 250% zoom and infinite panning that alters perceived colors
content = re.sub(
    r'\.flowing-gradient-active\s*\{[^}]*\}',
    """.flowing-gradient-active {
      background-size: 100% 100% !important;
      color: #FFFFFF !important;
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
    }""",
    content
)

# 4. Update CSS for nav-spotify-inactive: reduce greying out from 0.48 to 0.85, remove desaturate filter
content = content.replace(
    """    /* Light Theme Nav Spotify Button (Zero Vanishing Icon) */
    #nav-spotify-btn.nav-spotify-inactive {
      background-color: #FFFFFF !important;
      color: #3F3F46 !important;
      opacity: 0.48 !important;
      transform: scale(0.95) !important;
      filter: saturate(0.7) !important;
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
    }
    #nav-spotify-btn.nav-spotify-inactive:hover {
      background-color: #F4F4F5 !important;
      color: #09090B !important;
      opacity: 0.88 !important;
      transform: scale(1) !important;
      filter: saturate(1) !important;
    }
    #nav-spotify-btn.nav-spotify-inactive svg,
    #nav-spotify-btn.nav-spotify-inactive:hover svg,
    #nav-spotify-btn.nav-spotify-inactive:hover svg path {
      fill: #09090B !important;
      color: #09090B !important;
    }""",
    """    /* Light Theme Nav Spotify Button (Zero Vanishing Icon) */
    #nav-spotify-btn.nav-spotify-inactive {
      background-color: #FFFFFF !important;
      color: #52525B !important;
      opacity: 0.85 !important;
      transform: scale(1) !important;
      filter: none !important;
      border: 1px solid rgba(0, 0, 0, 0.08) !important;
      outline: none !important;
      box-shadow: none !important;
    }
    #nav-spotify-btn.nav-spotify-inactive:hover {
      background-color: #F4F4F5 !important;
      color: #09090B !important;
      opacity: 1 !important;
      transform: scale(1.05) !important;
      filter: none !important;
    }
    #nav-spotify-btn.nav-spotify-inactive svg,
    #nav-spotify-btn.nav-spotify-inactive:hover svg,
    #nav-spotify-btn.nav-spotify-inactive:hover svg path {
      fill: #09090B !important;
      color: #09090B !important;
    }"""
)

content = content.replace(
    """    /* Dark Theme Nav Spotify Button */
    html.dark #nav-spotify-btn.nav-spotify-inactive {
      background-color: #1C1C1F !important;
      color: #A1A1AA !important;
      opacity: 0.48 !important;
      transform: scale(0.95) !important;
      filter: saturate(0.7) !important;
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
    }
    html.dark #nav-spotify-btn.nav-spotify-inactive:hover {
      background-color: #27272A !important;
      color: #FFFFFF !important;
      opacity: 0.88 !important;
      transform: scale(1) !important;
      filter: saturate(1) !important;
    }
    html.dark #nav-spotify-btn.nav-spotify-inactive svg,
    html.dark #nav-spotify-btn.nav-spotify-inactive:hover svg,
    html.dark #nav-spotify-btn.nav-spotify-inactive:hover svg path {
      fill: #FFFFFF !important;
      color: #FFFFFF !important;
    }""",
    """    /* Dark Theme Nav Spotify Button */
    html.dark #nav-spotify-btn.nav-spotify-inactive {
      background-color: #1C1C1F !important;
      color: #A1A1AA !important;
      opacity: 0.85 !important;
      transform: scale(1) !important;
      filter: none !important;
      border: 1px solid rgba(255, 255, 255, 0.08) !important;
      outline: none !important;
      box-shadow: none !important;
    }
    html.dark #nav-spotify-btn.nav-spotify-inactive:hover {
      background-color: #27272A !important;
      color: #FFFFFF !important;
      opacity: 1 !important;
      transform: scale(1.05) !important;
      filter: none !important;
    }
    html.dark #nav-spotify-btn.nav-spotify-inactive svg,
    html.dark #nav-spotify-btn.nav-spotify-inactive:hover svg,
    html.dark #nav-spotify-btn.nav-spotify-inactive:hover svg path {
      fill: #FFFFFF !important;
      color: #FFFFFF !important;
    }"""
)

# 5. Update HTML tag for #nav-spotify-btn (line 1574)
content = re.sub(
    r'<button id="nav-spotify-btn"[^>]*>',
    '<button id="nav-spotify-btn" class="w-11 h-11 rounded-full flex items-center justify-center transition cursor-pointer relative nav-spotify-inactive" style="border: 1px solid rgba(0,0,0,0.08); outline: none !important; box-shadow: none !important; opacity: 0.85; transform: scale(1); filter: none;" title="Toggle Spotify Mini-Player (Dashboard & Calendar)">',
    content
)

# 6. Update updateNavSpotifyBtnState implementation in JS
old_update_fn = r'window\.updateNavSpotifyBtnState = updateNavSpotifyBtnState;\s*function updateNavSpotifyBtnState\(\) \{[\s\S]*?resetSpotifyGradientToDefault\(\);\s*\}\s*\}'

new_update_fn = """window.updateNavSpotifyBtnState = updateNavSpotifyBtnState;
      function updateNavSpotifyBtnState() {
        const navSpotifyBtn = document.getElementById('nav-spotify-btn');
        const floatPlayer = getFloatingMiniPlayer();
        const dot = document.getElementById('nav-spotify-dot');
        if (!navSpotifyBtn) return;
        const isVisible = floatPlayer && !floatPlayer.classList.contains('hidden') && floatPlayer.style.display !== 'none';
        
        // Ensure zero ring or outline
        navSpotifyBtn.style.setProperty('outline', 'none', 'important');
        navSpotifyBtn.style.setProperty('box-shadow', 'none', 'important');

        if (isVisible) {
          // Mini-player is open: button is ACTIVE (not greyed out)
          navSpotifyBtn.classList.add('bg-ink-950', 'text-white', 'nav-spotify-active');
          navSpotifyBtn.classList.remove('bg-white/90', 'text-ink-700', 'nav-spotify-inactive', 'border-zinc-200/80', 'dark:border-[#27272A]', 'ring-2', 'ring-ink-950', 'dark:ring-[#EAEAE6]');
          navSpotifyBtn.style.opacity = '1';
          navSpotifyBtn.style.transform = 'scale(1)';
          navSpotifyBtn.style.filter = 'none';
          navSpotifyBtn.style.setProperty('border', 'none', 'important');
        } else {
          // Mini-player is closed: button is INACTIVE (greyed out) with reduced, tasteful dimming (0.85)
          navSpotifyBtn.classList.remove('bg-ink-950', 'text-white', 'nav-spotify-active', 'ring-2', 'ring-ink-950', 'dark:ring-[#EAEAE6]');
          navSpotifyBtn.classList.add('bg-white/90', 'text-ink-700', 'nav-spotify-inactive');
          navSpotifyBtn.style.opacity = '0.85';
          navSpotifyBtn.style.transform = 'scale(1)';
          navSpotifyBtn.style.filter = 'none';
          navSpotifyBtn.style.removeProperty('border');
        }

        const st = (typeof window !== 'undefined' && window.spotifyState) ? window.spotifyState : ((typeof spotifyState !== 'undefined') ? spotifyState : null);
        const isConnected = Boolean(st && st.connected);
        const isPlaying = Boolean(isConnected && st.is_playing);

        if (dot) {
          dot.classList.remove('hidden', 'bg-emerald-500');
          if (!isConnected) {
            // Solid Red Dot
            dot.style.setProperty('background-color', '#EF4444', 'important');
            dot.style.boxShadow = '0 0 6px rgba(239, 68, 68, 0.6)';
            dot.style.display = 'block';
            dot.classList.remove('animate-pulse');
          } else if (!isPlaying) {
            // Solid Yellow Dot
            dot.style.setProperty('background-color', '#FACC15', 'important');
            dot.style.boxShadow = '0 0 6px rgba(250, 204, 21, 0.6)';
            dot.style.display = 'block';
            dot.classList.remove('animate-pulse');
          } else {
            // Pulsating Green Dot
            dot.style.setProperty('background-color', '#22C55E', 'important');
            dot.style.boxShadow = '0 0 8px rgba(34, 197, 94, 0.8)';
            dot.style.display = 'block';
            dot.classList.add('animate-pulse');
          }
        }

        // Gradient Logic: EXACT SAME gradient as album cover, and ONLY present when:
        // 1) Song is actively playing, AND
        // 2) Button is active (mini-player open) and NOT greyed out!
        const shouldShowGradient = isVisible && isConnected && isPlaying;

        if (shouldShowGradient) {
          const grad = window.currentSpotifyGradient || 'linear-gradient(135deg, #272730 0%, #16161C 55%, #0E0E12 100%)';
          navSpotifyBtn.style.background = grad;
          navSpotifyBtn.style.backgroundImage = grad;
          navSpotifyBtn.classList.add('flowing-gradient-active');
          if (window.currentSpotifyColors && window.currentSpotifyColors.isLightCover) {
            navSpotifyBtn.classList.add('spotify-light-cover');
          } else {
            navSpotifyBtn.classList.remove('spotify-light-cover');
          }
        } else {
          // Zero gradient when button is greyed out (mini-player closed) OR when music is paused/idle
          navSpotifyBtn.style.background = '';
          navSpotifyBtn.style.backgroundImage = '';
          navSpotifyBtn.classList.remove('flowing-gradient-active', 'spotify-light-cover');
          if (!isConnected || !isPlaying) {
            resetSpotifyGradientToDefault();
          }
        }
      }"""

content = re.sub(old_update_fn, new_update_fn, content)

with open('studypulse.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied exact gradient & greyed-out fixes to studypulse.html successfully.")
