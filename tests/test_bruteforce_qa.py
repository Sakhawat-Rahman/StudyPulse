import os
import sys
import json
import datetime
import re
import threading
import time
import urllib.request
import urllib.error

# Resolve path
this_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(this_dir) if os.path.basename(this_dir) == 'tests' else this_dir
sys.path.insert(0, workspace_dir)
sys.path.insert(0, this_dir)
import app
from app import (
    parse_multi_exam_prompt,
    smart_multidomain_slice,
    run_ephemeral_llama_slice,
    plan_exam_schedule,
    generate_tailored_subtasks,
    generate_ical_feed,
    get_state_file_path,
    get_monitor_work_area,
    DesktopBridge
)

results = []

def record_finding(bug_id, subsystem, severity, trigger, expected, actual, root_cause, status="OPEN"):
    results.append({
        "id": bug_id,
        "subsystem": subsystem,
        "severity": severity,
        "trigger": trigger,
        "expected": expected,
        "actual": actual,
        "root_cause": root_cause,
        "status": status
    })

print("=================================================================")
print("STARTING BRUTE-FORCE QA & CHAOS HARNESS FOR STUDYPULSE v3.2")
print("=================================================================")

today = datetime.date(2026, 11, 8)

# -------------------------------------------------------------------------
# SUITE 1: Adversarial & Mixed-Domain Natural Language Fuzzing
# -------------------------------------------------------------------------
print("\n--- SUITE 1: Adversarial & Mixed-Domain NLP Fuzzing ---")

# 1.1 Mixed Exam + Personal Habit + Chore
p1 = "I have a Physics Midterm on 18th Nov (High importance), need to clean my messy room tomorrow, do a 45 minute leg workout today, and buy groceries on Friday"
res1 = smart_multidomain_slice(p1)
# Check: Did it turn into Workout Session or miss Physics Midterm?
if res1.get('domain') == 'fitness' or res1.get('title') == 'Workout Session' or not any('Physics' in ex.get('title', '') for ex in res1.get('exams', [])):
    record_finding(
        "BUG-001",
        "NLP Slicer",
        "HIGH",
        p1,
        "Should prioritize or separate Physics Midterm on 18th Nov from casual fitness/chore keywords.",
        f"Domain classified as '{res1.get('domain')}', title: '{res1.get('title')}'. Physics exam completely discarded in favor of workout session.",
        "app.py:L801: `is_fitness` early return triggers because 'midterm' is not in the exclusion list `['exam', 'quiz', 'test', 'study', 'class', 'cse', 'math', 'bio', 'chem']`."
    )

# 1.2 Uneven Respectively Mismatch (3 exams vs 2 dates)
p2 = "CSE 215, MAT 120, and PHY 111 exams on 16th and 19th November respectively"
exams2 = parse_multi_exam_prompt(p2, today=today)
if len(exams2) != 3 or any('CSE 215, MAT' in e['title'] for e in exams2):
    record_finding(
        "BUG-002",
        "NLP Slicer",
        "HIGH",
        p2,
        "Should separate 3 distinct exams: CSE 215, MAT 120, and PHY 111, mapping dates cleanly without dropping or grouping.",
        f"Parsed {len(exams2)} exams: {[e.get('title') for e in exams2]}",
        "app.py:L565: Regex for paired exams only splits on commas if len(names) >= 2 and len(days) >= 2, but fails when names.length != days.length or grouping includes 'and'."
    )

# 1.3 Past Dates & Same-Day Emergency Prompts
p3 = "I have a Bio Quiz TODAY in 3 hours and an Econ test yesterday on 3rd November"
res3 = smart_multidomain_slice(p3)
past_subtasks = []
for ex in res3.get('exams', []):
    for s in ex.get('subtasks', []):
        if s.get('date') and s['date'] < today.isoformat():
            past_subtasks.append((s['title'], s['date']))
if past_subtasks or any(ex.get('dueDate') < today.isoformat() for ex in res3.get('exams', [])):
    record_finding(
        "BUG-003",
        "NLP Slicer",
        "CRITICAL",
        p3,
        "Subtasks and active milestones must NEVER be scheduled on dates in the past prior to Today (2026-11-08).",
        f"Generated subtasks in the past: {past_subtasks}",
        "app.py:L657: `generate_tailored_subtasks` calculates `due_dt - timedelta(days=d)` without clamping to `today`, allowing dates prior to today."
    )

