# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

log_patch = """
---

## Patch 3.2.18: Unified Pointer Drag Engine, Zero-Vanishing Hover Contrast, HTML Entity Decoding & Executable Synchronization

**Patch Date:** 2026-11-09  
**Scope:** `app.py`, `studypulse.html`, `dist/StudyPulse.exe`, `StudyPulse.exe`  
**Test Coverage:** `tests/test_hover_and_drag_fixes.py`, `tests/test_entity_and_play_button_fixes.py`, `tests/verify_all_last_prompt_features.py` (100% PASS)

### Defects Resolved:

1. **BUG-024: Mini-Player Drag Engine Glitch & Unresponsiveness**
   - **Root Cause:**
     - Registered `mouseleave` on `document` and `blur` on `window` terminated drag immediately when cursor moved rapidly or near the Edge WebView2 window borders.
     - `#floating-spotify-drag-header` contained `title="Drag to reposition (magnetically snaps to corners)"`, spawning native Windows `tooltips_class32` popups that stole focus and dropped click-drags.
     - Failsafe `(e.buttons & 1) === 0` terminated on the first movement pixel if WebView2 synthetic events temporarily lagged button state.
   - **Fix:**
     - Unified Pointer Capture Engine: Attached `pointerdown`, `pointermove`, `pointerup`, and `pointercancel` with native `setPointerCapture()` and `releasePointerCapture()`.
     - Preserved backward-compatible standard Mouse Events (`mousedown`, `mousemove`, `mouseup`) with window-level mouseup capturing.
     - Removed `mouseleave` and `blur` early cancellations; failsafe buttons check only activates after 5px of confirmed movement.
     - Stripped native `title` tooltip and `cursor-move` class; applied consistent `cursor: grab` when idle and `cursor: grabbing !important` during active drag across both header and body.
     - Maintained full 140px corner snapping (`tl`, `tr`, `bl`, `br`, `custom`) and responsive window resize edge clamping.

2. **BUG-025: Hover Icon Vanishing in Light / White Mode**
   - **Root Cause:**
     - In light mode with an active mini-player, `#nav-spotify-btn` has black background (`#09090B`). Hovering lacked explicit white SVG fill enforcement, causing black-on-black invisibility.
     - Mini-player and playbar play buttons (`#floating-spotify-play-btn`, `#floating-spotify-compact-play-btn`, `#inbuilt-spotify-play-btn`) had hardcoded inline styles `style="fill: #000000 !important; color: #000000 !important;"`. Under `spotify-light-cover`, button background was set to `#09090B`, turning the icon and text pitch black on black.
   - **Fix:**
     - Replaced inline icon fills with `fill: currentColor !important; color: inherit !important;` so child icons and labels dynamically adapt to parent button contrast.
     - Added dedicated CSS hover rules for `#nav-spotify-btn.nav-spotify-active:hover` forcing `#FFFFFF` icon fill on dark button in light mode, and `#09090B` icon fill on light button in dark mode.
     - Enforced high-contrast hover states across all mini-player header buttons (`#floating-spotify-compact-toggle-btn`, `#floating-spotify-focus-jump-btn`, `#floating-spotify-close-btn`) under both standard and light-cover modes.

3. **BUG-026: HTML Entity Rendering in Track & Playlist Names (`Teacher&#039;s Pet`)**
   - **Root Cause:**
     - Escaped numeric and named entities (`&#039;`, `&#39;`, `&apos;`, `&quot;`) from iTunes and Spotify metadata searches were rendered verbatim via DOM `textContent`.
   - **Fix:**
     - Upgraded `formatTrackString(str)` in `studypulse.html` to comprehensively decode numeric decimal entities (`&#(\\d+);`), hexadecimal entities (`&#x([0-9a-f]+);`), quotes (`&quot;`), apostrophes (`&#0*39;`, `&apos;`), and XML delimiters.
     - Integrated `import html; html.unescape()` across all Spotify API handlers in `app.py` (`get_status()`, `scan_win32_spotify()`, `get_user_playlists()`, `search_catalog()`).

4. **BUG-027: Dark Mode Play Button Contrast in Search Results & Playlists**
   - **Root Cause:**
     - Playlist cards and search track rows in dark mode required crisp, bright play affordance matching the rest of the app toggles.
   - **Fix:**
     - Enforced crisp white pill buttons with black play icons and bold text (`background-color: #FFFFFF !important; color: #000000 !important;`) on `.spotify-track-play-btn`, `.spotify-fav-card .spotify-playlist-play-btn`, and `#spotify-search-playlists-grid .spotify-playlist-play-btn`.
     - Added smooth hover lift with `#F4F4F5` / `#E4E4E7` backgrounds and zero contrast inversion.

5. **Root Executable Synchronization (`StudyPulse.exe`):**
   - Updated `app.py:get_asset_path()` to prioritize `studypulse.html` adjacent to `sys.executable` so live disk edits are immediately reflected in frozen builds.
   - Rebuilt `dist/StudyPulse.exe` via PyInstaller and overwritten root `g:\\ADHD app\\StudyPulse.exe` (18,367,270 bytes).
"""

with open('docs/logs.md', 'a', encoding='utf-8') as f:
    f.write(log_patch)

print("Updated docs/logs.md successfully.")
