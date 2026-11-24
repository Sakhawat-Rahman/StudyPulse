# StudyPulse: Complete Technical Manual & Product Specification (v3.2.17)

> **Document Version:** 3.2.17 (Production Release)  
> **Release Date:** November 2026  
> **Classification:** Comprehensive Technical, Architecture & Product Reference  
> **Platform Target:** Microsoft Windows 10/11 (64-bit) & Local Wi-Fi Mobile Companion  
> **Technology Stack:** Python 3.14 / PyWebView / Microsoft Edge WebView2 (Evergreen Chromium) / Win32 API / HTML5 / Tailwind CSS / Vanilla ES2022 / Ephemeral llama.cpp CPU Inference  

---

## 1. Executive Summary & Product Vision

**StudyPulse** is an advanced, local-first executive functioning companion, daily habit momentum system, and multi-exam readiness platform engineered specifically for neurodivergent learners, individuals with ADHD, and students managing demanding academic workloads.

### The Neurodivergent Challenge
Traditional task managers and productivity applications routinely fail users with ADHD due to three distinct neurological friction points:
1. **Task Paralysis (Initiation Deficit):** Large, ambiguous goals (e.g., *"Study Chemistry Midterm"*) trigger acute executive dysfunction and avoidance. Neurodivergent brains require atomic, non-threatening micro-steps (2 to 15 minutes) with explicit physical starter steps.
2. **Time Blindness & Working Memory Drift:** Inability to accurately estimate time horizons or preserve sequence order. Users require shortest-first task sequencing upfront so quick dopamine wins establish kinetic study momentum before tackling larger blocks.
3. **Sensory & Distraction Friction:** Intrusive thoughts, chores, and secondary ideas frequently derail active focus sessions. Without a frictionless parking lot, interrupting oneself to record a chore breaks deep flow state permanently.

### Core Architectural Pillars (Version 3.2.13)
- **Local-First & Ephemeral Neural Intelligence:** 0-RAM idle footprint utilizing ephemeral `llama-cli.exe` with quantized `SmolLM2-360M-Instruct-Q4_K_M.gguf`. Subprocess spins up on demand, parses complex requirements into shortest-upfront micro-steps, and terminates cleanly with zero lingering background memory.
- **Deterministic Natural Language Task Slicing:** Multi-exam conversational parser identifying multiple exams, staggered due dates, course codes, and multi-day study runways, complete with strict conversational noise stripping (`clean_exam_title`).
- **Mathematically True Habit Momentum:** Responsive SVG line histogram with subpixel anti-aliasing (`shape-rendering="geometricPrecision"`), dynamic geometry recalculation on resize via `ResizeObserver`, and automatic midnight rollover.
- **Strict 3-Mode Priority Standard:** Clear triage hierarchy restricted strictly to `Important`, `Normal`, and `Low`, eliminating decision fatigue.
- **Sensory-Optimized Carbon Obsidian Dark Mode:** True #0A0A0B and #161618 deep carbon surfaces, subtle 1px border highlights, high-contrast typography (#EAEAE6), and synchronized native Windows DWM Immersive Dark Mode.
- **Seamless Phone Companion:** Local LAN companion (`http://192.168.1.x:8765`) featuring instant QR code pairing, two-way live synchronization, and an RFC 5545 iCalendar live feed URL.
- **High-Fidelity Studio Audio Deck (Patch 3.2.13):** Dynamic HSL jewel-tone color extraction playbar, true in-app song search with album context offset, widescreen studio expansion (`max-w-7xl`), 4-column responsive library grid, dedicated non-pausing `Library ▾` / `Library ▴` drawer button, studio view attention guidance (`@keyframes attentionBounce`), and animated flowing gradient on the sidebar Spotify toggle (`@keyframes gradientFlow`).

---

## 2. System Architecture & Technical Stack

```
+-------------------------------------------------------------------------+
|                       STUDYPULSE v3.2.13 ARCHITECTURE                   |
+-------------------------------------------------------------------------+
|                                                                         |
|  +------------------------+      +-----------------------------------+  |
|  |   Frontend UI Shell    |      |       Python Backend Core         |  |
|  | (Edge WebView2 Engine) | <==> |            (app.py)               |  |
|  | - Tailwind CSS         | JSON | - Win32 Window Engine (ctypes)    |  |
|  | - Vanilla ES2022       | RPC  | - LocalSyncServer (:8765)         |  |
|  | - Carbon Obsidian Dark |      | - SpotifyBridge (OAuth & Win32)   |  |
|  | - Responsive SVG Chart |      | - RFC 5545 iCal Engine            |  |
|  +------------------------+      +-----------------------------------+  |
|              ^                                     |                    |
|              | HTTP / WebSockets                   | Subprocess Exec    |
|              v                                     v                    |
|  +------------------------+      +-----------------------------------+  |
|  | Phone Companion View   |      |  Ephemeral Neural Engine (0 MB)   |  |
|  | (Local Wi-Fi Browser)  |      | - llama-cli.exe (C++ / Win32)     |  |
|  | - QR Code Auto-Connect |      | - SmolLM2-360M-Instruct-Q4_K_M    |  |
|  | - Touch-Optimized Rail |      | - Spawn on demand, exit on JSON   |  |
|  +------------------------+      +-----------------------------------+  |
+-------------------------------------------------------------------------+
```