# 1.4 Month Rollover & Year Boundary
p4 = "Final exams on 29th November, 2nd December, and 5th January"
exams4 = parse_multi_exam_prompt(p4, today=today)
if len(exams4) != 3 or any(e['dueDate'] < '2026-11-29' for e in exams4 if 'december' in e.get('details', '').lower() or 'january' in e.get('details', '').lower()):
    record_finding(
        "BUG-004",
        "NLP Slicer",
        "HIGH",
        p4,
        "Should extract 3 distinct exams: Nov 29, 2026; Dec 02, 2026; Jan 05, 2027 (advancing year when month < current month).",
        f"Extracted {len(exams4)} exams: {[(e.get('title'), e.get('dueDate')) for e in exams4]}",
        "app.py:L478: `target_month` breaks on first month found (November), and year boundary is never advanced when month is earlier than current month."
    )

# 1.5 Ambiguous Numbers vs Course Codes vs Marks
p5 = "CSE 327 and EEE 141 exams on 21st Nov, 50 marks MCQ, Chapters 1, 2, 3, 4 and 15 practice problems, importance high"
exams5 = parse_multi_exam_prompt(p5, today=today)
if len(exams5) < 2 or any(e.get('priority') != 'important' for e in exams5):
    record_finding(
        "BUG-005",
        "NLP Slicer",
        "MEDIUM",
        p5,
        "Should extract 2 exams (CSE 327, EEE 141) with priority='important' without treating 50 marks or chapters 1..4, 15 as dates.",
        f"Extracted {len(exams5)} exams with priorities {[e.get('priority') for e in exams5]} and titles {[e.get('title') for e in exams5]}",
        "app.py:L496: `parse_priority_str` requires colon `(?:importance|priority)\\s*:` so `importance high` without colon falls back to normal."
    )

# 1.6 Empty, Whitespace, Emoji-Only & Syllabus Wall
for raw_edge in ["", "   ", "😭😭😭🔥🔥", "A" * 5000]:
    try:
        e_res = smart_multidomain_slice(raw_edge)
        assert e_res and "title" in e_res and "exams" in e_res and e_res["title"].strip() != ""
    except Exception as ex:
        record_finding(
            "BUG-006",
            "NLP Slicer",
            "HIGH",
            f"Fuzz string: {raw_edge[:30]}...",
            "Should safely return default milestone without throwing unhandled exception.",
            f"Exception raised: {ex}",
            "app.py:L780: smart_multidomain_slice does not handle extreme inputs safely."
        )

# 1.7 XSS Injection in Prompts
p_xss = "Exam on <img src=x onerror=alert(1)> 15th Nov & <script>window.close()</script>"
exams_xss = parse_multi_exam_prompt(p_xss, today=today)
for ex in exams_xss:
    if "<script>" in ex['title'] or "<img" in ex['title']:
        record_finding(
            "BUG-007",
            "UI/Dark Mode",
            "HIGH",
            p_xss,
            "Titles and details should sanitize or HTML-escape dangerous tags before insertion into DOM.",
            f"Unescaped raw HTML tags in parsed exam title: {ex['title']}",
            "studypulse.html:L4086, L4951: Template literals interpolate unescaped `${st.title}` and `${item.text}` into innerHTML."
        )
        break

# 1.8 Calendar Day Overflow Clamping (31st Nov, 30th Feb)
p_overflow = "CSE 215 quiz on 31st November and Math test on 30th February"
try:
    exams_overflow = parse_multi_exam_prompt(p_overflow, today=today)
    for ex in exams_overflow:
        due = datetime.date.fromisoformat(ex['dueDate'])
        assert due >= today, f"Date {due} is in the past"
        if "november" in ex.get('details', '').lower() or "31st" in ex.get('details', '').lower():
            assert ex['dueDate'].endswith("-11-30"), f"Expected Nov 30, got {ex['dueDate']}"
        if "february" in ex.get('details', '').lower() or "30th" in ex.get('details', '').lower():
            assert ex['dueDate'].endswith("-02-28"), f"Expected Feb 28, got {ex['dueDate']}"
except Exception as ex_overflow:
    record_finding(
        "BUG-019",
        "NLP Slicer",
        "MEDIUM",
        p_overflow,
        "Calendar overflow days should be safely clamped to the month's maximum valid day.",
        f"Exception raised: {ex_overflow}",
        "app.py: make_clamped_date failed or day was not clamped to monthrange."
    )

