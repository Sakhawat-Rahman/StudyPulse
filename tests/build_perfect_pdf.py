import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#71717a"))
        
        # Header (Skip on Cover Page)
        if self._pageNumber > 1:
            self.drawString(40, 755, "StudyPulse v3.2.13 — Production Engineering & Visual Architecture Manual")
            self.drawRightString(572, 755, "Confidential / Internal Reference")
            self.setStrokeColor(colors.HexColor("#e4e4e7"))
            self.setLineWidth(0.5)
            self.line(40, 748, 572, 748)

        # Footer
        self.setStrokeColor(colors.HexColor("#e4e4e7"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)
        
        self.drawString(40, 30, "Carbon Obsidian Architecture • 0-RAM Ephemeral Engine • Win32 Windowing • Hardware Spotify Deck")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.restoreState()

def build_pdf(output_path, screenshots_dir):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Clean Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#09090b"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#52525b"),
        spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'H1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#09090b"),
        spaceBefore=11,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#18181b"),
        spaceBefore=9,
        spaceAfter=3,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.2,
        textColor=colors.HexColor("#27272a"),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=11.8,
        textColor=colors.HexColor("#27272a"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#3f3f46")
    )
    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#27272a")
    )
    td_code = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#09090b")
    )
    img_title_style = ParagraphStyle(
        'ImgTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#09090b"),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )
    img_caption_style = ParagraphStyle(
        'ImgCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#52525b"),
        spaceBefore=3,
        spaceAfter=8
    )
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # =========================================================================
    # COVER / HEADER BLOCK
    # =========================================================================
    story.append(Paragraph("StudyPulse v3.2.13", title_style))
    story.append(Paragraph("Production Architecture, Neurodivergent UX Systems & Complete Visual Interface Manual", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#09090b"), spaceBefore=0, spaceAfter=8))

    meta_table_data = [
        [
            Paragraph("<b>Classification:</b> Comprehensive Technical, Architecture & Product Reference", meta_style),
            Paragraph("<b>Target Operating System:</b> Microsoft Windows 10/11 (64-bit)", meta_style)
        ],
        [
            Paragraph("<b>Core Runtime:</b> Python 3.14 + PyWebView + Edge Chromium WebView2", meta_style),
            Paragraph("<b>Companion Platform:</b> Local Wi-Fi Web App (iOS / Android)", meta_style)
        ],
        [
            Paragraph("<b>Frontend Framework:</b> Vanilla ES2022 + Tailwind CSS (Zero Build)", meta_style),
            Paragraph("<b>Audio Subsystem:</b> Hardware Spotify Deck + Widescreen 4-Column Grid", meta_style)
        ],
        [
            Paragraph("<b>AI Intelligence:</b> Ephemeral llama.cpp SmolLM2-360M CPU Inference", meta_style),
            Paragraph("<b>Persistence & Integrity:</b> Thread-Safe Atomic JSON Disk I/O", meta_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[266, 266])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f4f4f5")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e4e4e7")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e4e4e7")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Executive Callout
    callout_data = [[
        Paragraph("<b>EXECUTIVE MISSION STATEMENT:</b> StudyPulse is an executive-function augmentation system engineered to dissolve ADHD analysis paralysis, study fatigue, and working-memory drop-off through tactile micro-tasking, intelligent syllabus decomposition, dynamic jewel-tone audio immersion, and atomic local synchronization.", meta_style)
    ]]
    callout_table = Table(callout_data, colWidths=[532])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fafafa")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#09090b")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 1: EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Neurodivergent Product Vision", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#09090b"), spaceBefore=2, spaceAfter=6))
    
    story.append(Paragraph("Traditional productivity software fundamentally fails neurodivergent learners due to four clinical friction points:", body_style))
    story.append(Paragraph("• <b>Task Initiation Paralysis:</b> Ambiguous academic goals (<i>'Study for Calculus II Midterm'</i>) overwhelm working memory, triggering dopamine withdrawal and acute avoidance.", bullet_style))
    story.append(Paragraph("• <b>Cognitive & Sensory Fatigue:</b> Cluttered interfaces with neon badges and confetti streaks induce sensory saturation rather than calm focus.", bullet_style))
    story.append(Paragraph("• <b>All-or-Nothing Shame Spirals:</b> Rigid binary habit trackers cause abandonment when a routine is only partially completed (e.g. 5,000 of 7,000 steps).", bullet_style))
    story.append(Paragraph("• <b>Intrusive Distraction Derailment:</b> Unrelated urgent thoughts break hyperfocus when acted upon, or clog working memory when suppressed.", bullet_style))

    story.append(Paragraph("Core Architectural Pillars of StudyPulse v3.2.13:", h2_style))
    story.append(Paragraph("• <b>Distraction-Free Monochrome Obsidian & Pure Light:</b> Ultra-clean obsidian canvas (<code>#0A0A0B</code>) and clean light mode with zero neon tints or childish gimmicks.", bullet_style))
    story.append(Paragraph("• <b>Integrated Hardware Spotify Console (v3.2.13):</b> Velvet-slate surface architecture, 4-column responsive library shelf, dedicated non-pausing Library drawer button, and dynamic HSL jewel-tone gradients.", bullet_style))
    story.append(Paragraph("• <b>0-RAM Ephemeral AI Engine:</b> On-demand CPU neural inference via <code>llama-cli.exe</code> that terminates immediately after outputting JSON.", bullet_style))
    story.append(Paragraph("• <b>Distraction Parking Lot ('Park Thought'):</b> Instant external working memory capture accessible globally via <code>Ctrl+Space</code>.", bullet_style))
    story.append(Paragraph("• <b>Proportional Habit Weighting:</b> Flexible daily routine logging (20%, 30%, 50%, 70%) with mathematically 1:1 round SVG consistency charts.", bullet_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 2: SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("2. System Architecture & Engineering Stack", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#09090b"), spaceBefore=2, spaceAfter=6))

    arch_data = [
        [Paragraph("Subsystem Layer", th_style), Paragraph("Technologies Used", th_style), Paragraph("Architectural Responsibilities", th_style)],
        [
            Paragraph("<b>Native Windows OS Layer</b>", td_style),
            Paragraph("Win32 API (ctypes)<br/>Microsoft Edge WebView2<br/>Windows Shell AppID", td_style),
            Paragraph("Hardware-accelerated window positioning, borderless dragging, profile directory isolation, taskbar process binding, and PE multi-resolution icon injection.", td_style)
        ],
        [
            Paragraph("<b>Spotify Subsystem</b>", td_style),
            Paragraph("Spotify Web API<br/>Win32 WM_APPCOMMAND<br/>OAuth 2.0 PKCE", td_style),
            Paragraph("Hardware deck console, in-app catalog search with album context offset, dynamic HSL jewel-tone gradient engine, flowing ambient toggle, and 4-column playlist grid.", td_style)
        ],
        [
            Paragraph("<b>Python Backend Core<br/>(app.py)</b>", td_style),
            Paragraph("Python 3.14<br/>PyWebView Bridge<br/>Threading HTTPServer", td_style),
            Paragraph("Process concurrency management, native Win32 window geometry controller, DesktopBridge IPC exposed via <code>window.pywebview.api</code>, and local Wi-Fi sync server (:8765).", td_style)
        ],
        [
            Paragraph("<b>Reactive Frontend Core<br/>(studypulse.html)</b>", td_style),
            Paragraph("Vanilla ES2022<br/>Tailwind CSS (Zero-Build)<br/>Web Audio API Chimes", td_style),
            Paragraph("Single-file reactive client, heuristic NLP task slicing engine, interactive 7-column calendar, widescreen Focus Studio, and dual storage fallback bus.", td_style)
        ],
        [
            Paragraph("<b>Mobile LAN Companion</b>", td_style),
            Paragraph("Mobile Web (Safari / Chrome)<br/>Vector QR Pairing<br/>REST Sync Protocol", td_style),
            Paragraph("Zero-install mobile web controller operating over local subnet (<code>http://192.168.x.x:8765</code>) with bidirectional atomic JSON synchronization.", td_style)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[110, 130, 292])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#09090b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 3: SUBSYSTEM SPECIFICATIONS
    # =========================================================================
    story.append(Paragraph("3. Subsystem Deep-Dives & Featureset Specifications (v3.2.13)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#09090b"), spaceBefore=2, spaceAfter=6))

    story.append(Paragraph("3.1 Integrated Spotify Audio Deck & In-App Search Engine (Patch 3.2.13)", h2_style))
    story.append(Paragraph("StudyPulse v3.2.13 delivers a comprehensive, zero-preview audio ecosystem designed for deep concentration without cognitive interruptions:", body_style))
    story.append(Paragraph("• <b>Hardware Deck Surface Architecture:</b> Designed with complementary velvet-slate surfaces (<code>#141418</code> background, <code>1px solid rgba(255,255,255,0.12)</code> border) that pop with crisp visual authority against both Light and Dark surrounding cards.", bullet_style))
    story.append(Paragraph("• <b>Dedicated Library Drawer Toggle (<code>Library ▾ / Library ▴</code>):</b> Replaced the old power toggle with a non-pausing expand/collapse button. Expanding or collapsing the playlist library drawer never halts or interrupts active audio streaming.", bullet_style))
    story.append(Paragraph("• <b>4-Column Responsive Playlist Grid:</b> Upgraded personal library rendering into an expansive 4-column horizontal media tile grid (<code>grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4</code>) with <code>max-h-[580px]</code> scroll bounding, cutting vertical height by over 50%.", bullet_style))
    story.append(Paragraph("• <b>True In-App Search with Context Offset:</b> Solved the Windows desktop Spotify Connect idle receiver quirk by resolving the song's album context (<code>album_uri</code>) and playing via <code>{\"context_uri\": album_uri, \"offset\": {\"uri\": track_uri}}</code>. Songs found in search (e.g. <i>cold/mess</i>) play instantly inside the app.", bullet_style))
    story.append(Paragraph("• <b>Dynamic HSL Jewel-Tone Gradient Engine:</b> <code>applyAlbumArtGradient()</code> samples cover art onto a 32x32 canvas, filters muddy pixels, and renders 100% opaque rich jewel-tone gradients over a dark base with zero white bleed-through.", bullet_style))
    story.append(Paragraph("• <b>Focus Studio Attention Pulse (<code>@keyframes attentionBounce</code>):</b> Suppresses the floating mini-player inside Focus Studio. Clicking the nav Spotify button while in Studio triggers a 0.68s scale and luminous glow pulse on the playbar to direct attention there.", bullet_style))
    story.append(Paragraph("• <b>Flowing Ambient Gradient (<code>@keyframes gradientFlow</code>):</b> Features a 3.5s smooth moving gradient on the sidebar Spotify toggle matching current song cover hues during active playback, reverting to clean monochrome on pause.", bullet_style))
    story.append(Paragraph("• <b>Dark Mode Contrast Shields:</b> Play/pause buttons are 100% pure white (<code>#FFFFFF</code>), seekbar fills and waveforms are luminous white, and pause icons are jet black (<code>#000000</code>) for maximum optical contrast.", bullet_style))

    story.append(Paragraph("3.2 Widescreen Focus Studio & Single-Task Anti-Paralysis Mode", h2_style))
    story.append(Paragraph("• <b>Widescreen Studio Expansion:</b> Expanded viewport constraint to <code>max-w-5xl xl:max-w-6xl 2xl:max-w-7xl</code>, eliminating awkward 600px+ blank side margins on modern widescreen monitors.", bullet_style))
    story.append(Paragraph("• <b>Single-Task Isolation Card:</b> Completely redesigned with deep velvet-slate surface (<code>#1E1E24</code>), prominent bold white title (<code>#FFFFFF</code>), amber priority tag (<code>#FCD34D</code>), and high-contrast action buttons.", bullet_style))

    story.append(Paragraph("3.3 AI Study Copilot & Multi-Exam Slicing Engine", h2_style))
    story.append(Paragraph("Supports dual-engine task decomposition (Deterministic NLP and 0-RAM Ephemeral SmolLM2-360M). Automatically deconstructs multi-exam syllabi, resolves relative weekdays, pairs respective exam dates, schedules 4-day advance reverse prep sessions, clamps prep dates safely to today or future dates, and enforces calendar month boundaries.", body_style))

    story.append(Paragraph("3.4 Strict 3-Mode Priority Standard & Habit Momentum", h2_style))
    story.append(Paragraph("Enforces strictly <b>`Important`</b> (warm amber pill), <b>`Normal`</b> (crisp zinc pill), and <b>`Low`</b> (muted dark pill). Accommodates partial daily effort through fractional quick-log buttons (20%, 30%, 50%, 70%) and dynamic 1:1 round SVG histograms.", body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 4: QA AUDIT SUMMARY
    # =========================================================================
    story.append(Paragraph("4. Quality Assurance & Chaos Testing Audit (BUG-001 through BUG-048)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#09090b"), spaceBefore=2, spaceAfter=6))
    story.append(Paragraph("Prior to production release, StudyPulse v3.2.13 underwent comprehensive multi-suite regression testing across headless Microsoft Edge Chromium WebView2, resolving all reported defects documented in `logs.md`:", body_style))

    qa_summary_data = [
        [Paragraph("Bug / Patch", th_style), Paragraph("Subsystem", th_style), Paragraph("Severity", th_style), Paragraph("Root Cause & Resolution Summary", th_style)],
        [
            Paragraph("BUG-041", td_code), Paragraph("Win32 Media", td_style), Paragraph("HIGH", td_style),
            Paragraph("Media keys leaked globally to YouTube/VLC during playback; implemented targeted <code>WM_APPCOMMAND</code> exclusively for Spotify.", td_style)
        ],
        [
            Paragraph("BUG-043", td_code), Paragraph("Seekbar Engine", td_style), Paragraph("HIGH", td_style),
            Paragraph("Seekbar continually reset back to 0:00 every 3s poll; added local progress preservation ticker and proportional click scrub.", td_style)
        ],
        [
            Paragraph("BUG-044", td_code), Paragraph("Spotify UI", td_style), Paragraph("MEDIUM", td_style),
            Paragraph("Player ON/OFF toggle paused music unexpectedly; replaced with dedicated <code>Library ▾ / Library ▴</code> drawer button.", td_style)
        ],
        [
            Paragraph("BUG-045", td_code), Paragraph("Focus Studio", td_style), Paragraph("MEDIUM", td_style),
            Paragraph("Clicking nav toggle while in studio auto-expanded deck and scrolled; suppressed mini-player and added attention bounce animation.", td_style)
        ],
        [
            Paragraph("BUG-046", td_code), Paragraph("Mini-Player", td_style), Paragraph("LOW", td_style),
            Paragraph("Toggle button lacked visual feedback; added flowing animated jewel-tone gradient (<code>gradientFlow</code>) active when music plays.", td_style)
        ],
        [
            Paragraph("BUG-047", td_code), Paragraph("In-App Search", td_style), Paragraph("HIGH", td_style),
            Paragraph("Search track click failed to play audio; resolved album context offset (<code>context_uri + offset</code>) to reliably create playback queue.", td_style)
        ],
        [
            Paragraph("BUG-048", td_code), Paragraph("Dark Mode UI", td_style), Paragraph("MEDIUM", td_style),
            Paragraph("Seekbars and pause buttons invisible in dark mode; enforced pure white (<code>#FFFFFF</code>) contrast shields and jet-black icons.", td_style)
        ],
        [
            Paragraph("PATCH 3.2.12", td_code), Paragraph("Widescreen UI", td_style), Paragraph("ENHANCE", td_style),
            Paragraph("Expanded Focus Studio to <code>max-w-7xl</code> and upgraded playlist grids to responsive 4-column layout.", td_style)
        ]
    ]
    qa_table = Table(qa_summary_data, colWidths=[65, 65, 55, 347])
    qa_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#09090b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(qa_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 5: MANIFEST
    # =========================================================================
    story.append(Paragraph("5. File Manifest & Distribution Verification", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#09090b"), spaceBefore=2, spaceAfter=6))

    manifest_data = [
        [Paragraph("Artifact Name", th_style), Paragraph("Format & Type", th_style), Paragraph("Role & Production Status", th_style)],
        [
            Paragraph("<b>StudyPulse.exe</b>", td_style),
            Paragraph("PE32+ Executable (18,356,268 bytes)", td_style),
            Paragraph("Primary standalone Windows executable compiled with PyInstaller, embedded Python 3.14, and WebView2 hooks.", td_style)
        ],
        [
            Paragraph("<b>app.py</b>", td_style),
            Paragraph("Python Backend Source", td_style),
            Paragraph("Houses Win32 window manager, DesktopBridge IPC, SpotifyBridge audio engine, and local sync server (:8765).", td_style)
        ],
        [
            Paragraph("<b>studypulse.html</b>", td_style),
            Paragraph("Single-File HTML5/JS Core", td_style),
            Paragraph("Production client application with Carbon Obsidian styling, multi-exam NLP, dynamic SVG charts, and Spotify deck.", td_style)
        ],
        [
            Paragraph("<b>docs/logs.md</b>", td_style),
            Paragraph("Markdown Audit Trail", td_style),
            Paragraph("Chronological audit log tracking BUG-001 through BUG-048 and all 13 production release patches.", td_style)
        ],
        [
            Paragraph("<b>docs/Manual (.md / .pdf)</b>", td_style),
            Paragraph("Product Documentation", td_style),
            Paragraph("Complete architectural and user manuals (StudyPulse_Comprehensive_Manual.md and .pdf).", td_style)
        ]
    ]
    manifest_table = Table(manifest_data, colWidths=[120, 120, 292])
    manifest_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#09090b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(manifest_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 6: VISUAL INTERFACE SHOWCASE & VERIFIED GALLERY
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("6. Visual Interface Showcase & UI Architecture Gallery", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#09090b"), spaceBefore=2, spaceAfter=8))
    story.append(Paragraph("The following verified photographic gallery presents StudyPulse v3.2.13 across all primary views, operational states, and color themes (Clean Light Mode and Carbon Obsidian Dark Mode), captured freshly and directly from production runtime:", body_style))
    story.append(Spacer(1, 6))

    # Gallery 1: Main Dashboard (Light Mode)
    story.append(Paragraph("6.1 Main Multi-Column Dashboard — Clean Light Mode", img_title_style))
    img_p1 = os.path.join(screenshots_dir, "fig6_1_dashboard_light.png")
    if os.path.exists(img_p1):
        story.append(RLImage(img_p1, width=532, height=299.25))
        story.append(Paragraph("<b>Figure 6.1:</b> StudyPulse v3.2.13 Full Dashboard in Clean Light Mode. Demonstrates daylight typography, momentum readiness gauge (22%), 7D consistency histogram, shortest-first study queue, upcoming exams cards, and bottom-left docked Spotify mini-player.", img_caption_style))

    # Gallery 2: Main Dashboard (Dark Mode)
    story.append(Paragraph("6.2 Main Multi-Column Dashboard — Carbon Obsidian Dark Mode", img_title_style))
    img_p2 = os.path.join(screenshots_dir, "fig6_2_dashboard_dark.png")
    if os.path.exists(img_p2):
        story.append(RLImage(img_p2, width=532, height=299.25))
        story.append(Paragraph("<b>Figure 6.2:</b> StudyPulse v3.2.13 Full Dashboard in Carbon Obsidian Dark Mode. Sensory-friendly #0A0A0B canvas with high-contrast priority tags, 1px border highlights, pure white contrast shields, and DWM Immersive Dark Mode synchronization.", img_caption_style))

    # Gallery 3: Focus Timer Studio (Light & Dark)
    story.append(PageBreak())
    story.append(Paragraph("6.3 Focus Timer Studio Architecture — Clean Light & Obsidian Dark", img_title_style))
    img_p3 = os.path.join(screenshots_dir, "fig6_3_studio_light.png")
    img_p4 = os.path.join(screenshots_dir, "fig6_4_studio_dark.png")
    if os.path.exists(img_p3) and os.path.exists(img_p4):
        studio_table_data = [
            [RLImage(img_p3, width=260, height=146.25), RLImage(img_p4, width=260, height=146.25)],
            [
                Paragraph("<b>Figure 6.3:</b> Studio View (Clean Light)", img_caption_style),
                Paragraph("<b>Figure 6.4:</b> Studio View (Obsidian Dark)", img_caption_style)
            ]
        ]
        studio_table = Table(studio_table_data, colWidths=[266, 266])
        studio_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(studio_table)

    # Gallery 4: Calendar Views (Light & Dark)
    story.append(Spacer(1, 6))
    story.append(Paragraph("6.4 Monthly Academic & Exam Calendar Grid — Light & Dark Modes", img_title_style))
    img_p5 = os.path.join(screenshots_dir, "fig6_5_calendar_light.png")
    img_p6 = os.path.join(screenshots_dir, "fig6_6_calendar_dark.png")
    if os.path.exists(img_p5) and os.path.exists(img_p6):
        cal_table_data = [
            [RLImage(img_p5, width=260, height=146.25), RLImage(img_p6, width=260, height=146.25)],
            [
                Paragraph("<b>Figure 6.5:</b> Calendar Grid (Clean Light)", img_caption_style),
                Paragraph("<b>Figure 6.6:</b> Calendar Grid (Obsidian Dark)", img_caption_style)
            ]
        ]
        cal_table = Table(cal_table_data, colWidths=[266, 266])
        cal_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(cal_table)

    # Gallery 5: Preferences & Telemetry Modals
    story.append(PageBreak())
    story.append(Paragraph("6.5 Application Preferences & Telemetry Modals — Light & Dark", img_title_style))
    img_p7a = os.path.join(screenshots_dir, "fig6_7a_settings_light.png")
    img_p7b = os.path.join(screenshots_dir, "fig6_7b_settings_dark.png")
    if os.path.exists(img_p7a) and os.path.exists(img_p7b):
        pref_table_data = [
            [RLImage(img_p7a, width=260, height=172.5), RLImage(img_p7b, width=260, height=172.5)],
            [
                Paragraph("<b>Figure 6.7a:</b> Settings Modal (Clean Light)", img_caption_style),
                Paragraph("<b>Figure 6.7b:</b> Settings Modal (Obsidian Dark)", img_caption_style)
            ]
        ]
        pref_table = Table(pref_table_data, colWidths=[266, 266])
        pref_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(pref_table)

    # Gallery 6: Compact Widget & Phone Companion
    story.append(Spacer(1, 6))
    story.append(Paragraph("6.6 Compact Desktop Widget View & Phone Companion Integration", img_title_style))
    story.append(Paragraph("Side-by-side presentation of the ultra-compact 380px Desktop Widget Mode (pinned alongside textbooks or IDEs) in Clean Light Mode (left) and Obsidian Dark Mode (center), alongside the Phone Companion & QR Integration modal (right):", body_style))

    img_p8_light = os.path.join(screenshots_dir, "fig6_8a_widget_light.png")
    img_p8_dark = os.path.join(screenshots_dir, "fig6_8b_widget_dark.png")
    img_p8_qr = os.path.join(screenshots_dir, "fig6_8c_phone_qr_dark.png")

    if os.path.exists(img_p8_light) and os.path.exists(img_p8_dark):
        w_widget = 125
        h_widget = 125 * (720 / 380)

        w_qr = 230
        h_qr = 230 * (850 / 1280)

        widget_table_data = [
            [
                RLImage(img_p8_light, width=w_widget, height=h_widget),
                RLImage(img_p8_dark, width=w_widget, height=h_widget),
                RLImage(img_p8_qr, width=w_qr, height=h_qr) if os.path.exists(img_p8_qr) else Paragraph("Phone QR", td_style)
            ],
            [
                Paragraph("<b>Figure 6.8a:</b> Compact Widget (Light)", img_caption_style),
                Paragraph("<b>Figure 6.8b:</b> Compact Widget (Dark)", img_caption_style),
                Paragraph("<b>Figure 6.8c:</b> Phone Companion & QR Modal", img_caption_style)
            ]
        ]
        widget_table = Table(widget_table_data, colWidths=[140, 140, 240])
        widget_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(widget_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated StudyPulse v3.2.13 PDF with Verified Showcase at: {output_path}")

if __name__ == "__main__":
    out_dir = r"G:\ADHD app\docs"
    screenshots = r"G:\ADHD app\screenshots_live"
    out_file = os.path.join(out_dir, "StudyPulse_Comprehensive_Manual.pdf")
    build_pdf(out_file, screenshots)