### Component Breakdown
1. **Frontend Presentation (`studypulse.html`):** Single-page application rendered inside Microsoft Edge WebView2 Evergreen runtime. Styled using utility-first Tailwind CSS classes and custom CSS custom properties. Zero external runtime dependencies.
2. **Desktop Container & Native Bridge (`app.py`):** Built with Python 3.14 and `pywebview`. Exposes a thread-safe bi-directional JS API bridge (`save_app_state`, `slice_task_ai`, `spotify_control`, `toggle_widget_mode`, `set_native_theme`, `toggle_fullscreen`).
3. **Win32 Windowing & DWM Integration:** Direct Win32 API calls via `ctypes` (`dwmapi.dll`, `user32.dll`) providing frameless borderless window movement, non-blocking edge resizing, immersive dark window frame attributes (`DWMWA_USE_IMMERSIVE_DARK_MODE`), and multi-monitor work area clamping.
4. **Local Sync Server (`LocalSyncServer` on `:8765`):** Embedded multi-threaded HTTP server enabling phone companion mode over local Wi-Fi, serving state sync (`/api/state`), live RFC 5545 calendar feeds (`/calendar.ics`), and companion AI slicing (`/api/ai/slice`).
5. **Ephemeral Neural Engine (`models/`):** Quantized `SmolLM2-360M-Instruct-Q4_K_M.gguf` paired with precompiled `llama-cli.exe`. Executes via `subprocess.run` with `CREATE_NO_WINDOW`, capturing structured JSON and releasing 100% of CPU/RAM resources immediately upon completion.
6. **Spotify Desktop Audio Engine (`SpotifyBridge` in `app.py`):** Hybrid integration combining Spotify Web API (OAuth 2.0 PKCE) and targeted Win32 `WM_APPCOMMAND` / media key dispatches exclusively to Spotify, preventing leakage to YouTube, Discord, or VLC.

---

## 3. Comprehensive Featureset Specifications

### 3.1 AI Study Copilot & Conversational Multi-Exam Slicing Engine
The core intelligence engine converts messy, conversational human study prompts into structured, multi-day preparation roadmaps.
- **Conversational Multi-Exam Decomposition:** When presented with combined prompts (e.g., *"I have a math exam this Friday and I also have a CSC live exam on November 28 and the cse theory exam on November 15"*), the parser identifies distinct clauses separated by conversational conjunctions (`and`, semicolons, periods) and extracts each exam independently.
- **Conversational Phrase Stripping (`clean_exam_title`):** Cleans leading phrases (*"I have a"*, *"I also have"*, *"there is an"*, *"my"*) while preserving academic codes (`CSE`, `CSC`, `MAT`, `PHY`, `EEE`, `BIO`, `CHEM`) and milestone types (`Mid`, `Final`, `Quiz`, `Lab`).
- **Timezone-Safe Date Computation (`formatLocalDate`):** Calculates relative weekdays and calendar dates using strictly local date methods (`getFullYear()`, `getMonth() + 1`, `getDate()`), entirely preventing UTC offset boundary shifts from altering dates in Asian/European timezones.
- **Shortest-Upfront Micro-Task Sequencing:** Generates 3 to 4 varied micro-tasks per exam milestone (10m formula review, 15m syntax check, 20m problem set, 25m mock simulation), guaranteeing atomic starter steps.

### 3.2 Strict 3-Mode Priority Standard
To eliminate cognitive friction and ambiguous task triage, StudyPulse enforces strictly three priority modes across all storage, UI badges, and parsers:
- **IMPORTANT:** High-stakes exams, imminent deadlines, or critical reviews. Styled with high-contrast amber/gold borders and glowing dot accents.
- **NORMAL:** Standard balanced study sessions, regular coursework, and default milestones. Styled with muted zinc badges.
- **LOW:** Optional readings, minor reviews, or secondary exercises. Styled with subtle ghost badges.
- *Migration Guarantee:* Deprecated legacy priorities (such as `urgent` or `medium`) are automatically coerced during state hydration into `important` and `normal`.

### 3.3 Carbon & Obsidian Dark Mode
Designed in accordance with the *Carbon Obsidian* sensory specification:
- **Color Tokens:** Background: `#0A0A0B` (Canvas), `#161618` (Glass Shell), `#1C1C1F` (Cards & Modals). Text: `#EAEAE6` (High contrast primary), `#A1A1AA` (Muted labels). Borders: `rgba(255, 255, 255, 0.08)`.
- **DWM Native Titlebar Sync:** Synchronizes Windows titlebar chrome via `DwmSetWindowAttribute(hwnd, 20, 1)`.
- **Text Selection Visibility:** High-visibility text selection highlight (`::selection { background: #3f3f46; color: #ffffff; }`).
- **Zero-Flicker Bootstrapping:** Reads `localStorage` theme state immediately prior to DOM rendering, preventing white flash on boot.

### 3.4 Distraction Parking Lot ("Park Thought")
- Accessible globally via **Ctrl + Space** or the top titlebar button.
- Dedicated mental decluttering drawer to capture intrusive ADHD thoughts (*"Pay electricity bill"*, *"Check laundry"*) without derailing flow.
- Features one-click conversion of any parked thought into an actionable study milestone or queue item.

### 3.5 Ironclad Daily Rituals & Consistency Analytics
- **Dynamic Timeframes:** Toggle between 7-Day (7D), 30-Day (30D), and 90-Day (90D) historical tracking horizons.
- **Mathematically True SVG Line Histogram:** Dynamically computes 1:1 pixel coordinates within SVG viewBox. Configured with `shape-rendering="geometricPrecision"` to render perfectly round data points with zero oval distortion.
- **ResizeObserver Geometry Engine:** Automatically monitors card dimensions and re-renders SVG coordinates on window maximization, restore, or display scaling.
- **Quick Lazy Day Logging:** Provides 20%, 30%, 50%, and 70% whole-day progress buttons for quick logging on high-fatigue days.
- **Midnight Rollover Engine:** Evaluates calendar date transitions automatically; snapshots completed percentages to `habitHistory` and resets checkboxes for a fresh start.

### 3.6 Dedicated Focus Timer Studio & Widescreen Workspace
- **Widescreen Viewport Architecture:** Widened container constraint to `max-w-5xl xl:max-w-6xl 2xl:max-w-7xl mx-auto w-full`, providing balanced aesthetic framing on 1080p, 1440p, and 4K widescreen monitors.
- **Circular SVG Countdown Visualization:** High-contrast countdown display with animated progress stroke.
- **Session Length Presets:** 15m Sprint, 25m Pomodoro, 45m Deep Work, 60m Block.
- **Midpoint Awareness Chime:** Optional acoustic checkpoint chime to assist users with time blindness.