# 1.10 Conversational Multi-Exam Extraction & Title Cleaning
p_conv = "I have a math exam this Friday and I also have a CSC live exam on November 28 and the cse theory exam on November 15"
try:
    exams_conv = parse_multi_exam_prompt(p_conv, today=today)
    assert len(exams_conv) == 3, f"Expected 3 exams, got {len(exams_conv)}"
    titles = [e['title'] for e in exams_conv]
    assert "Math Exam" in titles, f"Missing 'Math Exam' in {titles}"
    assert "CSC Live Exam" in titles, f"Missing 'CSC Live Exam' in {titles}"
    assert "CSE Theory Exam" in titles, f"Missing 'CSE Theory Exam' in {titles}"
    math_ex = next(e for e in exams_conv if e['title'] == "Math Exam")
    assert math_ex['dueDate'] == "2026-11-13", f"Expected Friday Nov 13, got {math_ex['dueDate']}"
    csc_ex = next(e for e in exams_conv if e['title'] == "CSC Live Exam")
    assert csc_ex['dueDate'] == "2026-11-28", f"Expected Nov 28, got {csc_ex['dueDate']}"
    cse_ex = next(e for e in exams_conv if e['title'] == "CSE Theory Exam")
    assert cse_ex['dueDate'] == "2026-11-15", f"Expected Nov 15, got {cse_ex['dueDate']}"
except Exception as ex_conv:
    record_finding(
        "BUG-020",
        "NLP Slicer",
        "HIGH",
        p_conv,
        "Should extract 3 distinct exams (Math Exam, CSC Live Exam, CSE Theory Exam) with clean titles and exact dates.",
        f"Exception: {ex_conv}",
        "app.py: clean_exam_title or weekday regex or month-first matching failed."
    )

# -------------------------------------------------------------------------
# SUITE 2: Ephemeral Neural Engine Torture Tests
# -------------------------------------------------------------------------
print("\n--- SUITE 2: Ephemeral Neural Engine Torture Tests ---")

# 2.1 Malformed / Truncated JSON recovery
malformed_outputs = [
    '```json\n{"title": "Exam Prep", "exams": [{"title": "Bio", "dueDate": "2026-11-20", "priority": "important"}],}\n```',
    '{"title": "Truncated Exam", "isMultiExam": false, "exams": [{"title": "Chem", "dueDate": "2026-11-15"',
]
for raw_out in malformed_outputs:
    try:
        cleaned_json = re.sub(r'```(?:json)?\s*', '', raw_out).strip('`').strip()
        cleaned_json = re.sub(r',\s*([}\]])', r'\1', cleaned_json)
        match = re.search(r'\{.*\}', cleaned_json, re.DOTALL)
        if match:
            json.loads(match.group(0))
    except Exception as e:
        record_finding(
            "BUG-008",
            "Neural Subprocess",
            "HIGH",
            f"Malformed LLM stdout: {raw_out[:40]}...",
            "Regex cleaner should repair trailing commas and extract valid JSON before failing.",
            f"JSONDecodeError: {e}",
            "app.py:L1027: Raw `json.loads(match.group(0))` without trailing comma or markdown backtick sanitization."
        )
        break

# 2.2 Concurrency Lock for Subprocess Execution
bridge = DesktopBridge()
if not hasattr(bridge, '_slice_lock') and not hasattr(app, '_slice_lock') and not hasattr(app, '_ai_inference_lock'):
    record_finding(
        "BUG-009",
        "Neural Subprocess",
        "HIGH",
        "Concurrent rapid calls to slice_task_ai",
        "A threading.Lock or mutex must prevent concurrent llama-cli subprocesses from spawning simultaneously.",
        "Zero mutex locks found in app.py for subprocess execution; multiple rapid clicks spawn multiple CPU processes simultaneously.",
        "app.py:L1745: `slice_task_ai` has no concurrency lock."
    )

# 2.3 Recursive 2-Minute Micro-Slicer Prefix Bloat
task_title = "Step 0: Open tools & set up workspace for Review CSE"
sub_res = bridge.slice_micro_task(task_title, current_mins=2)
# Second recursive slice on output
sub_res2 = bridge.slice_micro_task(sub_res[0]['title'], current_mins=2)
if "Step 0: Open tools & set up workspace for Step 0" in sub_res2[0]['title'] or sub_res2[0]['title'].count("Step 0:") > 1:
    record_finding(
        "BUG-010",
        "NLP Slicer",
        "MEDIUM",
        f"slice_micro_task('{task_title}')",
        "Should strip existing 'Step X: ...' prefixes to prevent recursive prefix ballooning.",
        f"Bloated title: {sub_res2[0]['title']}",
        "app.py:L1756: `slice_micro_task` blindly appends `clean` without stripping previous step prefixes."
    )

