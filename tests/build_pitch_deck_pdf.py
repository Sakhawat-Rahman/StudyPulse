import os
import sys
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.pdfgen import canvas

class PitchDeckNumberedCanvas(canvas.Canvas):
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
            self.draw_slide_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, page_count):
        self.saveState()
        w, h = 792, 612 # landscape letter
        
        # Skip decorative header/footer on cover slide
        if self._pageNumber > 1:
            # Header line
            self.setStrokeColor(colors.HexColor("#27272a"))
            self.setLineWidth(0.75)
            self.line(36, h - 38, w - 36, h - 38)

            # Header micro-copy
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#10b981"))
            self.drawString(36, h - 30, "STUDYPULSE v3.2.20")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#71717a"))
            self.drawString(135, h - 30, "•   Cognitive-Ergonomic ADHD Study Workspace & Hardware Spotify Console")
            self.drawRightString(w - 36, h - 30, "OFFICIAL PITCH DECK & PRODUCT SHOWCASE")

            # Footer line
            self.setStrokeColor(colors.HexColor("#27272a"))
            self.setLineWidth(0.75)
            self.line(36, 32, w - 36, 32)

            # Footer copy
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#71717a"))
            self.drawString(36, 20, "Engineered for Neurodivergent Minds   •   Zero-Cloud Ephemeral AI   •   Win32 DWM Native Performance")
            
            page_str = f"Slide {self._pageNumber} of {page_count}"
            self.drawRightString(w - 36, 20, page_str)

        self.restoreState()