### 3.7 Integrated Spotify Hardware Audio Deck, Pastel Cover Polarity & In-App Search (v3.2.15)
StudyPulse includes a complete in-app Spotify console and persistent audio experience engineered specifically for uninterrupted deep focus:
- **Complementary Velvet-Slate Deck Surface & Cohesive Glass Elevation (Patch 3.2.15):** Rendered in deep `#141418` / `#18181E` with subtle white border highlights and soft glassmorphic elevation (`box-shadow: 0 10px 28px -6px rgba(0, 0, 0, 0.22), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset`), creating a tactile hardware deck feel that pops cleanly without aggressive drop shadow artifacts.
- **White, Cream & Pastel Cover Contrast Polarity (`.spotify-light-cover`, Patch 3.2.15):** Automatically samples 32x32 cover art for high-key covers (`avgLum > 0.60` or `lightPixelRatio > 0.45`). Instead of forcing dark muddy clamping, renders a Luminous Pearl / Pastel Mesh Gradient (`0.76..0.93` lightness, `0.05..0.42` saturation) and activates `.spotify-light-cover` contrast polarity:
  - Deep Obsidian (`#09090B`) bold titles with zero text shadow.
  - Crisp charcoal (`rgba(15, 15, 20, 0.75)`) subtitles.
  - Solid Jet Black (`#09090B`) primary play/pause buttons with pure white (`#FFFFFF`) SVG icons inside.
  - Solid Jet Black seekbar fill, thumb, and volume sliders.
  - Subtle dark glass pills (`rgba(0, 0, 0, 0.08)`) for timestamps, badges, and library toggles.
- **Universal Text Entity Formatter (`formatTrackString`, Patch 3.2.15):** Automatically decodes raw HTML entities (`&#039;` -> `'`, `&amp;` -> `&`, `&quot;` -> `"`) and assigns text via `.textContent`, permanently preventing scrambled strings like `Teacher&#039;s Pet`.
- **Sidebar Nav Toggle Polarity (Patch 3.2.15):** Purged all stray rings from `#nav-spotify-btn` when inactive; when active, seamlessly matches native app toggles (`bg-ink-950 text-white` in Light Mode, `#EAEAE6` in Dark Mode).
- **Dedicated Library Expand / Collapse Button (`Library ▾` / `Library ▴`):** Replaces redundant power toggles with an expand/collapse drawer button (`#inbuilt-spotify-power-btn`). Toggling the library drawer never halts or pauses background music streaming.
- **Responsive 4-Column Playlist Grid:** Formats personal playlists into a clean horizontal media tile grid (`grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4`) bounded by a max-height scroll viewport (`max-h-[580px] overflow-y-auto`), cutting vertical height by over 50%.
- **True 12-Bin Hue-Clustered Color Engine (Patch 3.2.14):** `applyAlbumArtGradient(imgUrl)` samples cover art onto a 32x32 offscreen `<canvas>`, converts to HSL, and groups vibrant pixels into 12 hue buckets (`Math.floor(h / 30) % 12`). Completely eliminates cross-hue muddy averaging (e.g. bright yellow + sky blue no longer mixes into dark muddy olive), preserving faithful high saturation (`s: 0.68..0.92`) and radiant proportional brightness (`l: 0.26..0.42`) so bright yellow stays golden-yellow, pink stays rose, and blue stays cobalt blue. Overlaid with subtle `.spotify-vibrant-text` text readability shadow.
- **3-State Sidebar Status Dot & Idle Gradient Reset (Patch 3.2.14):** The `#nav-spotify-dot` indicator on the left sidebar navigation button displays:
  - *Red Dot (`#EF4444`):* Spotify disconnected.
  - *Yellow Dot (`#FACC15`):* Connected, player paused.
  - *Green Dot Pulsating (`#22C55E`):* Connected and actively streaming music.
  When paused or disconnected, dynamic album gradients are stripped from all surfaces, reverting to clean default surfaces (`#141418` / monochrome obsidian).
- **Dual-Mode Floating Mini-Player & 175px Magnetic Snap Preview (Patch 3.2.14):**
  - *Renamed Header:* Updated to crisp `"Spotify"` title with dedicated mode toggle `#floating-spotify-compact-toggle-btn` (`⧉`).
  - *Standard Pill Mode:* Generous 360px horizontal pill with vinyl art, full metadata, click-to-seek progress scrubber, and transport row.
  - *Compressed Mini-Player Mode:* 176px compact card featuring a square 156x156px rounded cover art with an interactive 4px progress seekbar embedded along the bottom edge supporting direct click-to-seek, and compact transport buttons below.
  - *175px Magnetic Snap Preview:* Corner snap pull distance increased to 175px with `#spotify-snap-ghost` displaying a glassy blurry landing zone (`backdrop-filter: blur(18px) saturate(1.4)`, dashed white border) matching the active player dimensions.
  - *Default Mini Style Preference:* Users can configure their preferred default mini-player style (`Standard Pill` vs `Compressed Mini`) in **Settings -> Preferences**.
- **Waking Day 3px Horizon Bar Off by Default (Patch 3.2.14):** Defaults to off (`showHorizonBar = false`) with container hidden by default and automatic one-time migration (`state._horizonDefaultMigratedV3214`).
- **High-Contrast Dark Mode Play Buttons (Patch 3.2.14):** Solves dark-on-dark contrast where global `.bg-white` rules obscured play buttons in search results and playlist cards; all search track and playlist play buttons are forced to pure solid white (`#FFFFFF`) background with jet-black (`#000000`) icons and text in both light and dark modes.

### 3.8 Multi-View Workspace Modes
- **Full Dashboard Mode:** Complete multi-card layout displaying study readiness, queue, habits, upcoming tests, and AI copilot.
- **Desktop Widget Mode:** Pinned compact 440px borderless strip. Stays visible alongside textbooks or coding IDEs with native Win32 window movement.
- **Single-Task Anti-Paralysis Focus Mode:** Single-task isolation mode that hides all other UI elements, presenting strictly the next active micro-step with high-contrast velvet-slate surface (`#1E1E24`), bold white title, amber priority tag, and prominent action buttons.