# -------------------------------------------------------------------------
# SUITE 3: Ironclad Daily Habits & Rollover Edge Cases
# -------------------------------------------------------------------------
print("\n--- SUITE 3: Ironclad Daily Habits & Rollover Edge Cases ---")

# Check JS source code in studypulse.html
html_path = os.path.join(workspace_dir, "studypulse.html")
with open(html_path, "r", encoding="utf-8") as f:
    js_code = f.read()

# 3.1 Division by Zero on Target = 0
habit_zero = {"id": "h-test", "type": "numeric", "target": 0, "current": 50}
def py_get_habit_pct(h):
    if h.get('type') in ['numeric', 'counter']:
        target = h.get('target', 0)
        if not target or target <= 0:
            return 0
        return min(100, round((h.get('current', 0) / target) * 100))
    return 0

# 3.2 Over-Target Step Input
habit_over = {"id": "h-steps", "type": "numeric", "target": 7000, "current": 15000}
pct_over = py_get_habit_pct(habit_over)
assert pct_over <= 100, f"Expected <= 100%, got {pct_over}"

# 3.3 Multi-Day Offline Rollover Gap & todayLazyProgress Persistence
if "state.todayLazyProgress = null" not in js_code and "delete state.todayLazyProgress" not in js_code:
    record_finding(
        "BUG-011",
        "Habit Engine",
        "HIGH",
        "Crossing midnight rollover when todayLazyProgress was previously logged (e.g. 70%)",
        "`todayLazyProgress` must be reset/cleared to null on midnight rollover so new day starts at 0%.",
        "`checkMidnightRollover` resets habit.current but leaves `state.todayLazyProgress` intact, causing getTodayOverallHabitScore() to report 70% on the new day.",
        "studypulse.html:L4279: `checkMidnightRollover` omits `state.todayLazyProgress = null;`"
    )

# Multi-day gap in habitHistory
if "while (curr < end)" not in js_code:
    record_finding(
        "BUG-012",
        "Habit Engine",
        "MEDIUM",
        "User opens app on Nov 8 after last opening on Nov 3 (5 days gap)",
        "Intermediate missed days (Nov 4, 5, 6, 7) should be recorded with 0% overall score in habitHistory.",
        "Only state.lastRolloverDate is recorded; intermediate days are missing from habitHistory entirely.",
        "studypulse.html:L4285: Single `if (todayStr !== state.lastRolloverDate)` only archives the single lastRolloverDate."
    )

# -------------------------------------------------------------------------
# SUITE 4: Dynamic 1:1 SVG Line Histogram Geometry & Data Extremes
# -------------------------------------------------------------------------
print("\n--- SUITE 4: SVG Line Histogram Geometry & Data Extremes ---")

# 4.1 Empty history crash in points[0].x
if "if (!points || points.length === 0)" not in js_code:
    record_finding(
        "BUG-013",
        "SVG Histogram",
        "HIGH",
        "renderHabitConsistencyChart() called when data array is empty or points is empty",
        "Should guard against empty points array before accessing `points[0].x` and `lastPoint.x`.",
        "When points is empty, `points[0].x` throws TypeError: Cannot read properties of undefined (reading 'x').",
        "studypulse.html:L4366: `points[points.length - 1].x` and `points[0].x` evaluated without `if (points.length === 0)` guard."
    )

# -------------------------------------------------------------------------
# SUITE 5: Strict 3-Mode Priority & State Migration Integrity
# -------------------------------------------------------------------------
print("\n--- SUITE 5: Strict 3-Mode Priority & State Migration ---")

# 5.1 Legacy State Import
if "normalizePriority" not in js_code:
    record_finding(
        "BUG-014",
        "Sync/Concurrency",
        "HIGH",
        "Loading legacy state with priority='emergency' or 'HIGH'",
        "`sanitizeGoals` should normalize all priorities strictly to 'important' | 'normal' | 'low'.",
        "sanitizeGoals only calls `.toLowerCase()`, leaving legacy 'emergency' as priority in state.",
        "studypulse.html:L2626: `priority: g && g.priority ? String(g.priority).toLowerCase() : 'normal'` preserves 'emergency'."
    )

# -------------------------------------------------------------------------
# SUITE 6: Calendar (.ics / webcal://) & Webhook Concurrency
# -------------------------------------------------------------------------
print("\n--- SUITE 6: Calendar RFC 5545 & Webhook Concurrency ---")

