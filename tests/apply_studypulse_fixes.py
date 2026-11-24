# -*- coding: utf-8 -*-
"""
Script to apply all fixes directly into studypulse.html:
1. formatTrackString HTML entity decoding
2. Unified Pointer + Mouse Drag Engine with Pointer Capture
3. Zero-Vanishing Hover Rules for nav-spotify-btn and Play buttons
4. Cursor and tooltip cleanup on floating mini-player header
5. Remove hardcoded black inline styles on play icons
"""
import re

with open('studypulse.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update formatTrackString
old_format = """    function formatTrackString(str) {
      if (!str) return '';
      let s = String(str);
      try {
        const doc = new DOMParser().parseFromString(s, 'text/html');
        s = doc.body.textContent || s;
      } catch (e) {}
      return s
        .replace(/&#0*39;/g, "'")
        .replace(/&apos;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>');
    }"""

new_format = """    function formatTrackString(str) {
      if (!str) return '';
      let s = String(str);
      s = s.replace(/&#(\\d+);/g, (m, dec) => String.fromCharCode(dec))
           .replace(/&#x([0-9a-f]+);/gi, (m, hex) => String.fromCharCode(parseInt(hex, 16)))
           .replace(/&quot;/g, '"')
           .replace(/&#0*39;/g, "'")
           .replace(/&apos;/g, "'")
           .replace(/&amp;/g, '&')
           .replace(/&lt;/g, '<')
           .replace(/&gt;/g, '>');
      try {
        const doc = new DOMParser().parseFromString(s, 'text/html');
        s = doc.body.textContent || s;
      } catch (e) {}
      return s;
    }"""

if old_format in content:
    content = content.replace(old_format, new_format)
    print("Replaced formatTrackString successfully.")
else:
    print("WARNING: old_format not found exactly, attempting regex replacement.")
    pattern = r'function formatTrackString\(str\)\s*\{[\s\S]*?return s[\s\S]*?;\s*\}'
    content = re.sub(pattern, new_format.strip(), content)
    print("Applied regex replacement for formatTrackString.")

# 2. Update Drag Header in HTML (remove tooltip and cursor-move, set style="cursor: grab;")
old_drag_header = '<div id="floating-spotify-drag-header" class="flex items-center justify-between gap-1.5 border-b border-white/10 pb-2 cursor-move select-none" title="Drag to reposition (magnetically snaps to corners)">'
new_drag_header = '<div id="floating-spotify-drag-header" class="flex items-center justify-between gap-1.5 border-b border-white/10 pb-2 select-none" style="cursor: grab;">'
if old_drag_header in content:
    content = content.replace(old_drag_header, new_drag_header)
    print("Replaced floating-spotify-drag-header tag successfully.")
else:
    print("WARNING: old_drag_header not found exactly, checking variant...")
    content = re.sub(
        r'<div id="floating-spotify-drag-header"[^>]*>',
        new_drag_header,
        content
    )
    print("Substituted drag header tag.")

# 3. Clean up inline styles on play icons & text
content = content.replace(
    '<svg id="inbuilt-spotify-play-icon" style="fill: #000000 !important; color: #000000 !important;" class="w-4 h-4 ml-0.5" viewBox="0 0 24 24" fill="currentColor">',
    '<svg id="inbuilt-spotify-play-icon" style="fill: currentColor !important; color: inherit !important;" class="w-4 h-4 ml-0.5" viewBox="0 0 24 24" fill="currentColor">'
)
content = content.replace(
    '<svg id="inbuilt-spotify-pause-icon" style="fill: #000000 !important; color: #000000 !important;" class="hidden w-4 h-4" viewBox="0 0 24 24" fill="currentColor">',
    '<svg id="inbuilt-spotify-pause-icon" style="fill: currentColor !important; color: inherit !important;" class="hidden w-4 h-4" viewBox="0 0 24 24" fill="currentColor">'
)
content = content.replace(
    '<svg id="floating-spotify-play-icon" style="fill: #000000 !important; color: #000000 !important;" class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">',
    '<svg id="floating-spotify-play-icon" style="fill: currentColor !important; color: inherit !important;" class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">'
)
content = content.replace(
    '<svg id="floating-spotify-pause-icon" style="fill: #000000 !important; color: #000000 !important;" class="hidden w-3 h-3" viewBox="0 0 24 24" fill="currentColor">',
    '<svg id="floating-spotify-pause-icon" style="fill: currentColor !important; color: inherit !important;" class="hidden w-3 h-3" viewBox="0 0 24 24" fill="currentColor">'
)
content = content.replace(
    '<span id="floating-spotify-play-text" style="color: #000000 !important; font-weight: 700 !important;">Play</span>',
    '<span id="floating-spotify-play-text" style="color: inherit !important; font-weight: 700 !important;">Play</span>'
)
content = content.replace(
    '<svg id="floating-spotify-compact-play-icon" style="fill: #000000 !important; color: #000000 !important;" class="w-3.5 h-3.5 ml-0.5" viewBox="0 0 24 24" fill="currentColor">',
    '<svg id="floating-spotify-compact-play-icon" style="fill: currentColor !important; color: inherit !important;" class="w-3.5 h-3.5 ml-0.5" viewBox="0 0 24 24" fill="currentColor">'
)
content = content.replace(
    '<svg id="floating-spotify-compact-pause-icon" style="fill: #000000 !important; color: #000000 !important;" class="hidden w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">',
    '<svg id="floating-spotify-compact-pause-icon" style="fill: currentColor !important; color: inherit !important;" class="hidden w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">'
)

# 4. Update CSS for cursor feedback on mini-player
old_cursor_css = """    /* Draggable Mini-Player Cursor Feedback */
    #floating-spotify-mini-player {
      cursor: grab;
      user-select: none;
      -webkit-user-select: none;
    }
    #floating-spotify-mini-player.is-dragging {
      cursor: grabbing !important;
    }"""

new_cursor_css = """    /* Draggable Mini-Player Cursor Feedback */
    #floating-spotify-mini-player,
    #floating-spotify-drag-header {
      cursor: grab;
      user-select: none;
      -webkit-user-select: none;
    }
    #floating-spotify-mini-player.is-dragging,
    #floating-spotify-mini-player.is-dragging #floating-spotify-drag-header {
      cursor: grabbing !important;
    }"""

if old_cursor_css in content:
    content = content.replace(old_cursor_css, new_cursor_css)
    print("Updated cursor CSS.")

# 5. Overhaul Drag Engine in JS
drag_engine_old_regex = r'// Robust Drag Engine for Floating Mini-Player[\s\S]*?document\.addEventListener\(\'mouseleave\', endDrag\);\s*\}'

drag_engine_new = """// Robust Drag Engine for Floating Mini-Player (Unified Pointer Capture + Mouse Fallback)
    if (floatPlayer) {
      let isDragging = false, startX = 0, startY = 0, origLeft = 0, origTop = 0;
      let activePointerId = null;

      const isNonDraggableTarget = (target) => {
        return !!target.closest('button, input, a, select, [role="button"], #floating-spotify-seekbar-container, #floating-spotify-compact-seekbar-container, .spotify-mini-close-btn, .no-drag, [data-no-drag]');
      };

      const startDrag = (e) => {
        // Only primary left click / primary pointer
        if (e.button !== 0) return;
        if (isNonDraggableTarget(e.target)) return;

        isDragging = true;
        floatPlayer.classList.add('is-dragging');
        floatPlayer.style.transition = 'none';

        startX = e.clientX;
        startY = e.clientY;

        const rect = floatPlayer.getBoundingClientRect();
        origLeft = rect.left;
        origTop = rect.top;

        floatPlayer.style.left = origLeft + 'px';
        floatPlayer.style.top = origTop + 'px';
        floatPlayer.style.bottom = 'auto';
        floatPlayer.style.right = 'auto';

        if (e.pointerId !== undefined && floatPlayer.setPointerCapture) {
          activePointerId = e.pointerId;
          try {
            floatPlayer.setPointerCapture(e.pointerId);
          } catch(err) {}
        }

        document.body.classList.add('select-none');
        if (e.cancelable) e.preventDefault();
      };

      const moveDrag = (e) => {
        if (!isDragging) return;
        if (activePointerId !== null && e.pointerId !== undefined && e.pointerId !== activePointerId) return;

        // Failsafe: if buttons is explicitly 0 and mouse has moved at least 5px, end drag
        const distMoved = Math.hypot(e.clientX - startX, e.clientY - startY);
        if (e.buttons !== undefined && (e.buttons & 1) === 0 && distMoved > 4) {
          endDrag(e);
          return;
        }

        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        const pWidth = floatPlayer.offsetWidth || 350;
        const pHeight = floatPlayer.offsetHeight || 130;

        const curLeft = Math.max(8, Math.min(window.innerWidth - pWidth - 8, origLeft + dx));
        const curTop = Math.max(8, Math.min(window.innerHeight - pHeight - 8, origTop + dy));

        floatPlayer.style.left = curLeft + 'px';
        floatPlayer.style.top = curTop + 'px';

        // Corner magnetic snapping detection & Ghost Preview Box
        const distLeft = curLeft;
        const distTop = curTop;
        const distRight = window.innerWidth - (curLeft + pWidth);
        const distBottom = window.innerHeight - (curTop + pHeight);
        const SNAP_PULL = 140;

        const ghost = document.getElementById('spotify-snap-ghost');
        let snapCorner = null;

        if (distLeft < SNAP_PULL && distTop < SNAP_PULL) snapCorner = 'tl';
        else if (distRight < SNAP_PULL && distTop < SNAP_PULL) snapCorner = 'tr';
        else if (distLeft < SNAP_PULL && distBottom < SNAP_PULL) snapCorner = 'bl';
        else if (distRight < SNAP_PULL && distBottom < SNAP_PULL) snapCorner = 'br';

        if (snapCorner && ghost) {
          floatPlayer.classList.add('ring-2', 'ring-white/40');
          ghost.style.width = pWidth + 'px';
          ghost.style.height = pHeight + 'px';
          if (snapCorner === 'tl') {
            ghost.style.top = '64px';
            ghost.style.left = '88px';
          } else if (snapCorner === 'tr') {
            ghost.style.top = '64px';
            ghost.style.left = (window.innerWidth - pWidth - 24) + 'px';
          } else if (snapCorner === 'bl') {
            ghost.style.top = (window.innerHeight - pHeight - 24) + 'px';
            ghost.style.left = '88px';
          } else if (snapCorner === 'br') {
            ghost.style.top = (window.innerHeight - pHeight - 24) + 'px';
            ghost.style.left = (window.innerWidth - pWidth - 24) + 'px';
          }
          ghost.style.bottom = 'auto';
          ghost.style.right = 'auto';
          ghost.classList.remove('hidden');
        } else {
          floatPlayer.classList.remove('ring-2', 'ring-white/40');
          if (ghost) ghost.classList.add('hidden');
        }
      };

      const endDrag = (e) => {
        if (!isDragging) return;
        isDragging = false;

        if (activePointerId !== null && floatPlayer.releasePointerCapture) {
          try {
            if (floatPlayer.hasPointerCapture && floatPlayer.hasPointerCapture(activePointerId)) {
              floatPlayer.releasePointerCapture(activePointerId);
            }
          } catch(err) {}
          activePointerId = null;
        }

        document.body.classList.remove('select-none');
        floatPlayer.classList.remove('is-dragging', 'ring-2', 'ring-white/40');

        const ghostEl = document.getElementById('spotify-snap-ghost');
        if (ghostEl) ghostEl.classList.add('hidden');
        floatPlayer.style.transition = 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)';

        const rect = floatPlayer.getBoundingClientRect();
        const pWidth = floatPlayer.offsetWidth || 350;
        const pHeight = floatPlayer.offsetHeight || 130;
        const distLeft = rect.left;
        const distTop = rect.top;
        const distRight = window.innerWidth - (rect.left + pWidth);
        const distBottom = window.innerHeight - (rect.top + pHeight);
        const SNAP_THRESHOLD = 140;

        if (distLeft < SNAP_THRESHOLD && distTop < SNAP_THRESHOLD) {
          applyMiniDockPos('tl');
        } else if (distRight < SNAP_THRESHOLD && distTop < SNAP_THRESHOLD) {
          applyMiniDockPos('tr');
        } else if (distLeft < SNAP_THRESHOLD && distBottom < SNAP_THRESHOLD) {
          applyMiniDockPos('bl');
        } else if (distRight < SNAP_THRESHOLD && distBottom < SNAP_THRESHOLD) {
          applyMiniDockPos('br');
        } else {
          currentMiniDock.xRatio = rect.left / Math.max(1, (window.innerWidth - pWidth));
          currentMiniDock.yRatio = rect.top / Math.max(1, (window.innerHeight - pHeight));
          applyMiniDockPos('custom');
        }
      };

      // Native Pointer Events for rock-solid pointer capture
      floatPlayer.addEventListener('pointerdown', startDrag);
      floatPlayer.addEventListener('pointermove', moveDrag);
      floatPlayer.addEventListener('pointerup', endDrag);
      floatPlayer.addEventListener('pointercancel', endDrag);

      // Standard Mouse Events for headless test automation and older environments
      floatPlayer.addEventListener('mousedown', startDrag);
      document.addEventListener('mousemove', moveDrag);
      document.addEventListener('mouseup', endDrag);
      window.addEventListener('mouseup', endDrag);
    }"""

content = re.sub(drag_engine_old_regex, drag_engine_new, content)
print("Updated Drag Engine.")

with open('studypulse.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("studypulse.html updated successfully.")