### 3.9 Mobile Companion Mode & Responsive Architecture
- Access StudyPulse from any mobile browser on the same Wi-Fi network at `http://192.168.1.x:8765`.
- **Clean Mobile Header Cluster:** Intuitive top-bar layout grouping Logo, Quick 2-Way Sync, Study Calendar, AI Slicer, and Theme Toggle.
- **PC Version Sync Button Suppression:** The circling-arrow sync button is strictly hidden on the PC desktop app (`#nav-sync-btn { display: none !important; }`), ensuring zero redundant clutter on PC while remaining accessible on mobile.
- **Sidebar Rail Visual Spacing:** On desktop, a 65px vertical gap and centered divider line isolate the Phone Link button (`#open-sync-btn`) from the Action & Theme toggle cluster (`#open-new-goal-btn` and `#theme-toggle-nav-btn`), establishing clean visual grouping.

---

## 4. Quality Assurance, Chaos Testing & Bug Audit Record

StudyPulse is validated using an automated multi-suite test harness running through headless Microsoft Edge Chromium WebView2:
- `tests/test_library_and_search_play.py`: Validates library expand drawer, studio attention bounce, flowing ambient gradient, and search track playback.
- `tests/test_wide_console_layout.py`: Validates widescreen layout (`max-w-7xl`), 4-column playlist grid, seekbar scrubbing width, and DOM hygiene.
- `tests/test_contrast_and_layout_fixes.py`: Validates dark mode contrast shields, pure white play buttons, luminous seekbars, and right-column layout.
- `tests/test_spotify_console_overhaul.py`: Validates complementary velvet-slate surface, corner bleed elimination, and in-dashboard search display.
- `tests/test_live_interactions.py`: Validates view switching, deck expand/collapse, modal close buttons, and seekbar sync.
- `tests/verify_backend_live.py`: Validates backend instantiation, token storage, HTTP sync server, and Web API endpoints.
- `tests/test_precision_upgrades.py`: Validates 12-bin hue-clustered gradients, 3-state status dot, dual-mode compressed mini-player, 175px magnetic snap ghost preview, default style preference, and dark mode play contrast.
- `tests/test_light_cover_and_text_fixes.py`: Validates proportional color sampling for high-key covers, light cover contrast polarity (`.spotify-light-cover`), text entity decoding (`Teacher's Pet`), and sidebar toggle active/inactive polarity.

### Complete Bug Audit Record (BUG-001 through BUG-057 / Patches 3.2.1 through 3.2.15)