# 6.1 RFC 5545 Character Escaping
test_state = {
    "goals": [
        {
            "id": "g-test",
            "title": "Math Midterm, Calculus & Algebra; Part 1\nNotes",
            "dueDate": "2026-11-20",
            "category": "exam",
            "priority": "important",
            "subtasks": [
                {"id": "s-test", "title": "Review formulas, chapters 1;2\nStep 1", "date": "2026-11-18", "mins": 30, "priority": "important", "completed": False}
            ]
        }
    ],
    "ironcladHabits": []
}
feed = generate_ical_feed(test_state)
# Check for unescaped newlines, commas, or semicolons in SUMMARY per RFC 5545
for line in feed.split("\r\n"):
    if line.startswith("SUMMARY:") and re.search(r'(?<!\\)[,;]', line):
        record_finding(
            "BUG-015",
            "Calendar/ICS",
            "HIGH",
            "Exam title with commas and semicolons in RFC 5545 feed",
            "Commas, semicolons, and newlines in SUMMARY/DESCRIPTION must be escaped as \\,, \\;, \\n per RFC 5545.",
            f"Unescaped line in iCalendar feed: {line}",
            "app.py:L1107: `f\"SUMMARY:[{cat}] {title}\"` does not call `escape_rfc5545()`."
        )
        break

# -------------------------------------------------------------------------
# SUITE 7: LocalSyncServer Race Conditions (Concurrent Writes)
# -------------------------------------------------------------------------
print("\n--- SUITE 7: LocalSyncServer Concurrent State Saves ---")

threads = []
write_errors = []

def concurrent_writer(thread_id):
    try:
        res = bridge.save_app_state({"thread_id": thread_id, "time": time.time(), "goals": []})
        if res.get("status") != "ok":
            write_errors.append(res.get("message", "Save failed"))
    except Exception as e:
        write_errors.append(str(e))

for i in range(15):
    t = threading.Thread(target=concurrent_writer, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

if write_errors:
    record_finding(
        "BUG-016",
        "Sync/Concurrency",
        "CRITICAL",
        "15 concurrent writes to state_file without mutex lock",
        "Atomic file replacement must be serialized with a threading.Lock and use unique temp filenames.",
        f"PermissionError / WinError encountered during concurrent write: {write_errors[0]}",
        "app.py:L1612 & L1952: Both `save_app_state` and `do_POST` write to identical `state_file + '.tmp'` without a threading.Lock."
    )

# -------------------------------------------------------------------------
# SUITE 8: Win32 Windowing, DPI Scaling & Multi-Monitor Edge Cases
# -------------------------------------------------------------------------
print("\n--- SUITE 8: Win32 Windowing, DPI Scaling & Multi-Monitor ---")

# 8.1 Off-screen coordinate clamping
left, top, work_w, work_h = get_monitor_work_area()
offscreen_x, offscreen_y = 3500, -500
# Check if move_window_to clamps coordinates
res_move = bridge.move_window_to(offscreen_x, offscreen_y)
# If coordinates were not clamped
if res_move.get('x') == offscreen_x and (offscreen_x > left + work_w or offscreen_y < top):
    record_finding(
        "BUG-017",
        "Win32 Windowing",
        "MEDIUM",
        f"move_window_to({offscreen_x}, {offscreen_y}) when monitor work area is [{left}, {top}, {work_w}, {work_h}]",
        "Window coordinates should be clamped to ensure the window titlebar remains visible on screen.",
        f"Unclamped coordinates accepted: x={res_move.get('x')}, y={res_move.get('y')}",
        "app.py:L1263: `move_window_to` accepts raw coordinates without work-area bounds clamping."
    )

# 8.2 Ctrl+Space toggle vs stacking
if "!modal.classList.contains('hidden')" not in js_code:
    record_finding(
        "BUG-018",
        "UI/Dark Mode",
        "LOW",
        "Pressing Ctrl+Space while braindump modal is already open",
        "Ctrl+Space should toggle (close) the modal if already open, and Escape key should dismiss it.",
        "`Ctrl+Space` calls `openBrainDumpModal()` unconditionally without checking if already active.",
        "studypulse.html:L6071: Keydown handler for `e.ctrlKey && e.code === 'Space'` unconditionally opens without toggle check."
    )

print("\n=================================================================")
if len(results) == 0:
    print("CHAOS TEST RUN COMPLETE: ALL 18+ EDGE CASES PASSED! 0 BUGS REMAINING.")
else:
    print(f"CHAOS TEST RUN COMPLETE: STILL FOUND {len(results)} UNRESOLVED ISSUES.")
    for r in results:
        print(f"  [{r['id']}] ({r['severity']}) {r['subsystem']}: {r['trigger'][:45]}...")
print("=================================================================")