def build_pitch_deck():
    output_pdf = r"G:\ADHD app\docs\StudyPulse_Pitch_Deck_Showcase.pdf"
    screenshots_dir = r"G:\ADHD app\showcase_pitch_deck"
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    # 792 x 612 landscape letter
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Typography styles
    c_white = colors.HexColor("#FFFFFF")
    c_dark = colors.HexColor("#09090B")
    c_emerald = colors.HexColor("#10B981")
    c_zinc_400 = colors.HexColor("#A1A1AA")
    c_zinc_700 = colors.HexColor("#3F3F46")
    c_zinc_800 = colors.HexColor("#27272A")
    c_zinc_900 = colors.HexColor("#18181B")

    s_cover_tag = ParagraphStyle(
        'CoverTag', fontName='Helvetica-Bold', fontSize=10, leading=12,
        textColor=c_emerald, spaceAfter=8
    )
    s_cover_title = ParagraphStyle(
        'CoverTitle', fontName='Helvetica-Bold', fontSize=32, leading=38,
        textColor=c_white, spaceAfter=12
    )
    s_cover_sub = ParagraphStyle(
        'CoverSub', fontName='Helvetica', fontSize=14, leading=20,
        textColor=colors.HexColor("#D4D4D8"), spaceAfter=24
    )
    s_cover_pill = ParagraphStyle(
        'CoverPill', fontName='Helvetica-Bold', fontSize=8.5, leading=11,
        textColor=c_emerald, alignment=1
    )

    s_slide_tag = ParagraphStyle(
        'SlideTag', fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=c_emerald, spaceAfter=3
    )
    s_slide_title = ParagraphStyle(
        'SlideTitle', fontName='Helvetica-Bold', fontSize=16, leading=19,
        textColor=c_white, spaceAfter=4
    )
    s_slide_desc = ParagraphStyle(
        'SlideDesc', fontName='Helvetica', fontSize=9, leading=12,
        textColor=colors.HexColor("#D4D4D8"), spaceAfter=10
    )

    s_card_badge = ParagraphStyle(
        'CardBadge', fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.HexColor("#FACC15"), spaceAfter=2
    )
    s_card_title = ParagraphStyle(
        'CardTitle', fontName='Helvetica-Bold', fontSize=9, leading=11,
        textColor=c_white, spaceAfter=2
    )
    s_card_text = ParagraphStyle(
        'CardText', fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor("#A1A1AA")
    )

    story = []

    def get_image(filename, target_w, target_h):
        img_path = os.path.join(screenshots_dir, filename)
        if not os.path.exists(img_path):
            return Spacer(target_w, target_h)
        with Image.open(img_path) as im:
            orig_w, orig_h = im.size
        # Maintain aspect ratio
        ratio = min(target_w / orig_w, target_h / orig_h)
        final_w = orig_w * ratio
        final_h = orig_h * ratio
        return RLImage(img_path, width=final_w, height=final_h)

    # =========================================================================
    # SLIDE 1: COVER SLIDE
    # =========================================================================
    cover_box = [
        Paragraph("REVOLUTIONARY ADHD NEURO-ERGONOMICS", s_cover_tag),
        Paragraph("StudyPulse: The Cognitive Operating Workspace", s_cover_title),
        Paragraph(
            "Engineered from first principles for ADHD minds. Eliminates executive dysfunction, "
            "choice paralysis, and cognitive friction through zero-glare Obsidian architecture, "
            "atomic micro-task slicing, and native zero-latency hardware Spotify streaming.",
            s_cover_sub
        ),
        Spacer(1, 16)
    ]

    pills_data = [
        [
            Paragraph("🧠 ZERO WORKING MEMORY OVERLOAD", s_cover_pill),
            Paragraph("⚡ 1-THING ANTI-PARALYSIS", s_cover_pill),
            Paragraph("🎵 TRUE HARDWARE SPOTIFY DECK", s_cover_pill),
            Paragraph("🔒 100% PRIVATE LOCAL AI", s_cover_pill)
        ]
    ]
    pills_table = Table(pills_data, colWidths=[175, 175, 175, 175])
    pills_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#18181B")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    # Wrap in dark slide container
    cover_table = Table([[cover_box], [pills_table]], colWidths=[720])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#09090B")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
        ('TOPPADDING', (0,0), (-1,-1), 60),
        ('BOTTOMPADDING', (0,0), (-1,-1), 60),
        ('LEFTPADDING', (0,0), (-1,-1), 40),
        ('RIGHTPADDING', (0,0), (-1,-1), 40),
    ]))
    story.append(cover_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE CREATION HELPER
    # =========================================================================
    def add_single_showcase_slide(tag, title, desc, img_name, cards):
        """
        Standard landscape pitch slide:
        Top: Title & Description
        Center: High-res screenshot (width ~720, height ~330)
        Bottom: 3 key takeaway cards
        """
        slide_elements = []
        slide_elements.append(Paragraph(tag.upper(), s_slide_tag))
        slide_elements.append(Paragraph(title, s_slide_title))
        slide_elements.append(Paragraph(desc, s_slide_desc))

        # Screenshot container
        img_obj = get_image(img_name, 720, 325)
        img_table = Table([[img_obj]], colWidths=[720], rowHeights=[325])
        img_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#121215")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        slide_elements.append(img_table)
        slide_elements.append(Spacer(1, 8))

        # 3 Bottom Feature Highlight Cards
        card_cells = []
        for c in cards:
            c_p = [
                Paragraph(c[0].upper(), s_card_badge),
                Paragraph(c[1], s_card_title),
                Paragraph(c[2], s_card_text)
            ]
            card_cells.append(c_p)

        card_table = Table([card_cells], colWidths=[236, 236, 236])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#141417")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        slide_elements.append(card_table)

        # Container table for entire slide
        wrapper = Table([[slide_elements]], colWidths=[720])
        wrapper.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#09090B")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1C1C1F")),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ]))
        story.append(wrapper)
        story.append(PageBreak())

    def add_dual_showcase_slide(tag, title, desc, img1_name, title1, img2_name, title2, cards):
        """
        Side-by-side comparison slide (e.g. Light vs Dark, or Dual Widgets)
        """
        slide_elements = []
        slide_elements.append(Paragraph(tag.upper(), s_slide_tag))
        slide_elements.append(Paragraph(title, s_slide_title))
        slide_elements.append(Paragraph(desc, s_slide_desc))

        img1_obj = get_image(img1_name, 350, 325)
        img2_obj = get_image(img2_name, 350, 325)

        sub_header1 = Paragraph(f"<b>{title1}</b>", ParagraphStyle('SubH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_emerald, alignment=1))
        sub_header2 = Paragraph(f"<b>{title2}</b>", ParagraphStyle('SubH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_emerald, alignment=1))

        dual_table = Table([
            [sub_header1, sub_header2],
            [img1_obj, img2_obj]
        ], colWidths=[355, 355], rowHeights=[14, 315])
        dual_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#121215")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        slide_elements.append(dual_table)
        slide_elements.append(Spacer(1, 8))

        card_cells = []
        for c in cards:
            c_p = [
                Paragraph(c[0].upper(), s_card_badge),
                Paragraph(c[1], s_card_title),
                Paragraph(c[2], s_card_text)
            ]
            card_cells.append(c_p)

        card_table = Table([card_cells], colWidths=[236, 236, 236])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#141417")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        slide_elements.append(card_table)

        wrapper = Table([[slide_elements]], colWidths=[720])
        wrapper.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#09090B")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1C1C1F")),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ]))
        story.append(wrapper)
        story.append(PageBreak())

    # =========================================================================
    # SLIDE 2: COMMAND DASHBOARD (LIGHT THEME)
    # =========================================================================
    add_single_showcase_slide(
        tag="Executive Dashboard • Clean Light Mode",
        title="High-Legibility Daytime Command Center",
        desc="Designed for study environments with natural ambient light. High-contrast typography with Plus Jakarta Sans headings and OpenType Inter body copy eliminates reading fatigue.",
        img_name="01_dashboard_command_center_light.png",
        cards=[
            ("Cognitive Hierarchy", "Readiness & Sprint Queue", "Visual exam momentum dial (16%) paired with a prioritized queue showing exact time commitments upfront."),
            ("AI Copilot Prompt", "Natural Language Slicing", "Inline prompt bar converts messy exam syllabus requirements into structured, ordered micro-steps in seconds."),
            ("Ironclad Rituals", "Non-Negotiable Habit Grid", "Daily routines with a 7-day sparkline momentum curve prevents dopamine crashes and tracks streak consistency.")
        ]
    )

    # =========================================================================
    # SLIDE 3: COMMAND DASHBOARD (DARK THEME)
    # =========================================================================
    add_single_showcase_slide(
        tag="Executive Dashboard • Carbon Obsidian Dark Mode",
        title="Zero-Glare Sensory Pacing for Deep Night Sessions",
        desc="Pure Carbon Obsidian palette (#09090B / #141416) with OLED true-black depth. Calibrated to prevent sensory overload and late-night visual hyper-stimulation.",
        img_name="02_dashboard_command_center_dark.png",
        cards=[
            ("Sensory Protection", "OLED Deep Black Depth", "Subtle borders (rgba 255,255,255,0.08) maintain clean card definition without blinding luminescent glare."),
            ("Visual Telemetry", "Tabular JetBrains Mono", "Countdown numbers and exam badges use tabular figures to stop horizontal layout jitter during active time tracking."),
            ("Sidebar Clarity", "3-State Tactical Indicator", "Left navigation rail provides one-click access with clear red/yellow/green hardware Spotify connection dots.")
        ]
    )

    # =========================================================================
    # SLIDE 3B: AI STUDY COPILOT MULTI-EXAM SLICER
    # =========================================================================
    add_single_showcase_slide(
        tag="AI Study Copilot • Multi-Exam Topic Slicer",
        title="Natural Language Multi-Exam & Micro-Task Decomposition",
        desc="Converts complex multi-date exam prompts ('I have CSE 215 Exams on 17th, 20th, 25th november on arrys, pointers and struct respectively') into coordinated milestones with concrete study drills.",
        img_name="03_ai_study_copilot_multi_breakdown.png",
        cards=[
            ("Multi-Milestone Split", "Coordinated Exam Dates", "Automatically isolates CSE 215: Arrays (Nov 17), Pointers (Nov 20), and Struct (Nov 25) without clamping dates."),
            ("Topic-Aware Drills", "Zero Generic Fillers", "Generates tailored syntax reviews, hands-on coding tasks, dynamic memory drills, and exam-day warmups per subject."),
            ("Editable Staging", "Real-Time Reprioritization", "Edit preparation rules, cycle priority badges, and refine micro-steps before committing to the study queue.")
        ]
    )

    # =========================================================================
    # SLIDE 4: FOCUS TIMER STUDIO (LIGHT THEME)
    # =========================================================================
    add_single_showcase_slide(
        tag="Dedicated Deep Work • Clean Light Studio",
        title="Distraction-Free Sprint Console with Midpoint Chime",
        desc="Isolates the user from all background dashboard clutter. Featuring an ergonomic 25-minute Pomodoro focus dial, acoustic midpoint chime, and integrated audio console.",
        img_name="04_focus_timer_studio_light.png",
        cards=[
            ("Dopamine Calibration", "Acoustic Midpoint Chime", "Gentle bell at 12m30s signals half-way progress, grounding wandering attention without breaking deep flow state."),
            ("Custom Durations", "Flexible Sprint Lengths", "Quick 5m / 10m / 25m / 50m chips allow matching sprint length to fluctuating daily ADHD energy levels."),
            ("Integrated Deck", "Studio Audio Strip", "Central hardware playbar keeps focus audio controls within reach without switching away to external music apps.")
        ]
    )

    # =========================================================================
    # SLIDE 5: FOCUS TIMER STUDIO (DARK THEME)
    # =========================================================================
    add_single_showcase_slide(
        tag="Dedicated Deep Work • Carbon Obsidian Studio",
        title="Total Immersion Focus Dial for Night Sprints",
        desc="Zero peripheral distraction. Sits centered in deep space black with glowing emerald focus indicator and immediate single-keystroke Spacebar start/pause controls.",
        img_name="05_focus_timer_studio_dark.png",
        cards=[
            ("Zero Peripheral Noise", "Shielded Work Environment", "All task queues, exam dates, and statistics vanish. Only the current task and timer clock remain in view."),
            ("Single Keystroke", "Instant Keyboard Drive", "Spacebar toggles sprint, Escape exits, Ctrl+Shift+D inverts theme instantly without interrupting audio stream."),
            ("Attention Bounce", "Visual Guidance Cue", "Subtle pulse animation guides user attention to play controls if Spotify is triggered during an active sprint.")
        ]
    )

    # =========================================================================
    # SLIDE 6: SPOTIFY HARDWARE CONSOLE DECK
    # =========================================================================
    add_single_showcase_slide(
        tag="Integrated Audio Hardware • Zero Previews",
        title="Full-Track Spotify Web API Study Console",
        desc="Eliminates the #1 ADHD distraction trigger: switching windows to change music. Renders the user's real Spotify library with zero 30-second preview limitations.",
        img_name="06_spotify_hardware_console_deck.png",
        cards=[
            ("Real Personal Library", "Live Spotify Web API", "Dynamically pulls user playlists directly into an obsidian grid with cover-extracted ambient gradients."),
            ("Full Track Playback", "Native Client Protocol", "One click launches URI playback directly in Spotify desktop client for unrestricted high-fidelity audio."),
            ("Instant Catalog Search", "Zero Context-Switching", "Search any track, study frequency, or focus playlist and launch playback without leaving the study sprint.")
        ]
    )

    # =========================================================================
    # SLIDE 7: MINI-PLAYER STANDARD PILL MODE
    # =========================================================================
    add_single_showcase_slide(
        tag="Ambient Audio Control • Standard Pill Mode",
        title="Magnetic Floating Mini-Player with Corner Snapping",
        desc="A floating glassmorphic audio pill that docks seamlessly into any screen corner. Features live seekbar scrub, volume slider, and track metadata with zero window switching.",
        img_name="07_mini_player_standard_pill.png",
        cards=[
            ("Corner Magnetics", "Instant 140px Snap Pull", "Drag smoothly anywhere; snaps magnetically to top-left, top-right, bottom-left, or bottom-right corners."),
            ("Precise Scrubbing", "Direct Seekbar Track", "Click or drag the horizontal seekbar to skip directly to timestamps; volume slider adjusts desktop gain."),
            ("Full Drag Engine", "Pointer Capture Guard", "Advanced setPointerCapture engine prevents mouse loss or stuck drag states even when moving cursor rapidly.")
        ]
    )

    # =========================================================================
    # SLIDE 8: MINI-PLAYER COMPRESSED ALBUM MODE
    # =========================================================================
    add_single_showcase_slide(
        tag="Ambient Audio Control • Compressed Mode",
        title="Ultra-Compact 176px Vertical Album Companion",
        desc="Engineered for users who want maximum screen space for coding IDEs or notes. Features a large 156x156 album art cover, embedded 4px seekbar, and zero header truncation.",
        img_name="08_mini_player_compressed_album.png",
        cards=[
            ("Minimal Footprint", "176px High-Aesthetic Card", "Takes less than 12% screen width. Displays high-res album cover with embedded progress line."),
            ("Zero Header Clutter", "Protected 'Spotify' Label", "Permanently removed bulky PLAYING badges to guarantee the Spotify brand and close button never truncate."),
            ("Single-Click Switch", "Pill to Album Toggle", "Click the split-view icon in header to toggle instantly between wide horizontal pill and vertical album card.")
        ]
    )

    # =========================================================================
    # SLIDE 9: 1-THING ANTI-PARALYSIS MODE
    # =========================================================================
    add_single_showcase_slide(
        tag="ADHD Behavioral Engine • Instant Execution",
        title="1-Thing Anti-Paralysis Mode (Single-Task Execution)",
        desc="When faced with 20+ study tasks, ADHD working memory collapses into freeze state. 1-Thing mode aggressively hides everything except the single immediate micro-action.",
        img_name="09_single_task_anti_paralysis.png",
        cards=[
            ("Freeze Prevention", "Solitary Focus Isolation", "Blurs the entire background workspace. Displays exactly one ~15m subtask with bold title and priority badge."),
            ("Dopamine Payoff", "Instant Check-Off Flow", "Clicking '✓ Mark Complete' instantly records victory, updates progress, and presents the next micro-step."),
            ("Frictionless Escape", "Multi-Path Dismissal", "Easily exit back to the full dashboard anytime via circular close button, background click, or Escape key.")
        ]
    )

    # =========================================================================
    # SLIDE 10: MONTHLY STUDY CALENDAR (LIGHT & DARK)
    # =========================================================================
    add_dual_showcase_slide(
        tag="Milestone Planning • Dual Themes",
        title="Visual Exam & Study Schedule Calendar",
        desc="Translates distant, abstract exam dates into concrete visual timeline blocks. Combines countdown badges with color-coded subject chips to eliminate time-blindness.",
        img1_name="10_monthly_study_calendar_dark.png",
        title1="Carbon Obsidian Dark Mode",
        img2_name="11_monthly_study_calendar_light.png",
        title2="Clean Daytime Light Mode",
        cards=[
            ("Time-Blindness Cure", "Visual Date Proximity", "Color-coded exam milestone pills clearly show how close tests are, combating ADHD 'now vs not-now' thinking."),
            ("Scheduled Workload", "Daily Micro-Task Badges", "Calendar cells display scheduled study hours so students never unintentionally over-schedule their days."),
            ("Bi-Directional Sync", "RFC 5545 iCal Feed", "One-click copy subscription URL synchronizes all study milestones into Google Calendar, Apple Calendar, and Outlook.")
        ]
    )

    # =========================================================================
    # SLIDE 11: COMPACT PINNED DESKTOP WIDGET (LIGHT & DARK)
    # =========================================================================
    add_dual_showcase_slide(
        tag="Multitasking Companion • 380px Pinned Strip",
        title="Always-On-Top Compact Desktop Study Strip",
        desc="Pins alongside coding IDEs, lecture videos, or PDF textbooks. Takes only 380px horizontal screen width while providing instant task check-offs and audio controls.",
        img1_name="12_compact_desktop_widget_dark.png",
        title1="Carbon Dark Widget (380x740)",
        img2_name="13_compact_desktop_widget_light.png",
        title2="Clean Light Widget (380x740)",
        cards=[
            ("Pinned Multitasking", "Ultra-Narrow 380px Width", "Designed to sit comfortably next to Visual Studio Code, Zoom lecture streams, or Chrome research windows."),
            ("Instant Task Checks", "One-Click Item Striking", "Check off micro-steps directly from the strip without maximizing or switching focus away from active work."),
            ("Mini Spotify Strip", "Integrated Compact Player", "Track progression, play/pause, and skip controls stay pinned directly below the active task queue.")
        ]
    )

    # =========================================================================
    # SLIDE 12: TWO-WAY PHONE COMPANION & QR HUB
    # =========================================================================
    add_single_showcase_slide(
        tag="Mobile Ecosystem • Wireless LAN Sync",
        title="Two-Way Phone Companion Hub & Live QR Code Pairing",
        desc="Seamlessly bridges desktop PC and smartphone without external cloud servers. Instant QR scan unlocks full study tracking, task completion, and calendar feeds from your phone.",
        img_name="14_two_way_phone_companion_qr.png",
        cards=[
            ("Instant Camera Pairing", "Zero-Setup Live QR Code", "Scan with standard smartphone camera to instantly open local web companion at http://192.168.1.x:8765."),
            ("Two-Way Live Sync", "Real-Time LAN Protocol", "Checking off a task on phone updates the PC desktop app immediately with zero latency and zero data leakage."),
            ("Universal Calendar Feed", "RFC 5545 Live Feed URL", "One-click live subscription feed updates Apple Calendar, Google Calendar, and Outlook across all mobile devices.")
        ]
    )

    # =========================================================================
    # SLIDE 13: COGNITIVE ERGONOMICS & LOCAL AI
    # =========================================================================
    add_single_showcase_slide(
        tag="Cognitive Architecture • 100% Private Local AI",
        title="Sensory Ergonomics & Local Neural AI Configuration",
        desc="Total control over sensory stimulation and artificial intelligence telemetry. Choose between local offline neural copilot or self-hosted Ollama / DeepSeek models with zero privacy risk.",
        img_name="15_cognitive_ergonomics_preferences.png",
        cards=[
            ("Sensory Pacing", "Auditory & Visual Dials", "Toggle acoustic midpoint chimes, ambient background glow, and notification frequency to match sensory profile."),
            ("Zero Cloud Telemetry", "100% Offline Local AI", "Runs ephemeral neural task slicing directly on local CPU/GPU. Never sends study notes or personal tasks to cloud."),
            ("Data Sovereignty", "1-Click JSON Backup", "Full export and import of all study milestones, habit histories, and Spotify tokens into human-readable JSON files.")
        ]
    )

    # =========================================================================
    # SLIDE 14: TECHNICAL ARCHITECTURE & SUMMARY
    # =========================================================================
    summary_box = [
        Paragraph("PRODUCTION ENGINEERING SPECIFICATIONS", s_cover_tag),
        Paragraph("Why StudyPulse Outperforms Generic Productivity Tools", s_cover_title),
        Spacer(1, 10),
        Paragraph(
            "Generic productivity tools (Notion, Todoist, Forest) fail ADHD students because they introduce high "
            "configuration friction, cloud sync lag, and require constant tab-switching. StudyPulse is an engineered "
            "Win32 desktop system delivering sub-16ms UI responsiveness, hardware-accelerated audio, and native DWM integration.",
            s_cover_sub
        ),
        Spacer(1, 16)
    ]

    specs_table_data = [
        [
            Paragraph("<b>Subsystem</b>", s_card_badge),
            Paragraph("<b>Implementation Details</b>", s_card_badge),
            Paragraph("<b>ADHD Cognitive Benefit</b>", s_card_badge)
        ],
        [
            Paragraph("<b>Core Runtime</b>", s_card_title),
            Paragraph("Microsoft WebView2 + Python 3.14 + PyInstaller Native Binary (18.3 MB)", s_card_text),
            Paragraph("Sub-second startup, zero browser tab clutter, zero RAM bloat.", s_card_text)
        ],
        [
            Paragraph("<b>Audio Subsystem</b>", s_card_title),
            Paragraph("Win32 Process Interop + Spotify Web API PKCE Auth + Dynamic Canvas Gradient", s_card_text),
            Paragraph("Zero 30s preview limit; music control without switching windows.", s_card_text)
        ],
        [
            Paragraph("<b>Visual Typography</b>", s_card_title),
            Paragraph("Plus Jakarta Sans Display + Inter OpenType Body + JetBrains Mono Tabular", s_card_text),
            Paragraph("Clean visual hierarchy; stops layout jumping during countdowns.", s_card_text)
        ],
        [
            Paragraph("<b>Privacy & AI</b>", s_card_title),
            Paragraph("Local Ephemeral Neural Slicer + Ollama Local Model Port (:11434)", s_card_text),
            Paragraph("100% private study data; works completely offline with zero tracking.", s_card_text)
        ]
    ]

    specs_table = Table(specs_table_data, colWidths=[120, 340, 240])
    specs_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#141417")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#27272A")),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    summary_wrapper = Table([[summary_box], [specs_table]], colWidths=[720])
    summary_wrapper.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#09090B")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1C1C1F")),
        ('TOPPADDING', (0,0), (-1,-1), 24),
        ('BOTTOMPADDING', (0,0), (-1,-1), 24),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
        ('RIGHTPADDING', (0,0), (-1,-1), 20),
    ]))
    story.append(summary_wrapper)

    doc.build(story, canvasmaker=PitchDeckNumberedCanvas)
    print(f"Successfully generated Pitch Deck PDF at: {output_pdf}")
    return output_pdf

if __name__ == "__main__":
    build_pitch_deck()