| Issue ID | Subsystem | Severity | Description & Root Cause | Resolution Status |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | NLP Slicer | CRITICAL | Single 180m monolithic subtask output in neural mode. | **FIXED** - Enforced 3-4 varied micro-tasks (5m-30m). |
| **BUG-002** | Ephemeral LLM | HIGH | Hallucinated year 2023 on prompts without explicit years. | **FIXED** - Added year-suppression regex & prompt rules. |
| **BUG-003** | Habit Engine | HIGH | Past dates generated when exams scheduled within 1-2 days. | **FIXED** - Clamped study dates to `max(today, d)`. |
| **BUG-004** | Calendar / NLP | HIGH | Date parsing failed on multi-exam prompts with dates first. | **FIXED** - Added Format B dual-regex date parser. |
| **BUG-005** | Habit Engine | HIGH | Midnight rollover wiped historical data on multiday gap. | **FIXED** - Added chronological gap interpolation loop. |
| **BUG-006** | SVG Histogram | MEDIUM | SVG curve clipped at 0% and 100% boundary limits. | **FIXED** - Added `padY` vertical safety margin. |
| **BUG-007** | UI / Dark Mode | MEDIUM | Legacy priorities caused undefined badge styling. | **FIXED** - Standardized strictly to 3 modes. |
| **BUG-008** | Calendar / ICS | HIGH | Unescaped semicolons broke RFC 5545 iCal parser. | **FIXED** - Implemented RFC 5545 text escaping. |
| **BUG-009** | Sync / Server | HIGH | Synchronous webhook dispatch hung UI during timeout. | **FIXED** - Wrapped dispatch in daemon thread. |
| **BUG-010** | Sync / Server | CRITICAL | Race condition in concurrent state saves corrupted JSON. | **FIXED** - Added `threading.Lock` across all file I/O. |
| **BUG-011** | Win32 Window | HIGH | Maximized window covered Windows taskbar. | **FIXED** - Implemented `GetMonitorInfoW` work area clamping. |
| **BUG-012** | Win32 Window | MEDIUM | Widget repositioned off-screen on secondary monitor. | **FIXED** - Added multi-monitor coordinate clamping. |
| **BUG-013** | UI / Dark Mode | HIGH | Text selection invisible in Carbon Obsidian dark mode. | **FIXED** - Added explicit `::selection` CSS rules. |
| **BUG-014** | UI / Dark Mode | MEDIUM | Duplicate theme toggles confused users. | **FIXED** - Consolidated to single left sidebar rail toggle. |
| **BUG-015** | Win32 Window | MEDIUM | Resize handles visible while maximized. | **FIXED** - Added `body.is-maximized .resize-handle { display: none }`. |
| **BUG-016** | Habit Engine | MEDIUM | Partial lazy logging buttons duplicated in daily routine. | **FIXED** - Removed duplicate lazy logging section. |
| **BUG-017** | UI / Layout | LOW | Navigation buttons lacked visual breathing room. | **FIXED** - Added distinct spacing between nav and actions. |
| **BUG-018** | UI / Dark Mode | LOW | Checkbox circles in dark mode had insufficient contrast. | **FIXED** - Added defined whiteness borders (rgba 0.48). |
| **BUG-019** | NLP Slicer | HIGH | Conversational multi-exam prompt generated monolithic plan. | **FIXED** - Enhanced multi-clause sentence splitting. |
| **BUG-020** | Date Boundary | MEDIUM | Out-of-bounds calendar days (Nov 31) caused crash. | **FIXED** - Added month day range clamping (`monthrange`). |
| **BUG-021** | UI / Layout | LOW | Standalone action cluster lacked complementary styling. | **FIXED** - Added inverted high-visibility action buttons. |
| **BUG-022** | NLP Slicer | HIGH | Conversational filler words corrupted exam milestone titles. | **FIXED** - Implemented `clean_exam_title()` across Python & JS. |
| **BUG-023** | UI / Script | CRITICAL | Missing closing brace halted script parsing on app launch. | **FIXED** - Balanced bracket hierarchy in `studypulse.html`. |
| **BUG-024** | Calendar / Date | HIGH | `toISOString()` caused 1-day date shift in UTC+ timezones. | **FIXED** - Implemented timezone-safe `formatLocalDate()`. |
| **BUG-025** | SVG Histogram | MEDIUM | Duplicate pulsing circle created moving ghost halo on chart. | **FIXED** - Removed outer circle; added `ResizeObserver`. |
| **BUG-026** | Mobile Layout | MEDIUM | Mobile phone sync button floated detached across header. | **FIXED** - Grouped Logo, Sync, and Calendar in flex cluster. |
| **BUG-027** | UI / Desktop | LOW | Redundant sync button visible on PC; link button lacked space. | **FIXED** - Hidden sync on PC; added 65px divider gap. |
| **BUG-028** | Spotify Auth | MEDIUM | External popup spawned for Spotify login. | **FIXED** - Integrated in-app browser authorization with PKCE. |
| **BUG-029** | Single-Task UI | HIGH | Single-Task mode close button click swallowed by card stack. | **FIXED** - Enforced explicit z-indexing and pointer-event targets. |
| **BUG-030** | Mini-Player | MEDIUM | Floating player hidden during view navigation. | **FIXED** - Synchronized player visibility across dashboard & calendar. |
| **BUG-031** | Single-Task UI | HIGH | Close button missing top-right anchor, ReferenceError on exit. | **FIXED** - Moved `✕` inside header flex, declared global handler. |
| **BUG-032** | Spotify Auth | HIGH | Port mismatch (Bottle 42001 vs Sync 8765) caused 404 on login. | **FIXED** - Normalized API base URL via dynamic port detection. |
| **BUG-033** | Mini-Player | MEDIUM | Duplicate event listeners caused double-firing toggle. | **FIXED** - Consolidated listeners to single idempotent handler. |
| **BUG-034** | Focus Studio | LOW | Residual hardcoded "Deep Focus" placeholders in studio. | **FIXED** - Purged placeholders in favor of dynamic user playlists. |
| **BUG-035** | Spotify Embed | HIGH | `open.spotify.com refused to connect` (anti-clickjacking). | **FIXED** - Switched from iframes to pure Web API + native bridge. |
| **BUG-036** | Spotify Audio | HIGH | 30-second preview limitations in iframe audio player. | **FIXED** - Implemented full-fidelity native playback via SpotifyBridge. |
| **BUG-037** | Single-Task UI | MEDIUM | Close button unresponsive on certain display scale factors. | **FIXED** - Added 32x32px hit area and unified escape listener. |
| **BUG-038** | Spotify Client | LOW | Manual Spotify Client ID entry required on clean installs. | **FIXED** - Preloaded production Client ID with user override support. |
| **BUG-039** | UI / Core | CRITICAL | Uncaught syntax error broke all click handlers globally. | **FIXED** - Restored missing bracket pairings and validated AST. |
| **BUG-040** | WebView2 Cache| HIGH | Stale JavaScript retained in WebView2 persistent disk cache. | **FIXED** - Added automated cache clearing and cache-busting headers. |
| **BUG-041** | Win32 Media | HIGH | Media keys leaked globally to YouTube/VLC during playback. | **FIXED** - Implemented targeted `WM_APPCOMMAND` sent only to Spotify. |
| **BUG-042** | Spotify Library| MEDIUM | Playlists displayed "0 tracks" and blank artwork. | **FIXED** - Added fallback image resolution and dynamic track count read. |
| **BUG-043** | Seekbar | HIGH | Seekbar reset to 0:00 every 3 seconds during status poll. | **FIXED** - Added local progress preservation ticker and click scrub. |
| **BUG-044** | Spotify UI | MEDIUM | Player ON/OFF toggle confusing when Spotify already active. | **FIXED** - Replaced with `Library ▾` / `Library ▴` drawer button. |
| **BUG-045** | Focus Studio | MEDIUM | Clicking nav toggle while in studio opened mini-player & scrolled. | **FIXED** - Suppressed mini-player in studio; added attention bounce. |
| **BUG-046** | Mini-Player | LOW | Static toggle button lacked visual indication of playing state. | **FIXED** - Added flowing animated jewel-tone gradient (`gradientFlow`). |
| **BUG-047** | In-App Search | HIGH | Clicking play on search track failed to play audio. | **FIXED** - Resolved album context offset (`context_uri` + `offset`). |
| **BUG-048** | Dark Mode UI | MEDIUM | Seekbars, waveforms, and pause buttons dark in obsidian mode. | **FIXED** - Applied pure white `#FFFFFF` contrast shields and jet-black icons. |

---

## 5. Win32 Hardware Window Engine Reference

StudyPulse delivers a custom frameless windowing experience on Windows 10 and 11 via direct Win32 API calls (`ctypes`):
- **Immersive Dark Frame Synchronization:** Calls `DwmSetWindowAttribute` with `DWMWA_USE_IMMERSIVE_DARK_MODE` (attribute ID 20), ensuring window borders match the active theme.
- **DPI-Aware Multi-Monitor Work Area Clamping:** Reads `MONITORINFO` via `GetMonitorInfoW` to determine exact `rcWork` bounds. Prevents window borders from overlapping the taskbar or spawning off-screen on secondary monitors.
- **Window Corner Rounding:** On Windows 11 (Build 22000+), calls `DwmSetWindowAttribute` with `DWMWA_WINDOW_CORNER_PREFERENCE` (attribute ID 33) set to `DWMWCP_ROUND` (value 2).
- **Smooth Frameless Resizing:** Transparent Win32 hit-test resize borders (`.resize-handle`) positioned on all four edges and corners for smooth cursor-based resizing.

---

## 6. Technical Data Schemas & API Contracts

### 6.1 State Schema (`studypulse_state.json`)
```json
{
  "goals": [
    {
      "id": "goal-1794080865495-0",
      "title": "Math Exam",
      "category": "exam",
      "dueDate": "2026-11-13",
      "priority": "important",
      "details": "I have a math exam this Friday",
      "subtasks": [
        {
          "id": "sub-1794080865495-0-1",
          "title": "Review Math Exam core syntax, rules & diagrams",
          "mins": 15,
          "priority": "important",
          "date": "2026-11-09",
          "time": "10:00 AM",
          "slotLabel": "Nov 09  -  10:00 AM",
          "completed": false
        }
      ]
    }
  ],
  "activeLayout": "default",
  "habitHistory": {
    "2026-11-08": {
      "overallPct": 70,
      "habits": { "habit-walk": 100, "habit-namaj": 100 }
    }
  },
  "brainDump": [],
  "settings": {
    "aiEngine": "neural",
    "halfwayChime": true,
    "showEnergyFilter": true
  }
}
```

### 6.2 REST Endpoints (`LocalSyncServer :8765`)
- `GET /api/state`: Retrieves the current application state JSON.
- `POST /api/state`: Ingests an updated state payload with thread-safe file lock synchronization.
- `GET /api/spotify/status`: Returns active Spotify Connect player state, track, artist, album art, duration, and progress.
- `POST /api/spotify/control`: Dispatches targeted transport actions (`play`, `pause`, `play_uri`, `seek`, `volume`).
- `GET /api/spotify/playlists`: Returns user's saved Spotify playlists with real cover images and track counts.
- `GET /api/spotify/search`: Performs true in-app catalog search returning playable tracks with album context and playlists.
- `GET /calendar.ics`: Generates and serves a live RFC 5545 iCalendar feed with CRLF line endings.
- `POST /api/ai/slice`: Executes ephemeral neural or deterministic NLP slicing on behalf of mobile companions.

---

## 7. File Manifest & Distribution Verification

- **Executable:** [`StudyPulse.exe`](file:///g:/ADHD%20app/StudyPulse.exe) (18,356,268 bytes standalone binary, bundled with icon and HTML).
- **Core Runtime:** [`app.py`](file:///g:/ADHD%20app/app.py) (Python container and Win32 bridge).
- **Interface Shell:** [`studypulse.html`](file:///g:/ADHD%20app/studypulse.html) (Complete UI, styles, and client logic).
- **Neural Engine Subsystem:** `models/llama-cli.exe` and `models/SmolLM2-360M-Instruct-Q4_K_M.gguf`.
- **Icon Resource:** `studypulse.ico` (Multi-resolution 16x16 to 256x256 icon).
- **Automated QA Test Suite:** `tests/test_library_and_search_play.py`, `tests/test_wide_console_layout.py`, `tests/test_contrast_and_layout_fixes.py`, `tests/test_spotify_console_overhaul.py`, `tests/test_live_interactions.py`, `tests/verify_backend_live.py`.
- **Audit Documentation:** [`docs/logs.md`](file:///g:/ADHD%20app/docs/logs.md) (Chronological record of BUG-001 through BUG-048).
- **Product Manuals:** [`docs/StudyPulse_Comprehensive_Manual.md`](file:///g:/ADHD%20app/docs/StudyPulse_Comprehensive_Manual.md) and [`docs/StudyPulse_Comprehensive_Manual.pdf`](file:///g:/ADHD%20app/docs/StudyPulse_Comprehensive_Manual.pdf).

---

## 8. Visual Interface Gallery & Application States

This section catalogs high-resolution visual evidence of all primary interfaces, workspace modes, and operational states across StudyPulse v3.2.13.

### Figure 6.1: Main Multi-Column Dashboard Overview — Clean Light Mode
![Figure 6.1: Main Multi-Column Dashboard Overview — Clean Light Mode](screenshots_live/fig6_1_dashboard_light.png)
*The primary daylight interface displaying the circular navigation rail, Study Readiness momentum gauge (22%), Upcoming Tests cards, Today's Study Queue with shortest-first sequencing, AI Study Copilot input bar, Ironclad Daily Rituals with 7D consistency histogram, and the bottom-left docked Spotify mini-player.*

---

### Figure 6.2: Main Multi-Column Dashboard Overview — Carbon Obsidian Dark Mode
![Figure 6.2: Main Multi-Column Dashboard Overview — Carbon Obsidian Dark Mode](screenshots_live/fig6_2_dashboard_dark.png)
*Nighttime sensory-friendly dark theme featuring true carbon obsidian background (#0A0A0B / #141416), subtle 1px border highlights (#27272A), high-contrast typography (#EAEAE6), priority badges, and zero-flicker DWM Immersive Dark Mode synchronization.*

---

### Figure 6.3: Dedicated Focus Timer Studio — Clean Light Mode
![Figure 6.3: Dedicated Focus Timer Studio — Clean Light Mode](screenshots_live/fig6_3_studio_light.png)
*Dedicated widescreen focus studio providing circular countdown display (25:00), sprint preset pills, start/reset controls, and the integrated Spotify Desktop-style audio strip featuring cover art, track info, centered transport controls, seekbar with dual timestamps, volume slider, and dedicated Library drawer toggle.*

---

### Figure 6.4: Dedicated Focus Timer Studio — Carbon Obsidian Dark Mode
![Figure 6.4: Dedicated Focus Timer Studio — Carbon Obsidian Dark Mode](screenshots_live/fig6_4_studio_dark.png)
*Distraction-free obsidian timer studio minimizing visual stimulus. Shows high-contrast minute readouts, ambient progress ring, pure white transport controls, and the sleek dark-mode Spotify audio strip with live seekbar and dynamic 4-column library drawer.*

---

### Figure 6.5: Monthly Study & Exam Calendar View — Clean Light Mode
![Figure 6.5: Monthly Study & Exam Calendar View — Clean Light Mode](screenshots_live/fig6_5_calendar_light.png)
*Comprehensive monthly academic calendar displaying upcoming exam milestones, daily prep sessions, and milestone status chips. Features instant month navigation, today jump button, and direct synchronization with the RFC 5545 iCalendar feed.*

---

### Figure 6.6: Monthly Study & Exam Calendar View — Carbon Obsidian Dark Mode
![Figure 6.6: Monthly Study & Exam Calendar View — Carbon Obsidian Dark Mode](screenshots_live/fig6_6_calendar_dark.png)
*Obsidian dark mode academic calendar with high-visibility dates, clear milestone dots, and exam badge indicators designed for long study sessions without ocular fatigue.*

---

### Figure 6.7a: Application Preferences & AI Telemetry Modal — Light Mode
![Figure 6.7a: Application Preferences & AI Telemetry Modal — Light Mode](screenshots_live/fig6_7a_settings_light.png)
*Comprehensive configuration modal providing live CPU ephemeral model testing, AI engine selection, feature toggles, and mini-player dock position selectors.*

---

### Figure 6.7b: Application Preferences & AI Telemetry Modal — Carbon Obsidian Dark Mode
![Figure 6.7b: Application Preferences & AI Telemetry Modal — Carbon Obsidian Dark Mode](screenshots_live/fig6_7b_settings_dark.png)
*Dark theme preferences interface allowing zero-glare customization of sensory pacing, notifications, midpoint acoustic chimes, and full JSON data backup/restore.*

---

### Figure 6.8a: Compact Desktop Widget View — Clean Light Mode
![Figure 6.8a: Compact Desktop Widget View — Clean Light Mode](screenshots_live/fig6_8a_widget_light.png)
*Ultra-compact pinned companion window (380px wide). Sits alongside coding IDEs, lecture videos, or browser windows with quick check-offs and integrated audio controls.*

---

### Figure 6.8b: Compact Desktop Widget View — Carbon Obsidian Dark Mode
![Figure 6.8b: Compact Desktop Widget View — Carbon Obsidian Dark Mode](screenshots_live/fig6_8b_widget_dark.png)
*Dark mode companion widget designed for unobtrusive multitasking with high contrast readability and minimal pixel footprint.*

---

### Figure 6.8c: Phone Companion Hub & Live QR Code Modal
![Figure 6.8c: Phone Companion Hub & Live QR Code Modal](screenshots_live/fig6_8c_phone_qr_dark.png)
*Two-way wireless companion hub. Generates a live QR code and local LAN URL (http://192.168.1.x:8765) for instant phone companion access, alongside one-click RFC 5545 iCalendar feed URL subscription for Apple Calendar, Google Calendar, and Outlook.*

| BUG-049 | Dark mode search track & playlist play buttons rendered dark charcoal with black text due to global `html.dark .bg-white` override | P1 | High | Enforced dedicated `#FFFFFF` background with `#000000` text & SVG fill via `.spotify-track-play-btn` and `.spotify-playlist-play-btn` |
| BUG-050 | Bright/multi-color album covers (e.g. yellow+blue) mixed into muddy olive green due to RGB averaging and 23% lightness clamping | P1 | High | Replaced RGB averaging with 12-bin hue clustering, isolating per-bucket averages and mapping lightness proportionally (0.26..0.42) |
| BUG-051 | Sidebar navigation Spotify button remained stuck in album art gradient when music was paused or disconnected | P2 | Medium | Implemented `resetSpotifyGradientToDefault()`, stripping gradient and reverting `#nav-spotify-btn` to monochrome and playbars to `#141418` |
| BUG-052 | Left sidebar Spotify indicator dot only supported 1 binary state and stayed hidden or static | P2 | Medium | Upgraded `#nav-spotify-dot` to 3 distinct states: Solid Red (disconnected), Solid Yellow (paused), Pulsating Green (actively playing) |
| BUG-053 | Mini-player lacked compact vertical mode and corner dragging was sluggish without visual snap feedback | P2 | Medium | Engineered Compressed Mini-Player (176px, 156x156 cover, embedded 4px seekbar) with 175px snap pull and `#spotify-snap-ghost` blurry preview |
| BUG-054 | White, cream, and soft pastel album covers turned into harsh dark teal and rust-orange gradients due to discarded light pixels | P1 | High | Implemented true proportional sampling (`avgLum`, `lightPixelRatio > 0.45`), pearl mesh gradients, and automatic `.spotify-light-cover` contrast polarity |
| BUG-055 | Track titles in mini-player and widget displayed raw HTML entities (`Teacher&#039;s Pet`) due to double-escaping into `.textContent` | P2 | Medium | Implemented universal `formatTrackString()` DOMParser decoder and plain `.textContent` DOM insertion across all track/artist surfaces |
| BUG-056 | Left sidebar Spotify navigation button displayed an unwanted dark ring outline even when the mini-player was inactive / closed | P2 | Medium | Purged inactive ring classes; standardized active state to `.bg-ink-950 text-white` (black in light mode, white in dark mode, matching all app toggles) |
| BUG-057 | Inbuilt console playbar and floating mini-player had overly aggressive, harsh drop shadows (`0 14px 32px -8px rgba(0,0,0,0.45)`) | P2 | Medium | Softened drop shadows to cohesive glassmorphic elevation (`0 10px 28px -6px rgba(0,0,0,0.22), 0 0 1px 1px rgba(255,255,255,0.08) inset`) |
| BUG-058 | Mini-player close button (`✕`) failed to physically hide element due to inline `style.display = 'flex'` overriding `.hidden` | P1 | High | Enforced `fp.style.display = 'none'`, added `#floating-spotify-mini-player.hidden { display: none !important; }`, updated nav state, and persisted `state.showSpotifyMini = false` |
| BUG-059 | Clicking Settings (`#brand-home-btn`) in compact mode unexpectedly exited widget mode and flung the native Win32 window to maximized | P1 | High | Removed `toggleWidgetMode(false)` from brand mark; rendered `#settings-modal` in responsive compact formfactor (`.widget-settings-compact`, max-w-350px, compact tabs) |
| BUG-060 | Floating mini-player did not scale down during compact mode, overflowing the 380px window boundary at `left: 88px; width: 360px` | P1 | High | Added `body.widget-mode-active` rules, clamped standard pill to `calc(100vw - 32px)`, centered compressed album mode (`176px; left: 50%; translateX(-50%)`), and decoupled width from position transitions |
| BUG-061 | Application typography lacked unified studio-grade hierarchy and numeric tabular alignment on countdown timers, causing horizontal character jitter during active sprints | P2 | Medium | Implemented 3-tier typography system (`Plus Jakarta Sans` display headings, `Inter` body with OpenType features `cv02`, `cv03`, `cv04`, `cv11`, `ss01`, and `JetBrains Mono` tabular nums on timer clock, telemetry, seekbars, task chips, due dates, and uppercase micro headers) |
| BUG-062 | Predominantly white, cream, and soft pastel album covers rendered with dark saturated muddy olive/teal gradients and low text contrast | P1 | High | Implemented proportional pixel sampling (`avgLum > 0.58 || lightPixelRatio > 0.42`), high-key lightness clamping (`0.78..0.94`) with natural pastel saturation (`0.04..0.42`), pearl mesh gradient, ambient blur filter `saturate(1.06) brightness(1.02) contrast(0.96)`, and automatic `.spotify-light-cover` contrast polarity (Obsidian titles, Charcoal subtitles, Jet Black play button with pure white icon, dark glass pills) |
| BUG-063 | Left sidebar Spotify button had unwanted border/ring stroke in active and inactive states | P2 | Medium | Stripped all border/ring strokes (`border: none !important; outline: none !important; box-shadow: none !important;`); styled inactive state with tactile dimming (`opacity: 0.48; transform: scale(0.95); filter: saturate(0.7);`) and active state with full clarity |
| BUG-064 | Mini-player header contained redundant "PLAYING" badge that forced flex shrinkage of the Spotify title into "S.." | P2 | Medium | Completely deleted `#floating-spotify-live-badge` from DOM and enforced `white-space: nowrap !important; overflow: visible !important; flex-shrink: 0 !important; font-weight: 700 !important;` on `#floating-spotify-title-label` |
| BUG-065 | Mini-player close button (`✕`) was unresponsive in compressed mode due to drag listener event hijacking | P1 | High | Added explicit inline `onmousedown="event.stopPropagation();"` and `onclick="event.stopPropagation(); window.hideFloatingSpotifyPlayer && window.hideFloatingSpotifyPlayer();" style="position: relative; z-index: 50; pointer-events: auto; cursor: pointer;"` to `#floating-spotify-close-btn` with `pointer-events-none` on SVG, and added `e.target.closest('button, input, a, .no-drag')` early return in drag listener |
| BUG-066 | Mini-player dragging glitched and unresponsive to mouse button inputs due to document `mouseleave` and window `blur` aborts and native Windows tooltip interference | P1 | High | Engineered unified Pointer Capture engine (`setPointerCapture`), mouse fallbacks with window mouseup capture, `cursor: grab` feedback, and removed tooltip `title` attributes |
| BUG-067 | Hovering over Spotify nav button or play buttons in white/light mode caused icons to vanish (black-on-black or white-on-white) | P1 | High | Replaced inline icon fills with `fill: currentColor !important; color: inherit !important;`, added dedicated `:hover` rules enforcing white icon on active black button in light mode, and high contrast under `.spotify-light-cover` |
| BUG-068 | Track titles, artist labels, and playlist names displayed raw HTML entities (`Teacher&#039;s Pet`) | P2 | Medium | Upgraded `formatTrackString()` to decode decimal entities (`&#(\d+);`), hex entities, quotes, apostrophes, and integrated `import html; html.unescape()` across all Spotify API endpoints in `app.py` |
| BUG-069 | Stale PyInstaller executable running bundled assets rather than live disk changes | P1 | High | Updated `app.py:get_asset_path()` to prioritize `studypulse.html` beside `sys.executable`, rebuilt `dist/StudyPulse.exe` via PyInstaller, and synchronized root `StudyPulse.exe` |
| BUG-070 | Nav Spotify button gradient mismatched album art on dark/grayscale covers due to hardcoded purple fallback and 250% zoom animation | P1 | High | Stored computed album gradient in window.currentSpotifyGradient, assigned exact gradient to #nav-spotify-btn, and removed 250% zoom animation |
| BUG-071 | Sidebar Spotify button was excessively greyed out (opacity: 0.48, saturate: 0.7) when mini-player was inactive | P2 | Medium | Recalibrated inactive state to tactile opacity: 0.85, removed desaturation filter, and added crisp 1px border stroke |
| BUG-072 | Spotify nav button displayed gradient even when mini-player was closed/greyed out or song was paused | P1 | High | Enforced strict const shouldShowGradient = isVisible && isConnected && isPlaying; conditional gate, purging gradient and resetting to monochrome whenever closed or paused |
| BUG-073 | Left navigation rail Spotify toggle icon was invisible in dark mode when active due to white-on-white SVG path fill override | P1 | High | Explicitly targeted html.dark #nav-spotify-btn.nav-spotify-active svg, svg *, svg path with ill: #09090B !important, removed conflicting 	ext-white class, and bound dynamic theme contrast re-evaluation in setDarkMode() |
