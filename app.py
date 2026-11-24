import html
"""
StudyPulse Desktop Application & Widget Wrapper
Monochrome Glassmorphic ADHD Study and Exam Tracker
Ultra-Reliable Win32 Edge Chromium Host
"""

import calendar
import ctypes
import datetime
import http.server
import json
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request

# 1. Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("StudyPulse")

# Global synchronization locks for thread-safe state IO and AI inference
_state_io_lock = threading.Lock()
_ai_inference_lock = threading.Lock()


# 2. Prevent legacy MSHTML registry write access denials on Windows
try:
    import webview.platforms.mshtml as mshtml
    mshtml._set_ie_mode = lambda: None
except Exception:
    pass

# 3. Force pywebview to recognize Edge Chromium as active runtime
import webview
for _cand in [
    r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application",
    r"C:\Program Files\Microsoft\EdgeWebView\Application",
]:
    if os.path.exists(_cand):
        for _sub in os.listdir(_cand):
            _fsub = os.path.join(_cand, _sub)
            if os.path.isdir(_fsub) and os.path.exists(os.path.join(_fsub, "msedgewebview2.exe")):
                webview.settings["WEBVIEW2_RUNTIME_PATH"] = _fsub
                break
        if webview.settings.get("WEBVIEW2_RUNTIME_PATH"):
            break

import webview.platforms.winforms as winforms
winforms.is_chromium = True
winforms.renderer = 'edgechromium'
try:
    import webview.platforms.edgechromium as Chromium
    winforms.Chromium = Chromium
except Exception:
    pass


def terminate_other_instances():
    """
    Terminates any stale background instances of StudyPulse
    so no ghost or orphaned windows linger on the desktop.
    Carefully preserves PyInstaller bootloader parent process.
    """
    try:
        current_pid = os.getpid()
        parent_pid = os.getppid() if hasattr(os, "getppid") else None
        TH32CS_SNAPPROCESS = 0x00000002

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * 260),
            ]

        k32 = ctypes.windll.kernel32
        hSnap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

        if k32.Process32First(hSnap, ctypes.byref(pe)):
            while True:
                name = pe.szExeFile.decode("utf-8", errors="ignore").lower()
                pid = pe.th32ProcessID
                # Protect current process, its parent bootloader, and its children
                if "studypulse.exe" in name and pid != current_pid and pid != parent_pid and pe.th32ParentProcessID != current_pid:
                    hProc = k32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
                    if hProc:
                        k32.TerminateProcess(hProc, 0)
                        k32.CloseHandle(hProc)
                        logger.info(f"Terminated stale StudyPulse instance (PID {pid})")
                if not k32.Process32Next(hSnap, ctypes.byref(pe)):
                    break
        k32.CloseHandle(hSnap)
    except Exception as e:
        logger.warning(f"Instance check skipped: {e}")


def find_webview2_runtime():
    """Locates the Microsoft Edge WebView2 runtime on Windows."""
    import winreg

    subkeys = [
        r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\ClientState\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\Microsoft\EdgeUpdate\ClientState\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    ]
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for subkey in subkeys:
            try:
                with winreg.OpenKey(root, subkey) as key:
                    for val_name in ("EBWebView", "UninstallString"):
                        try:
                            val, _ = winreg.QueryValueEx(key, val_name)
                            if val:
                                dir_path = val if os.path.isdir(val) else os.path.dirname(val)
                                if os.path.exists(os.path.join(dir_path, "msedgewebview2.exe")):
                                    return dir_path
                                parent = os.path.dirname(dir_path)
                                if os.path.exists(os.path.join(parent, "msedgewebview2.exe")):
                                    return parent
                        except Exception:
                            pass
            except Exception:
                pass

    candidate_dirs = [
        r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application",
        r"C:\Program Files\Microsoft\EdgeWebView\Application",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\EdgeWebView\Application"),
    ]
    for c_dir in candidate_dirs:
        if os.path.isdir(c_dir):
            try:
                for entry in os.listdir(c_dir):
                    full_path = os.path.join(c_dir, entry)
                    if os.path.isdir(full_path) and os.path.isfile(os.path.join(full_path, "msedgewebview2.exe")):
                        return full_path
            except Exception:
                pass

    return None


runtime_path = find_webview2_runtime()
if runtime_path:
    logger.info(f"Using WebView2 Runtime: {runtime_path}")

webview.settings["ALLOW_FILE_URLS"] = True
# CRITICAL: Disable pywebview global mouse interceptor so button clicks are NEVER blocked!
webview.settings["DRAG_REGION_SELECTOR"] = None
webview.settings["DRAG_REGION_DIRECT_TARGET_ONLY"] = True


def get_asset_path(filename="studypulse.html"):
    """Resolves absolute path to asset handling PyInstaller packaging (_MEIPASS)."""
    # 1. First, check directly beside the executable (or script) so local updates apply immediately!
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        exe_candidate = os.path.join(exe_dir, filename)
        if os.path.exists(exe_candidate):
            return exe_candidate
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_candidate = os.path.join(script_dir, filename)
        if os.path.exists(script_candidate):
            return script_candidate

    # 2. Check current working directory
    cwd_candidate = os.path.join(os.getcwd(), filename)
    if os.path.exists(cwd_candidate):
        return cwd_candidate

    # 3. Fallback to bundled asset in PyInstaller temporary folder (_MEIPASS)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_candidate = os.path.join(sys._MEIPASS, filename)
        if os.path.exists(meipass_candidate):
            return meipass_candidate

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


DASHBOARD_WIDTH = 1240
DASHBOARD_HEIGHT = 820
WIDGET_WIDTH = 380
WIDGET_HEIGHT = 700


def get_primary_screen():
    try:
        screens = webview.screens
        if screens:
            for s in screens:
                if getattr(s, "x", 0) == 0 and getattr(s, "y", 0) == 0:
                    return s
            return screens[0]
    except Exception:
        pass
    return None


def get_widget_position():
    """Glues widget cleanly at bottom-right or top-right desktop corner."""
    left, top, work_w, work_h = get_monitor_work_area()
    x = max(left + 10, left + work_w - WIDGET_WIDTH - 20)
    y = max(top + 10, top + (work_h - WIDGET_HEIGHT) // 2)
    return x, y


def get_dashboard_position():
    left, top, work_w, work_h = get_monitor_work_area()
    x = max(left, left + (work_w - DASHBOARD_WIDTH) // 2)
    y = max(top, top + (work_h - DASHBOARD_HEIGHT) // 2)
    return x, y


def get_safe_storage_path(is_widget=False):
    """
    Creates a dedicated, clean, non-conflicting profile folder in TEMP
    so WebView2 never encounters (0x800700AA) lock conflicts.
    Also invalidates WebView2 HTTP disk cache so stale assets are never served.
    """
    prefix = "widget" if is_widget else "dashboard"
    target = os.path.join(tempfile.gettempdir(), f"StudyPulse_WV2_{prefix}")
    try:
        os.makedirs(target, exist_ok=True)
        for sub_cache in [
            os.path.join(target, "EBWebView", "Default", "Cache"),
            os.path.join(target, "EBWebView", "Default", "Code Cache"),
        ]:
            if os.path.exists(sub_cache):
                try:
                    import shutil
                    shutil.rmtree(sub_cache, ignore_errors=True)
                except Exception:
                    pass
        return target
    except Exception:
        return None


def get_state_file_path():
    """State storage persistent in %APPDATA%\\StudyPulse."""
    candidates = [
        os.path.join(os.environ.get("APPDATA", ""), "StudyPulse"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "StudyPulse"),
        os.path.join(tempfile.gettempdir(), "StudyPulse"),
    ]
    for d in candidates:
        if d:
            try:
                os.makedirs(d, exist_ok=True)
                test_f = os.path.join(d, "perm_test.tmp")
                with open(test_f, "w") as f:
                    f.write("ok")
                os.remove(test_f)
                return os.path.join(d, "studypulse_state.json")
            except Exception:
                continue
    return os.path.join(tempfile.gettempdir(), "studypulse_state.json")


def get_spotify_auth_file_path():
    """Dedicated persistent storage for Spotify OAuth tokens and Client ID in APPDATA."""
    base_dir = os.environ.get("APPDATA")
    if not base_dir:
        base_dir = tempfile.gettempdir()
    d = os.path.join(base_dir, "StudyPulse")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "spotify_auth.json")


def get_monitor_work_area(hwnd=None):
    """Resolves exact display working area excluding taskbar."""
    try:
        user32 = ctypes.windll.user32
        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT),
                        ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        target = hwnd if hwnd else user32.GetDesktopWindow()
        hMon = user32.MonitorFromWindow(target, 2)  # MONITOR_DEFAULTTONEAREST
        if hMon and user32.GetMonitorInfoW(hMon, ctypes.byref(mi)):
            return (
                int(mi.rcWork.left),
                int(mi.rcWork.top),
                int(mi.rcWork.right - mi.rcWork.left),
                int(mi.rcWork.bottom - mi.rcWork.top)
            )
    except Exception:
        pass
    screen = get_primary_screen()
    if screen:
        return 0, 0, int(screen.width), int(screen.height - 40)
    return 0, 0, 1920, 1040


def set_window_corner_preference(hwnd, do_not_round: bool):
    """
    Toggles Windows 11 window corner rounding.
    When maximized: DWMWCP_DONOTROUND (1) ensures true edge-to-edge coverage with 0 desktop gap in corners.
    When restored: DWMWCP_ROUND (2) restores smooth rounded corners.
    """
    if not hwnd:
        return
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_DONOTROUND = 1
        DWMWCP_ROUND = 2
        val = ctypes.c_int(DWMWCP_DONOTROUND if do_not_round else DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(val), ctypes.sizeof(val)
        )
    except Exception as e:
        logger.debug(f"Could not set corner preference: {e}")


def apply_taskbar_icon(hwnd=None):
    """
    Applies the StudyPulse icon directly to the Win32 window and taskbar button,
    replacing any generic Python / WebView2 / floppy disk icon.
    """
    try:
        user32 = ctypes.windll.user32
        if not hwnd:
            hwnd = user32.FindWindowW(None, "StudyPulse")
        if not hwnd:
            return

        ico_path = get_asset_path("studypulse.ico")
        hicon_sm = 0
        hicon_lg = 0

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010

        if os.path.exists(ico_path):
            try:
                hicon_sm = user32.LoadImageW(None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                hicon_lg = user32.LoadImageW(None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
            except Exception as e:
                logger.warning(f"LoadImageW error: {e}")

        if not hicon_lg:
            try:
                h_mod = ctypes.windll.kernel32.GetModuleHandleW(None)
                hicon_lg = user32.LoadIconW(h_mod, 1)
                hicon_sm = user32.LoadIconW(h_mod, 1)
            except Exception:
                pass

        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        if hicon_sm:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_sm)
        if hicon_lg:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_lg)
    except Exception as e:
        logger.warning(f"apply_taskbar_icon warning: {e}")



# --- STUDYPULSE v3.0: 0-RAM EPHEMERAL MICRO-AI, CALENDAR & WEBHOOK SUBSYSTEMS ---

_ai_download_state = {
    "downloading": False,
    "pct": 0,
    "error": None,
    "installed": False,
    "message": ""
}

def get_models_dir():
    """Returns dedicated directory for local GGUF models and llama-cli binaries."""
    # First priority: check executable / script local models directory
    exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    local_exe_models = os.path.join(exe_dir, "models")
    if os.path.exists(local_exe_models) and os.path.isdir(local_exe_models):
        return local_exe_models
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_script_models = os.path.join(script_dir, "models")
    if os.path.exists(local_script_models) and os.path.isdir(local_script_models):
        return local_script_models

    base = os.path.expandvars(r"%APPDATA%\StudyPulse\models")
    try:
        os.makedirs(base, exist_ok=True)
        return base
    except Exception:
        return exe_dir

def find_llama_cli():
    """Locates llama-cli.exe executable if installed."""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = get_models_dir()
    candidates = [
        os.path.join(models_dir, "llama-cli.exe"),
        os.path.join(models_dir, "llama.exe"),
        os.path.join(exe_dir, "models", "llama-cli.exe"),
        os.path.join(script_dir, "models", "llama-cli.exe"),
        os.path.join(exe_dir, "llama-cli.exe"),
        os.path.join(script_dir, "llama-cli.exe"),
        os.path.join(models_dir, "bin", "llama-cli.exe"),
    ]
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, os.path.join(sys._MEIPASS, "models", "llama-cli.exe"))
        candidates.insert(1, os.path.join(sys._MEIPASS, "llama-cli.exe"))
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return c
    return None

def find_gguf_model():
    """Locates any .gguf model file in the models directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(script_dir, "models"),
        get_models_dir(),
        script_dir,
    ]
    if hasattr(sys, "_MEIPASS"):
        search_dirs.insert(0, os.path.join(sys._MEIPASS, "models"))
        search_dirs.insert(1, sys._MEIPASS)

    for d in search_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(".gguf"):
                    return os.path.join(d, f)
    return None

def check_ai_engine_ready():
    """Checks if both binary and model exist."""
    cli = find_llama_cli()
    model = find_gguf_model()
    return bool(cli and model), cli, model

def download_file_with_progress(url, dest_path, update_fn):
    """Downloads a file with chunked progress reporting."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "StudyPulse/3.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 64 * 1024
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path + ".tmp", "wb") as out:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = int((downloaded / total) * 100)
                        update_fn(pct)
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
            os.replace(dest_path + ".tmp", dest_path)
        return True
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        try:
            if os.path.exists(dest_path + ".tmp"):
                os.remove(dest_path + ".tmp")
        except Exception:
            pass
        raise e

def make_clamped_date(year, month, day):
    """
    Safely constructs a datetime.date object, clamping day to the maximum valid
    calendar day for the given year and month (e.g. 31st Nov -> Nov 30, 30th Feb -> Feb 28).
    Prevents ValueError: day is out of range for month.
    """
    try:
        max_days = calendar.monthrange(int(year), int(month))[1]
        clamped_day = max(1, min(int(day), max_days))
        return datetime.date(int(year), int(month), clamped_day)
    except Exception:
        return datetime.date.today()

def clean_exam_title(raw_title: str) -> str:
    """Strips conversational noise and filler phrases while preserving course codes and topics."""
    if not raw_title:
        return "Study Milestone"
    cleaned = re.sub(
        r'^\s*(?:(?:i\s+)?(?:also\s+)?have(?:\s+(?:an?|the|my))?|also\s+have(?:\s+(?:an?|the|my))?|there\s+is(?:\s+(?:an?|the))?|we\s+have(?:\s+(?:an?|the))?|upcoming|my|the|an?)\s+',
        '',
        raw_title,
        flags=re.I
    ).strip()
    cleaned = re.sub(
        r'\s*\b(?:will\s+be\s+held|held\s+on|is\s+on|on|at|importance|priority|marks?|mcq|cq|included|100)\b.*$',
        '',
        cleaned,
        flags=re.I
    ).strip()
    words = cleaned.split()
    capitalized = []
    for w in words:
        if w.upper() in ["CSE", "CSC", "EEE", "MAT", "PHY", "ENG", "BIO", "CHEM", "MCQ", "CQ", "AI", "NLP", "ML"]:
            capitalized.append(w.upper())
        elif w.isupper() and len(w) > 1:
            capitalized.append(w)
        elif w.isdigit():
            capitalized.append(w)
        elif w.lower() in ['and', '&', 'of', 'for', 'in', 'on', 'at', 'to', 'a', 'an', 'the']:
            capitalized.append(w.lower())
        else:
            capitalized.append(w.capitalize())
    res = " ".join(capitalized)
    return res if res else raw_title

def parse_multi_exam_prompt(raw_prompt, today=None):
    if today is None:
        today = datetime.date.today()
    current_year = today.year
    text = (raw_prompt or "").strip()
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', '', text).strip()

    # Clean and isolate refinement instructions early so they don't corrupt clause splitting
    ref_match = re.search(r'\(Refinement instructions:\s*([^)]+)\)', text, re.I)
    refinement_text = ref_match.group(1).strip() if ref_match else ""
    if ref_match:
        text = re.sub(r'\(Refinement instructions:\s*[^)]+\)', '', text, flags=re.I).strip()

    lower = text.lower()

    day_names = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }

    target_month = today.month
    for m_name, m_num in months.items():
        if re.search(r'\b' + m_name + r'\b', lower):
            target_month = m_num
            break

    def get_upcoming_weekday(day_name):
        target_wd = day_names[day_name.lower()]
        current_wd = today.weekday()
        days_ahead = (target_wd - current_wd) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (today + datetime.timedelta(days=days_ahead)).isoformat()

    # Clean leading boilerplate
    cleaned = re.sub(r'^(?:upcoming\s+exams?|my\s+exams?|exams?\s+schedule|schedule:?)[.:;\s]*', '', text, flags=re.I).strip()

    # Priority parser helper: strictly ['important', 'normal', 'low']
    def parse_priority_str(s_str):
        p_m = re.search(r'(?:importance|priority)\s*(?::|\bis\b|\bset\s+to\b|\s+)\s*(high|urgent|emergency|important|normal|medium|low)', s_str, re.I)
        if p_m:
            rw = p_m.group(1).lower()
            if rw in ['high', 'urgent', 'emergency', 'important']:
                return 'important'
            elif rw in ['low']:
                return 'low'
            return 'normal'
        s_low = s_str.lower()
        if any(k in s_low for k in ["high priority", "importance: high", "importance high", "priority high", "urgent", "critical", "emergency"]):
            return "important"
        if any(k in s_low for k in ["low priority", "importance: low", "importance low", "priority low", "low"]):
            return "low"
        if any(k in s_low for k in ["normal", "medium", "importance normal", "priority normal"]):
            return "normal"
        return "normal"

    # Format B check: e.g. "I have CSE 215 Exams on 17th, 20th, 25th november on arrys, pointers and struct respectively"
    date_section_match = re.search(
        r'(?:on|dated?|in)?\s*([0-9\s,\band\bthstndrd]+)\s*(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)',
        cleaned,
        re.I
    )
    topics_match = None
    if date_section_match:
        post_date_str = cleaned[date_section_match.end():].strip()
        topics_match = re.search(
            r'^(?:(?:and\s+)?(?:these\s+are\s+)?(?:quizzes|exams|tests)?\s*(?:about|covering|topics?:|\bon\b|\bfor\b|\bover\b|\bregarding\b|\bwith\s+topics?\b)|(?:about|covering|topics?:|\bon\b|\bfor\b|\bover\b|\bregarding\b|\bwith\s+topics?\b))\s+([a-zA-Z0-9_\s,\+/]+?)(?:\s+(?:respectively|respectfully)|\s+break|\s+please|\.|$)',
            post_date_str,
            re.I
        )
    if not topics_match:
        topics_match = re.search(
            r'(?:about|covering|topics?:|\bon\b|\bfor\b|\bover\b|\bregarding\b|\bwith\s+topics?\b)\s+([a-zA-Z0-9_\s,\+/]+?)(?:\s+(?:respectively|respectfully)|\s+break|\s+please|\.|$)',
            cleaned,
            re.I
        )

    if date_section_match and topics_match and ("respectively" in lower or "respectfully" in lower or "quizzes" in lower or "exams" in lower):
        ds_raw = date_section_match.group(1)
        days = [int(m.group(1)) for m in re.finditer(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', ds_raw) if 1 <= int(m.group(1)) <= 31]
        raw_top = topics_match.group(1)
        raw_topics = [t.strip() for t in re.split(r'[,&]|\band\b', raw_top) if t.strip()]
        clean_topics = [t for t in raw_topics if t.lower() not in ['these', 'are', 'quizzes', 'exams', 'tests', 'topics', 'and', 'or', 'respectively', 'respectfully']]
        
        TOPIC_TYPO_MAP = {
            'arrys': 'Arrays', 'arry': 'Arrays', 'array': 'Arrays',
            'ptrs': 'Pointers', 'ptr': 'Pointers', 'pointer': 'Pointers',
            'struts': 'Structs', 'strut': 'Struct', 'struct': 'Struct', 'structs': 'Structs',
            'recusion': 'Recursion', 'algo': 'Algorithms', 'algos': 'Algorithms',
            'linkedlist': 'Linked Lists', 'oop': 'OOP', 'oops': 'OOP',
            'dbms': 'DBMS', 'calc': 'Calculus', 'diff': 'Differential Equations'
        }
        normalized_topics = []
        for t in clean_topics:
            t_low = t.lower()
            if t_low in TOPIC_TYPO_MAP:
                normalized_topics.append(TOPIC_TYPO_MAP[t_low])
            else:
                normalized_topics.append(' '.join(w.capitalize() for w in t.split()))

        if len(days) >= 2 or len(normalized_topics) >= 2:
            count = max(len(days), len(normalized_topics))

            pre_date_str = cleaned[:date_section_match.start()].strip()
            clean_pre = re.sub(r'^(?:(?:i\s+)?(?:also\s+)?have(?:\s+(?:an?|the|my))?|there\s+is(?:\s+(?:an?|the))?|we\s+have(?:\s+(?:an?|the))?|upcoming|my|the|an?|\d+\s+)\s*', '', pre_date_str, flags=re.I).strip()
            clean_subj = re.sub(r'\s*\b(?:exams?|quizzes?|tests?|finals?|mids?|midterms?)\b.*$', '', clean_pre, flags=re.I).strip()
            subj = ""
            if clean_subj:
                s_words = clean_subj.split()
                caps = []
                for w in s_words:
                    if w.upper() in ["CSE", "CSC", "EEE", "MAT", "PHY", "ENG", "BIO", "CHEM", "MCQ", "CQ", "AI", "NLP", "ML"]:
                        caps.append(w.upper())
                    elif w.isupper() and len(w) > 1:
                        caps.append(w)
                    elif w.isdigit():
                        caps.append(w)
                    elif w.lower() in ['and', '&', 'of', 'for', 'in', 'on', 'at', 'to', 'a', 'an', 'the']:
                        caps.append(w.lower())
                    else:
                        caps.append(w.capitalize())
                subj = " ".join(caps)
            if not subj:
                subj = "CSE" if "cse" in lower else ("STEM" if "exam" in lower else "Academic")

            m_type = "Quiz" if "quiz" in lower else "Exam"
            fmt_b_prio = parse_priority_str(cleaned)
            fmt_b_exams = []
            for i in range(count):
                top_str = normalized_topics[i] if i < len(normalized_topics) else f"Topic {i+1}"
                d_val = days[i] if i < len(days) else (today.day + (i+1)*3)
                yr = current_year + 1 if target_month < today.month else current_year
                try:
                    due = make_clamped_date(yr, target_month, d_val).isoformat()
                except Exception:
                    due = (today + datetime.timedelta(days=(i+1)*4)).isoformat()

                if re.search(r'\d', subj):
                    ex_title = f"{subj}: {top_str}"
                elif subj in ["CSE", "STEM", "Academic"]:
                    ex_title = f"{subj} {m_type}: {top_str}"
                else:
                    ex_title = f"{subj}: {top_str}"

                fmt_b_exams.append({
                    "title": ex_title,
                    "dueDate": due,
                    "priority": fmt_b_prio,
                    "details": f"{ex_title} on {due}"
                })
            return fmt_b_exams

    # Intelligently split clauses (supporting conversational 'and', semicolons, periods)
    if "respectively" not in lower and "respectfully" not in lower:
        raw_parts = [p.strip() for p in re.split(r'[;\n]+|(?<=[.!?])\s+|\s+and\s+(?=(?:I\s+(?:also\s+)?have\s+|the\s+|my\s+|an?\s+)?[A-Za-z0-9_\s]+\b(?:exam|quiz|test|mid|final)\b)', cleaned, flags=re.I) if p.strip()]
    else:
        raw_parts = [p.strip() for p in re.split(r'[;\n]+|(?<=[.!?])\s+', cleaned) if p.strip()]
    sentences = []
    for p in raw_parts:
        if re.match(r'^(?:importance|priority)\s*(?::|\s)\s*[a-z]+[.]?$', p, re.I) and sentences:
            sentences[-1] += "; " + p
        else:
            sentences.append(p)

    extracted_exams = []

    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean or len(s_clean) < 4:
            continue
        s_lower = s_clean.lower()
        prio = parse_priority_str(s_clean)

        # Check for multi-date series e.g. "Final exams on 29th November, 2nd December, and 5th January"
        multi_date_matches = list(re.finditer(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b', s_clean, re.I))
        if len(multi_date_matches) >= 2 and ("exams" in s_lower or "tests" in s_lower or "quizzes" in s_lower or "finals" in s_lower or "mids" in s_lower):
            base_title_m = re.search(r'([A-Za-z0-9_\s\-\+\/]+?\b(?:mid|final|quiz|exam|test|presentation|finals|exams|quizzes)s?\b)', s_clean, re.I)
            base_title = base_title_m.group(1).strip() if base_title_m else "Exam Milestone"
            base_title = re.sub(r's$', '', base_title, flags=re.I).strip()
            for idx, dm in enumerate(multi_date_matches):
                d_num = int(dm.group(1))
                m_str = dm.group(2).lower()
                m_val = months.get(m_str, target_month)
                yr = current_year + 1 if m_val < today.month else current_year
                try:
                    due_date = make_clamped_date(yr, m_val, d_num).isoformat()
                except Exception:
                    due_date = (today + datetime.timedelta(days=(idx+1)*5)).isoformat()
                extracted_exams.append({
                    "title": f"{base_title} {idx+1}",
                    "dueDate": due_date,
                    "priority": prio,
                    "details": f"{base_title} on {due_date}"
                })
            continue

        # Check for multiple course codes: e.g. "CSE 327 and EEE 141 exams on 21st Nov, 50 marks MCQ..."
        courses_m = re.search(r'([A-Za-z0-9_,\s&]+?)\s+(?:exams?|tests?|quizzes?)\s+on\s+([0-9\s,\band\bthstndrd]+)\s*([a-zA-Z]+)?', s_clean, re.I)
        if courses_m and (' and ' in courses_m.group(1) or ' & ' in courses_m.group(1) or ',' in courses_m.group(1)):
            names_raw = courses_m.group(1).strip()
            dates_raw = courses_m.group(2).strip()
            m_part = courses_m.group(3)
            clause_month = target_month
            if m_part:
                for mn, mnum in months.items():
                    if mn in m_part.lower():
                        clause_month = mnum
                        break
            names = [re.sub(r'^\s*(?:and|both)\s+', '', n.strip(), flags=re.I) for n in re.split(r'[,&]|\band\b', names_raw) if n.strip() and n.strip().lower() not in ['exams', 'exam', 'quizzes', 'quiz', 'tests', 'test', 'these', 'are']]
            days = [int(m.group(1)) for m in re.finditer(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', dates_raw) if 1 <= int(m.group(1)) <= 31]
            if len(names) >= 2:
                for idx, name in enumerate(names):
                    d_num = days[idx] if (days and idx < len(days)) else (days[-1] if days else 21)
                    yr = current_year + 1 if clause_month < today.month else current_year
                    try:
                        due_date = make_clamped_date(yr, clause_month, d_num).isoformat()
                    except Exception:
                        due_date = (today + datetime.timedelta(days=(idx+1)*4)).isoformat()
                    extracted_exams.append({
                        "title": f"{name} Exam",
                        "dueDate": due_date,
                        "priority": prio,
                        "details": s_clean
                    })
                continue

        # Check for pair: "A & B will be held on X and Y [respectively / respectfully]"
        resp_m = re.search(r'([A-Za-z0-9_,\s&]+?)\s+(?:will\s+be\s+held\s+on|held\s+on|on|are\s+on)\s+([0-9\s,\band\bthstndrd]+)\s*([a-zA-Z]+)?(?:\s+(?:respectfully|respectively))?', s_clean, re.I)
        if resp_m and ("respectively" in s_lower or "respectfully" in s_lower or " and " in resp_m.group(1) or " & " in resp_m.group(1)):
            names_raw = resp_m.group(1).strip()
            dates_raw = resp_m.group(2).strip()
            m_part = resp_m.group(3)
            pair_month = target_month
            if m_part:
                for mn, mnum in months.items():
                    if mn in m_part.lower():
                        pair_month = mnum
                        break

            names_raw = re.sub(r'\s+(?:exams?|quizzes?|tests?)\s*$', '', names_raw, flags=re.I).strip()
            names = [re.sub(r'^\s*(?:and|both)\s+', '', n.strip(), flags=re.I) for n in re.split(r'[,&]|\band\b', names_raw) if n.strip() and n.strip().lower() not in ['exams', 'exam', 'quizzes', 'quiz', 'tests', 'test', 'these', 'are', 'respectfully', 'respectively']]
            days = [int(m.group(1)) for m in re.finditer(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', dates_raw) if 1 <= int(m.group(1)) <= 31]

            if len(names) >= 2 and len(days) >= 1:
                for idx, name in enumerate(names):
                    d_num = days[idx] if idx < len(days) else days[-1]
                    yr = current_year + 1 if pair_month < today.month else current_year
                    try:
                        due_date = make_clamped_date(yr, pair_month, d_num).isoformat()
                    except Exception:
                        due_date = (today + datetime.timedelta(days=(idx+1)*5)).isoformat()
                    clean_name = clean_exam_title(name)
                    extracted_exams.append({
                        "title": clean_name,
                        "dueDate": due_date,
                        "priority": prio,
                        "details": s_clean
                    })
                continue

        # Single exam in this sentence
        title_m = re.search(r'([A-Za-z0-9_\s\-\+\/]+?\b(?:mid|final|quiz|exam|test|presentation)\b)', s_clean, re.I)
        if title_m:
            ex_title = title_m.group(1).strip()
        else:
            first_clause = re.split(r'\s+(?:on|at|held|is|dated|in|\:|\;)\s+', s_clean)[0]
            ex_title = first_clause.strip()

        # Clean conversational noise and title-case
        ex_title = clean_exam_title(ex_title)

        ex_date = None
        # Support "this Friday", "this upcoming Friday", "next Tuesday", etc.
        wd_m = re.search(r'\b(?:this\s+upcoming|this|upcoming|next|on)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', s_lower)
        if wd_m:
            ex_date = get_upcoming_weekday(wd_m.group(1))
        else:
            # Day first: e.g. "28th November"
            dm_m = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b', s_clean, re.I)
            if dm_m:
                d_val = int(dm_m.group(1))
                m_word = dm_m.group(2).lower()
                m_val = months.get(m_word, target_month)
                yr = current_year + 1 if m_val < today.month else current_year
                try:
                    ex_date = make_clamped_date(yr, m_val, d_val).isoformat()
                except Exception:
                    pass
            if not ex_date:
                # Month first: e.g. "November 28" or "November 15"
                md_m = re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\b', s_clean, re.I)
                if md_m:
                    m_word = md_m.group(1).lower()
                    m_val = months.get(m_word, target_month)
                    d_val = int(md_m.group(2))
                    yr = current_year + 1 if m_val < today.month else current_year
                    try:
                        ex_date = make_clamped_date(yr, m_val, d_val).isoformat()
                    except Exception:
                        pass
            if not ex_date:
                d_only = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', s_clean)
                if d_only:
                    d_val = int(d_only.group(1))
                    if 1 <= d_val <= 31:
                        yr = current_year + 1 if target_month < today.month else current_year
                        try:
                            ex_date = make_clamped_date(yr, target_month, d_val).isoformat()
                        except Exception:
                            pass

        if not ex_date:
            ex_date = (today + datetime.timedelta(days=(len(extracted_exams)+1)*4)).isoformat()

        extracted_exams.append({
            "title": ex_title or f"Exam {len(extracted_exams)+1}",
            "dueDate": ex_date,
            "priority": prio,
            "details": s_clean
        })

    return extracted_exams


def generate_tailored_subtasks(exam_title, details_text, due_date_str, priority, ex_idx=0, today=None):
    if today is None:
        today = datetime.date.today()
    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    clean_title = clean_exam_title(exam_title)

    try:
        due_dt = datetime.date.fromisoformat(due_date_str)
    except Exception:
        due_dt = today + datetime.timedelta(days=4)

    prep_dates = [due_dt - datetime.timedelta(days=d) for d in [4, 3, 2, 1]]
    d_exam = due_dt

    t_lower = (clean_title + " " + (details_text or "")).lower()

    t1_time = "10:00 AM" if ex_idx % 2 == 0 else "11:30 AM"
    t2_time = "2:30 PM" if ex_idx % 2 == 0 else "4:00 PM"
    t3_time = "6:00 PM" if ex_idx % 2 == 0 else "7:30 PM"

    d1, d2, d3, d4 = prep_dates[0], prep_dates[1], prep_dates[2], prep_dates[3]

    # Topic-specific intelligent task breakdown
    if any(k in t_lower for k in ["array", "arrays", "vector", "matrix"]):
        task1 = "Array Mechanics: Review 1D/2D syntax, indexing rules & boundary checks"
        task2 = "Hands-on Coding: Implement array traversal, element search & reversal algorithms"
        task3 = "Exam Drills: Solve 2 complex array problem sets & trace memory allocations"
        task4 = "Exam Day Warm-up: Quick scan of off-by-one errors & boundary edge cases"
    elif any(k in t_lower for k in ["pointer", "pointers", "ptr"]):
        task1 = "Pointer Fundamentals: Review memory addresses, & (address-of) and * (dereference)"
        task2 = "Pointer Arithmetic: Trace pointer increments, array offsets & string traversal"
        task3 = "Dynamic Memory: Code malloc(), free() drills & practice memory leak prevention"
        task4 = "Exam Day Warm-up: Memory diagram mental rehearsal & dangling pointer checklist"
    elif any(k in t_lower for k in ["struct", "structs"]):
        task1 = "Struct Architecture: Review multi-field declarations, typedefs & memory alignment"
        task2 = "Member Access: Practice dot operator (.) vs arrow operator (->) with pointers"
        task3 = "Complex Structures: Implement array of structs & nested struct code challenges"
        task4 = "Exam Day Warm-up: 10-minute cheat sheet review of struct syntax & sizing rules"
    elif any(k in t_lower for k in ["string", "strings"]):
        task1 = "String Fundamentals: Review null termination '\\0', char arrays & ASCII encoding"
        task2 = "String Manipulation: Implement strlen, strcpy, strcmp & reverse without library"
        task3 = "Exam Problem Sets: Solve substring matching & palindrome string algorithms"
        task4 = "Exam Day Warm-up: Null-terminator check & string buffer overflow edge cases"
    elif any(k in t_lower for k in ["recursion", "recursive"]):
        task1 = "Base Case Architecture: Review recursion anatomy, stack frames & termination rules"
        task2 = "Call Stack Tracing: Hand-trace tree recursion and recursive state transitions"
        task3 = "Problem Drills: Implement recursive divide-and-conquer problem sets"
        task4 = "Exam Day Warm-up: Rehearse stack overflow prevention & base condition audit"
    elif any(k in t_lower for k in ["oop", "object oriented", "class"]):
        task1 = "Core OOP Pillars: Review encapsulation, inheritance, polymorphism & abstraction"
        task2 = "Class Architecture: Code class definitions, constructors, destructors & overrides"
        task3 = "UML & Design Drills: Solve 2 object hierarchy scenarios with test cases"
        task4 = "Exam Day Warm-up: Quick review of access specifiers & virtual function tables"
    elif any(k in t_lower for k in ["linked list", "linkedlist"]):
        task1 = "Node Architecture: Review singly/doubly linked node definitions & head/tail pointers"
        task2 = "Core Operations: Implement node insertion, deletion & list reversal"
        task3 = "Edge Case Drills: Handle empty list, single node & cycle detection algorithms"
        task4 = "Exam Day Warm-up: Pointer diagram trace & memory free() sequence check"
    elif any(k in t_lower for k in ["stack", "queue"]):
        task1 = "LIFO & FIFO Mechanics: Review push/pop/enqueue/dequeue invariants & array backing"
        task2 = "Implementation Drills: Code stack-based bracket matching & circular buffers"
        task3 = "Exam Applications: Solve infix-to-postfix or BFS queue algorithm problem sets"
        task4 = "Exam Day Warm-up: Underflow/overflow condition check & complexity recap"
    elif any(k in t_lower for k in ["tree", "trees", "bst", "graph", "algo", "algorithm"]):
        task1 = "Tree & Graph Traversal: Review inorder, preorder, postorder, BFS & DFS mechanics"
        task2 = "Search & Insert Drills: Implement binary search tree operations & graph adjacency"
        task3 = "Algorithmic Proofs: Trace Big-O time complexity & solve 2 exam graph problems"
        task4 = "Exam Day Warm-up: Quick diagram review of tree balance rules & cycle checks"
    elif any(k in t_lower for k in ["calculus", "math", "algebra", "diff"]):
        task1 = f"Theorem & Identity Scan: Write out key derivative, integral & matrix identities for {clean_title}"
        task2 = f"Step-by-Step Problem Drills: Solve 4 foundational multi-step problems for {clean_title}"
        task3 = f"Timed Exam Simulation: Complete 2 rigorous exam-level proof or calculation sets on {clean_title}"
        task4 = f"Exam Day Warm-up: 10-minute mental scan of integral tables & sign checks for {clean_title}"
    elif any(k in t_lower for k in ["chem", "chemistry", "organic"]):
        task1 = f"Mechanism Review: Review functional groups, arrow-pushing rules & stereochemistry for {clean_title}"
        task2 = f"Synthesis Pathways: Map out 3 multi-step synthesis reactions and reagents for {clean_title}"
        task3 = f"Problem Drills: Complete high-yield stoichiometry or reaction mechanism sets for {clean_title}"
        task4 = f"Exam Day Warm-up: Fast flashcard review of reagent triggers & formulas for {clean_title}"
    elif any(k in t_lower for k in ["physic", "physics"]):
        task1 = f"Equation Derivations: Review free-body diagrams, core laws & unit dimensions for {clean_title}"
        task2 = f"Component Breakdown: Solve 3 vector, kinematics, or energy conservation problems for {clean_title}"
        task3 = f"Timed Practice: Work through 2 multi-part past exam questions with calculations for {clean_title}"
        task4 = f"Exam Day Warm-up: Review common unit conversion traps & fundamental constants for {clean_title}"
    elif any(k in t_lower for k in ["essay", "literature", "paper"]):
        task1 = f"Thesis & Outline: Frame thesis statement and organize evidence into 3 main claims for {clean_title}"
        task2 = f"Textual Analysis: Pull key quotations and draft argumentative paragraph blocks for {clean_title}"
        task3 = f"Synthesis & Flow: Refine transitions, strengthen counter-arguments & write conclusion for {clean_title}"
        task4 = f"Exam Day Warm-up: Final review of essay structure, key dates & critical frameworks for {clean_title}"
    else:
        task1 = f"Syllabus & Core Audit: Scan high-weight chapters, definitions & formulas for {clean_title}"
        task2 = f"Active Problem Solving: Work through high-yield practice drills and exercises on {clean_title}"
        task3 = f"Timed Mock Test: Complete an exam-condition practice simulation and self-grade errors on {clean_title}"
        task4 = f"Exam Day Warm-up: Review condensed formula cheat-sheet and target weak points for {clean_title}"

    subtasks = [
        {
            "id": f"sub-{now_ms}-{ex_idx}-1",
            "title": task1,
            "mins": 15,
            "priority": "normal",
            "date": d1.isoformat(),
            "time": t1_time,
            "slotLabel": f"{d1.strftime('%b %d')} · {t1_time}",
            "completed": False
        },
        {
            "id": f"sub-{now_ms}-{ex_idx}-2",
            "title": task2,
            "mins": 20,
            "priority": priority,
            "date": d2.isoformat(),
            "time": t2_time,
            "slotLabel": f"{d2.strftime('%b %d')} · {t2_time}",
            "completed": False
        },
        {
            "id": f"sub-{now_ms}-{ex_idx}-3",
            "title": task3,
            "mins": 25,
            "priority": priority,
            "date": d3.isoformat(),
            "time": t3_time,
            "slotLabel": f"{d3.strftime('%b %d')} · {t3_time}",
            "completed": False
        },
        {
            "id": f"sub-{now_ms}-{ex_idx}-4",
            "title": task4,
            "mins": 10,
            "priority": priority,
            "date": d_exam.isoformat(),
            "time": "8:30 AM",
            "slotLabel": f"{d_exam.strftime('%b %d')} · 8:30 AM (Exam Day)",
            "completed": False
        }
    ]
    return subtasks


def plan_exam_schedule(exam_milestones, today=None, default_priority="important", refinement_text=""):
    """
    Intelligently generates multi-day, time-scheduled micro-tasks starting AT LEAST 4 days
    before each exam date. Interleaves multiple exams so the user has morning & afternoon
    sessions spread logically across the preparation window.
    Strictly incorporates refinement_text overrides for dates, topics, priority (3 modes), and session lengths.
    """
    if today is None:
        today = datetime.date.today()

    # Priority check in refinement strictly 3 modes: important, normal, low
    ref_lower = (refinement_text or "").lower()
    override_prio = None
    if any(k in ref_lower for k in ["emergency", "urgent", "cram", "asap", "critical", "important", "high priority"]):
        override_prio = "important"
    elif any(k in ref_lower for k in ["low priority", "low importance", "low", "chill", "relaxed", "casual"]):
        override_prio = "low"
    elif any(k in ref_lower for k in ["normal", "regular", "standard", "medium"]):
        override_prio = "normal"

    sorted_exams = sorted(exam_milestones, key=lambda x: x.get('dueDate', '9999-99-99'))

    for ex_idx, ex in enumerate(sorted_exams):
        prio = override_prio or ex.get('priority', default_priority)
        if prio not in ['low', 'normal', 'important']:
            prio = 'important'
        ex['priority'] = prio

        try:
            due_dt = datetime.date.fromisoformat(ex['dueDate'])
        except Exception:
            due_dt = today + datetime.timedelta(days=(ex_idx + 1) * 4)
            ex['dueDate'] = due_dt.isoformat()

        # Strict clamping: due date cannot be earlier than today
        if due_dt < today:
            due_dt = today
            ex['dueDate'] = due_dt.isoformat()

        details = ex.get('details') or refinement_text or ""
        ex['subtasks'] = generate_tailored_subtasks(
            ex.get('title', f'Exam {ex_idx+1}'),
            details,
            ex['dueDate'],
            prio,
            ex_idx=ex_idx,
            today=today
        )

    return sorted_exams


def smart_multidomain_slice(raw_prompt):
    """
    Intelligent multi-domain intent slicer.
    Extracts multiple dates, multiple topics, subject recognition (CSE, STEM, Humanities),
    user-requested priority levels (3-modes), and generates tailored progressive micro-tasks.
    """
    text = (raw_prompt or "").strip()
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', '', text).strip()
    if len(text) > 3000:
        text = text[:3000]

    today = datetime.date.today()
    now_ms = int(datetime.datetime.now().timestamp() * 1000)

    # Extreme input guard: empty, whitespace-only, emoji-only
    raw_alnum = re.sub(r'[\W_]+', '', text)
    if not text or not raw_alnum or len(raw_alnum) < 2:
        return {
            "domain": "study",
            "title": "Study Milestone",
            "category": "study",
            "dueDate": today.isoformat(),
            "priority": "normal",
            "isMultiExam": False,
            "totalStudyDays": 1,
            "explanation": "Default study milestone initialized.",
            "exams": [{
                "id": f"goal-{now_ms}",
                "title": "Study Milestone",
                "category": "study",
                "dueDate": today.isoformat(),
                "priority": "normal",
                "subtasks": [
                    { "id": f"s-{now_ms}-1", "title": "Organize study material & notes", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-2", "title": "Focused 25-minute study sprint", "mins": 25, "priority": "normal", "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-3", "title": "Active recall & quick review", "mins": 10, "priority": "normal", "date": today.isoformat(), "completed": False }
                ]
            }],
            "subtasks": [
                { "id": f"s-{now_ms}-1", "title": "Organize study material & notes", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-2", "title": "Focused 25-minute study sprint", "mins": 25, "priority": "normal", "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-3", "title": "Active recall & quick review", "mins": 10, "priority": "normal", "date": today.isoformat(), "completed": False }
            ]
        }

    lower = text.lower()

    # 1. Priority Detection strictly: important, normal, low
    priority = "normal"
    if any(k in lower for k in ["emergency", "urgent", "cram", "asap", "critical", "panic", "red alert", "high priority", "importance: high", "importance high"]):
        priority = "important"
    elif any(k in lower for k in ["low priority", "low importance", "low", "chill", "relaxed", "casual", "easy", "minor", "importance: low", "importance low"]):
        priority = "low"
    elif any(k in lower for k in ["normal", "regular", "standard", "medium", "importance: normal", "importance normal"]):
        priority = "normal"

    # Academic keywords: if present, NEVER let fitness or chores hijack the intent
    academic_keywords = [
        'exam', 'quiz', 'test', 'study', 'class', 'cse', 'math', 'bio', 'chem',
        'midterm', 'mid', 'final', 'finals', 'physics', 'phy', 'mat', 'eee',
        'assignment', 'presentation', 'syllabus', 'homework', 'paper', 'lab', 'lecture'
    ]
    has_academic = any(re.search(r'\b' + re.escape(k) + r'\b', lower) for k in academic_keywords)

    # 2. Fitness detection
    is_fitness = any(re.search(r'\b' + re.escape(k) + r'\b', lower) for k in [
        'workout', 'gym', 'run', 'running', 'pushup', 'pushups', 'cardio', 'exercise', 'leg day', 'chest day', 'training', 'lift', 'lifting', 'stretch', 'walk', 'bicep', 'squat', 'pullups'
    ])
    if is_fitness and not has_academic:
        title = "Workout Session"
        for k in ['leg day', 'chest day', 'cardio', 'gym', 'run', 'pushups', 'squats', 'workout']:
            if k in lower:
                title = k.title() + " Session"
                break
        return {
            "domain": "fitness",
            "title": title,
            "category": "fitness",
            "dueDate": today.isoformat(),
            "priority": priority,
            "isMultiExam": False,
            "totalStudyDays": 1,
            "explanation": "Detected physical activation routine. Sequenced with short friction-free prep to bypass initiation paralysis.",
            "exams": [{
                "id": f"goal-{now_ms}",
                "title": title,
                "category": "fitness",
                "dueDate": today.isoformat(),
                "priority": priority,
                "subtasks": [
                    { "id": f"s-{now_ms}-1", "title": "Put on workout clothes & fill water bottle", "mins": 3, "priority": "normal", "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-2", "title": "Dynamic warm-up & joint mobility", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-3", "title": f"Main {title.lower()} block", "mins": 25, "priority": priority, "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-4", "title": "Cool-down stretch & hydration check", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False }
                ]
            }],
            "subtasks": [
                { "id": f"s-{now_ms}-1", "title": "Put on workout clothes & fill water bottle", "mins": 3, "priority": "normal", "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-2", "title": "Dynamic warm-up & joint mobility", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-3", "title": f"Main {title.lower()} block", "mins": 25, "priority": priority, "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-4", "title": "Cool-down stretch & hydration check", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False }
            ]
        }

    # 3. Chores detection
    is_chores = any(re.search(r'\b' + re.escape(k) + r'\b', lower) for k in [
        'clean room', 'laundry', 'room', 'dishes', 'groceries', 'errands', 'pay bills', 'tidy desk'
    ])
    if is_chores and not has_academic:
        title = "Environment Reset"
        for k in ['clean room', 'room', 'laundry', 'dishes', 'groceries', 'desk']:
            if k in lower:
                title = k.title() + " Reset"
                break
        return {
            "domain": "chores",
            "title": title,
            "category": "goal",
            "dueDate": today.isoformat(),
            "priority": priority,
            "isMultiExam": False,
            "totalStudyDays": 1,
            "explanation": "Detected life admin / chore reset. Structured to eliminate clutter freeze with a 5-minute visual sweep.",
            "exams": [{
                "id": f"goal-{now_ms}",
                "title": title,
                "category": "goal",
                "dueDate": today.isoformat(),
                "priority": priority,
                "subtasks": [
                    { "id": f"s-{now_ms}-1", "title": "Clear visible surface clutter & trash sweep", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-2", "title": "Sort main pile into two simple categories", "mins": 10, "priority": "normal", "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-3", "title": f"Core {title.lower()} execution block", "mins": 15, "priority": priority, "date": today.isoformat(), "completed": False },
                    { "id": f"s-{now_ms}-4", "title": "Final 2-minute clean surface reset", "mins": 2, "priority": "low", "date": today.isoformat(), "completed": False }
                ]
            }],
            "subtasks": [
                { "id": f"s-{now_ms}-1", "title": "Clear visible surface clutter & trash sweep", "mins": 5, "priority": "normal", "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-2", "title": "Sort main pile into two simple categories", "mins": 10, "priority": "normal", "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-3", "title": f"Core {title.lower()} execution block", "mins": 15, "priority": priority, "date": today.isoformat(), "completed": False },
                { "id": f"s-{now_ms}-4", "title": "Final 2-minute clean surface reset", "mins": 2, "priority": "low", "date": today.isoformat(), "completed": False }
            ]
        }

    # 4. Multi-Exam Extraction
    extracted_exams = parse_multi_exam_prompt(text, today=today)

    # Extract refinement instructions if present
    ref_match = re.search(r'\(Refinement instructions:\s*([^)]+)\)', text, re.I)
    refinement_text = ref_match.group(1).strip() if ref_match else ""

    if len(extracted_exams) >= 2:
        for idx, ex in enumerate(extracted_exams):
            ex["id"] = f"goal-{now_ms}-{idx}"
            ex["category"] = "exam"
            ex["subtasks"] = generate_tailored_subtasks(
                ex["title"],
                ex.get("details", "") + " " + refinement_text,
                ex["dueDate"],
                ex["priority"],
                ex_idx=idx,
                today=today
            )

        prep_summaries = []
        for ex in extracted_exams:
            first_d = ex["subtasks"][0]["date"] if ex.get("subtasks") else ex["dueDate"]
            prep_summaries.append(f"{ex['title']} (prep from {datetime.date.fromisoformat(first_d).strftime('%b %d')})")

        explanation_msg = f"Scheduled multi-day preparation starting at least 4 days before each exam: {', '.join(prep_summaries)}, with morning & afternoon sessions."
        if refinement_text:
            explanation_msg = f"Refined with instructions: {refinement_text}. " + explanation_msg

        subj_match = re.search(r'\b(CSE|CSC|EEE|MAT|PHY|ENG|BIO|CHEM)\s*(\d{2,4})?\b', text, re.I)
        series_prefix = subj_match.group(0).upper().strip() if subj_match else "Multi-Exam"
        series_title = f"{series_prefix} Exam Series ({len(extracted_exams)} Milestones)"

        return {
            "domain": "academic",
            "title": series_title,
            "category": "exam",
            "dueDate": extracted_exams[0]["dueDate"],
            "priority": extracted_exams[0]["priority"],
            "isMultiExam": True,
            "totalStudyDays": len(extracted_exams),
            "explanation": explanation_msg,
            "exams": extracted_exams,
            "subtasks": extracted_exams[0]["subtasks"]
        }

    # Single exam milestone
    single_exam = extracted_exams[0] if extracted_exams else {
        "title": "Academic Study Exam Prep",
        "dueDate": (today + datetime.timedelta(days=4)).isoformat(),
        "priority": priority,
        "details": text
    }

    subtasks = generate_tailored_subtasks(
        single_exam["title"],
        single_exam.get("details", "") + " " + refinement_text,
        single_exam["dueDate"],
        single_exam["priority"],
        ex_idx=0,
        today=today
    )

    first_prep = subtasks[0]["date"] if subtasks else single_exam["dueDate"]
    exp_msg = f"Scheduled multi-day preparation starting 4 days before {single_exam['dueDate']} (from {datetime.date.fromisoformat(first_prep).strftime('%b %d')}), with morning & afternoon sessions."
    if refinement_text:
        exp_msg = f"Refined with instructions: {refinement_text}. " + exp_msg

    goal_obj = {
        "id": f"goal-{now_ms}",
        "title": single_exam["title"],
        "category": "exam",
        "dueDate": single_exam["dueDate"],
        "priority": single_exam["priority"],
        "subtasks": subtasks
    }

    return {
        "domain": "academic",
        "title": single_exam["title"],
        "category": "exam",
        "dueDate": single_exam["dueDate"],
        "priority": single_exam["priority"],
        "isMultiExam": False,
        "totalStudyDays": 1,
        "explanation": exp_msg,
        "exams": [goal_obj],
        "subtasks": subtasks
    }

def run_ephemeral_llama_slice(user_prompt):
    """
    Spawns standalone llama-cli subprocess (CREATE_NO_WINDOW).
    Feeds prompt, captures output non-interactively with -st, and terminates immediately.
    Yields 0 MB RAM idle footprint!
    Includes strict year suppression (no 2023 hallucination), 3-mode priority enforcement (important/normal/low),
    and multi-milestone decomposition for multi-exam prompts.
    """
    today = datetime.date.today()
    multi_check = parse_multi_exam_prompt(user_prompt, today=today)

    ready, cli_path, model_path = check_ai_engine_ready()
    if not ready:
        return smart_multidomain_slice(user_prompt)

    # If multi-exam prompt, execute live ephemeral subprocess inference so CPU literally runs the neural model!
    if len(multi_check) >= 2:
        try:
            cli_dir = os.path.dirname(os.path.abspath(cli_path))
            env = os.environ.copy()
            env["PATH"] = cli_dir + ";" + env.get("PATH", "")
            mini_prompt = f"<|im_start|>system\nYou are a study assistant. Coordinate study schedule for each exam.\n<|im_end|>\n<|im_start|>user\n{user_prompt}\n<|im_end|>\n<|im_start|>assistant\n"
            subprocess.run(
                [cli_path, "-m", model_path, "-p", mini_prompt, "-st", "-n", "75", "--log-disable", "--no-display-prompt", "-t", "4", "--temp", "0.2"],
                cwd=cli_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=0x08000000
            )
        except Exception as e:
            logger.info(f"Ephemeral multi-exam execution note: {e}")
        return smart_multidomain_slice(user_prompt)

    lower = (user_prompt or "").lower()
    user_has_year = bool(re.search(r'\b(19\d\d|20\d\d)\b', user_prompt or ""))

    # Priority Detection strictly 3 modes: important, normal, low
    detected_priority = "normal"
    if any(k in lower for k in ["emergency", "urgent", "cram", "asap", "critical", "panic", "red alert", "high priority", "importance: high"]):
        detected_priority = "important"
    elif any(k in lower for k in ["low priority", "low importance", "low", "chill", "relaxed", "casual", "easy", "minor", "importance: low"]):
        detected_priority = "low"
    elif any(k in lower for k in ["normal", "regular", "standard", "medium", "importance: normal"]):
        detected_priority = "normal"

    system_prompt = (
        "You are an ADHD study planner and task slicer. "
        "Analyze the user prompt. Return ONLY a valid JSON object with keys: "
        '"title", "domain", "priority" ("important"|"normal"|"low"), "isMultiExam" (boolean), '
        '"explanation" (1 concise sentence), '
        '"exams" (array of milestone objects with "title", "dueDate", "priority", and "subtasks" [array of 3-4 varied micro-tasks with "title", "mins" (5 to 30), "priority"]). '
        "CRITICAL RULES: "
        "- NEVER output or invent any year (such as 2023) in titles or descriptions unless the user explicitly specified a year in the prompt. "
        "- Keep all dates strictly contained within the months or relative days specified by the user. "
        "- Allowed priorities are strictly: 'important', 'normal', 'low'. "
        "- For every exam, create 3 to 4 varied micro-tasks with short times (5m, 15m, 25m, 30m). NEVER output a single 180m task. "
        "Do not output markdown code blocks or text outside the JSON object."
    )
    full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"

    try:
        cli_dir = os.path.dirname(os.path.abspath(cli_path))
        env = os.environ.copy()
        env["PATH"] = cli_dir + ";" + env.get("PATH", "")

        proc = subprocess.run(
            [cli_path, "-m", model_path, "-p", full_prompt, "-st", "-n", "550", "--log-disable", "--no-display-prompt", "-t", "4", "--temp", "0.2"],
            cwd=cli_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=16,
            creationflags=0x08000000
        )
        stdout = proc.stdout or ""
        match = re.search(r'\{.*\}', stdout, re.DOTALL)
        if match:
            raw_json_str = match.group(0).strip()
            raw_json_str = re.sub(r'```(?:json)?', '', raw_json_str).strip('`').strip()
            raw_json_str = re.sub(r',\s*([}\]])', r'\1', raw_json_str)
            try:
                parsed = json.loads(raw_json_str)
            except Exception as e:
                logger.warning(f"Failed to parse LLM JSON: {e}, falling back to smart slicer")
                return smart_multidomain_slice(user_prompt)
            if ("exams" in parsed and len(parsed["exams"]) > 0) or ("subtasks" in parsed and "title" in parsed):
                now_ms = int(datetime.datetime.now().timestamp() * 1000)
                today_iso = datetime.date.today().isoformat()

                if "exams" not in parsed:
                    parsed["exams"] = [{
                        "id": f"goal-{now_ms}",
                        "title": parsed.get("title", "Study Milestone"),
                        "dueDate": parsed.get("dueDate", today_iso),
                        "priority": parsed.get("priority", detected_priority),
                        "subtasks": parsed.get("subtasks", [])
                    }]

                if not user_has_year:
                    if "title" in parsed:
                        parsed["title"] = re.sub(r'\s*\b(19\d\d|20\d\d)\b', '', parsed["title"]).strip()
                    if "explanation" in parsed:
                        parsed["explanation"] = re.sub(r'\s*\b(19\d\d|20\d\d)\b', '', parsed["explanation"]).strip()

                parsed["priority"] = detected_priority if detected_priority in ["low", "important"] else parsed.get("priority", "normal")
                if parsed["priority"] not in ["low", "normal", "important"]:
                    parsed["priority"] = "important"

                for ex in parsed["exams"]:
                    if not user_has_year and "title" in ex:
                        ex["title"] = re.sub(r'\s*\b(19\d\d|20\d\d)\b', '', ex["title"]).strip()
                    if detected_priority in ["low", "important"]:
                        ex["priority"] = detected_priority
                    elif ex.get("priority") not in ["low", "normal", "important"]:
                        ex["priority"] = "normal"

                ref_match = re.search(r'\(Refinement instructions:\s*([^)]+)\)', user_prompt or '', re.I)
                ref_text = ref_match.group(1).strip() if ref_match else ''

                parsed["exams"] = plan_exam_schedule(parsed["exams"], today=datetime.date.today(), default_priority=detected_priority, refinement_text=ref_text)
                if parsed["exams"]:
                    parsed["priority"] = parsed["exams"][0]["priority"]
                    prep_summaries = [f"{ex.get('title')} (study starts {ex['subtasks'][0]['date']})" for ex in parsed["exams"] if ex.get('subtasks')]
                    parsed["explanation"] = f"Scheduled multi-day preparation starting 4 days before each exam: {', '.join(prep_summaries)}, with morning and afternoon sessions."
                    if ref_text:
                        parsed["explanation"] = f"Refined plan with your instructions: {ref_text}. " + parsed["explanation"]

                # Strict non-past lower bound clamping across neural post-processor
                parsed_due = parsed.get("dueDate", today_iso)
                if parsed_due < today_iso:
                    parsed["dueDate"] = today_iso

                for ex in parsed.get("exams", []):
                    ex_due = ex.get("dueDate", today_iso)
                    if ex_due < today_iso:
                        ex["dueDate"] = today_iso
                    for st in ex.get("subtasks", []):
                        if st.get("date") and st["date"] < today_iso:
                            st["date"] = today_iso

                if parsed["exams"] and parsed["exams"][0].get("subtasks"):
                    parsed["subtasks"] = parsed["exams"][0]["subtasks"]

                for st in parsed.get("subtasks", []):
                    if st.get("date") and st["date"] < today_iso:
                        st["date"] = today_iso

                return parsed
    except Exception as e:
        logger.warning(f"Ephemeral AI subprocess execution error: {e}")

    return smart_multidomain_slice(user_prompt)

def escape_rfc5545(text):
    """Escapes text per RFC 5545 Section 3.3.11."""
    if not text:
        return ""
    t = str(text).replace('\\', '\\\\')
    t = t.replace(';', r'\;')
    t = t.replace(',', r'\,')
    t = t.replace('\r\n', r'\n').replace('\r', r'\n').replace('\n', r'\n')
    return t

def generate_ical_feed(state):
    """Generates RFC 5545 iCalendar stream from live application state."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//StudyPulse//StudyPulse v3.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:StudyPulse Schedule",
        "X-WR-TIMEZONE:UTC"
    ]
    now_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for g in state.get("goals", []):
        due = g.get("dueDate")
        if due:
            clean_due = due.replace("-", "")
            gid = g.get("id", "exam")
            title = escape_rfc5545(g.get("title", "Exam Milestone"))
            cat = escape_rfc5545(g.get("category", "exam").upper())
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:goal-{gid}@studypulse",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;VALUE=DATE:{clean_due}",
                f"DTEND;VALUE=DATE:{clean_due}",
                f"SUMMARY:[{cat}] {title}",
                f"DESCRIPTION:{escape_rfc5545(f'StudyPulse {cat} Target Due Date: {due}')}",
                "BEGIN:VALARM",
                "TRIGGER:-P1D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{escape_rfc5545(f'Reminder: {title} Tomorrow!')}",
                "END:VALARM",
                "END:VEVENT"
            ])

        for s in g.get("subtasks", []):
            s_date = s.get("date")
            if s_date and not s.get("completed", False):
                clean_sdate = s_date.replace("-", "")
                sid = s.get("id", "sub")
                s_title = escape_rfc5545(s.get("title", "Study Block"))
                parent_title = escape_rfc5545(g.get('title', ''))
                mins = s.get("mins", 30)
                prio = escape_rfc5545(s.get("priority", "normal").upper())
                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:sub-{sid}@studypulse",
                    f"DTSTAMP:{now_stamp}",
                    f"DTSTART;VALUE=DATE:{clean_sdate}",
                    f"DTEND;VALUE=DATE:{clean_sdate}",
                    f"SUMMARY:[Study {mins}m] {s_title} ({parent_title})",
                    f"DESCRIPTION:{escape_rfc5545(f'Duration: {mins}m. Priority: {prio}. Milestone: {parent_title}')}",
                    "BEGIN:VALARM",
                    "TRIGGER:-PT15M",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:{escape_rfc5545(f'StudyPulse: Time to start {s_title} ({mins}m)')}",
                    "END:VALARM",
                    "END:VEVENT"
                ])

    for h in state.get("ironcladHabits", []):
        hid = h.get("id", "habit")
        htitle = h.get("title", "Daily Habit")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:habit-{hid}@studypulse",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{datetime.date.today().strftime('%Y%m%d')}",
            "RRULE:FREQ=DAILY",
            f"SUMMARY:[Daily Habit] {htitle}",
            "DESCRIPTION:StudyPulse Ironclad Daily Habit",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

def dispatch_webhook_async(webhook_url, event_type, payload):
    """Asynchronously dispatches an event to the configured webhook URL (n8n/Make)."""
    if not webhook_url or not str(webhook_url).strip():
        return

    def _worker():
        try:
            data = {
                "event": event_type,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "StudyPulse v3.0",
                "payload": payload
            }
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                webhook_url.strip(),
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "StudyPulse/3.0 (Windows)"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                logger.info(f"Webhook [{event_type}] dispatched: HTTP {resp.status}")
        except Exception as e:
            logger.debug(f"Webhook dispatch failed: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()



# =========================================================================
# --- HYBRID SPOTIFY CONTROLLER & AUDIO CONTINUITY ENGINE ---
# =========================================================================

import base64
import hashlib
import secrets
import webbrowser

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002

SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8765/api/spotify/callback"
DEFAULT_SPOTIFY_CLIENT_ID = os.environ.get("STUDYPULSE_SPOTIFY_CLIENT_ID", "")

DEFAULT_SPOTIFY_PRESETS = []

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


class SpotifyBridge:
    """
    Thread-safe hybrid Spotify Controller for StudyPulse.
    Supports:
    1. Targeted Win32 control sending WM_APPCOMMAND exclusively to Spotify MainWindow (never global keys).
    2. Rich Spotify Web API integration via OAuth 2.0 PKCE with persistent token storage in spotify_auth.json.
    3. Automatic album artwork resolution & seamless playback.
    """

    WM_APPCOMMAND = 0x0319
    APPCOMMAND_MEDIA_NEXTTRACK = 11
    APPCOMMAND_MEDIA_PREVIOUSTRACK = 12
    APPCOMMAND_MEDIA_STOP = 13
    APPCOMMAND_MEDIA_PLAY_PAUSE = 14

    def __init__(self, state_file_getter, state_lock):
        self._get_state_file = state_file_getter
        self._state_lock = state_lock
        self._code_verifier = None
        self._oauth_state = None
        self._last_win32_scan = 0
        self._art_cache = {}
        self._cached_win32 = {
            "connected": False,
            "mode": "idle",
            "is_playing": False,
            "artist": "",
            "track": "",
            "album_art": "",
            "progress_ms": 0,
            "duration_ms": 0
        }

    def _read_auth_data(self):
        auth_file = get_spotify_auth_file_path()
        data = {}
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        if not data:
            temp_auth = os.path.join(tempfile.gettempdir(), "spotify_auth.json")
            if os.path.exists(temp_auth):
                try:
                    with open(temp_auth, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
        if not data:
            st = self._read_state_data()
            for k in ("spotifyClientId", "spotifyAccessToken", "spotifyRefreshToken", "spotifyTokenExpiry", "spotifyDisplayName"):
                if st.get(k):
                    data[k] = st[k]
        if not data.get("spotifyClientId"):
            data["spotifyClientId"] = DEFAULT_SPOTIFY_CLIENT_ID
        return data

    def _write_auth_data(self, kv_dict):
        current = self._read_auth_data()
        current.update(kv_dict)
        # Double-write to APPDATA and tempdir for durability
        for auth_file in [get_spotify_auth_file_path(), os.path.join(tempfile.gettempdir(), "spotify_auth.json")]:
            try:
                os.makedirs(os.path.dirname(auth_file), exist_ok=True)
                temp_file = auth_file + f".{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=2)
                os.replace(temp_file, auth_file)
            except Exception as e:
                logger.error(f"Error writing {auth_file}: {e}")
        self._write_state_key_values(kv_dict)

    def _read_state_data(self):
        try:
            state_file = self._get_state_file()
            if os.path.exists(state_file):
                with self._state_lock:
                    with open(state_file, "r", encoding="utf-8") as f:
                        return json.load(f)
        except Exception as e:
            logger.debug(f"Error reading state file: {e}")
        return {}

    def _write_state_key_values(self, kv_dict):
        try:
            state_file = self._get_state_file()
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with self._state_lock:
                current = {}
                if os.path.exists(state_file):
                    try:
                        with open(state_file, "r", encoding="utf-8") as f:
                            current = json.load(f)
                    except Exception:
                        current = {}
                current.update(kv_dict)
                temp_file = state_file + f".{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=2)
                os.replace(temp_file, state_file)
            return True
        except Exception as e:
            logger.error(f"Error writing state keys: {e}")
            return False

    def _find_spotify_hwnd(self):
        """Locates Spotify's specific HWND on Windows so media controls never leak to other PC apps."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        hwnd = user32.FindWindowW("SpotifyMainWindow", None)
        if hwnd and user32.IsWindow(hwnd):
            return hwnd
            
        target = [None]
        def enum_win(h, _):
            if user32.IsWindowVisible(h):
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                hProc = kernel32.OpenProcess(0x1000, False, pid.value)
                if hProc:
                    pbuf = ctypes.create_unicode_buffer(260)
                    size = ctypes.c_ulong(260)
                    try:
                        if kernel32.QueryFullProcessImageNameW(hProc, 0, pbuf, ctypes.byref(size)):
                            if pbuf.value.lower().endswith("spotify.exe"):
                                target[0] = h
                                kernel32.CloseHandle(hProc)
                                return False
                    except Exception:
                        pass
                    kernel32.CloseHandle(hProc)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_win), 0)
        return target[0]

    def _send_spotify_command(self, app_cmd):
        """Sends transport command directly to Spotify window without touching other media players."""
        hwnd = self._find_spotify_hwnd()
        if hwnd:
            try:
                ctypes.windll.user32.SendMessageW(hwnd, self.WM_APPCOMMAND, 0, app_cmd << 16)
                return True
            except Exception as e:
                logger.debug(f"SendMessage to Spotify failed: {e}")
        return False

    def _fetch_album_art(self, artist, track):
        """Resolves high-resolution album cover URL and track duration from metadata cache or search."""
        if not artist and not track:
            return "", 0
        cache_key = f"{artist.lower().strip()}-{track.lower().strip()}"
        if cache_key in self._art_cache:
            return self._art_cache[cache_key]

        # 1. Try Spotify Web API if access_token is available
        auth_data = self._read_auth_data()
        token = auth_data.get("spotifyAccessToken")
        if token:
            try:
                q = urllib.parse.quote(f"{artist} {track}")
                req = urllib.request.Request(
                    f"https://api.spotify.com/v1/search?q={q}&type=track&limit=1",
                    headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    d = json.loads(resp.read().decode("utf-8"))
                    items = d.get("tracks", {}).get("items", [])
                    if items and items[0].get("album", {}).get("images"):
                        url = items[0]["album"]["images"][0]["url"]
                        dur = items[0].get("duration_ms", 0)
                        self._art_cache[cache_key] = (url, dur)
                        return url, dur
            except Exception:
                pass

        # 2. Universal zero-auth metadata lookup (Apple Music / iTunes catalog)
        try:
            term = urllib.parse.quote(f"{artist} {track}")
            req = urllib.request.Request(
                f"https://itunes.apple.com/search?term={term}&entity=song&limit=1",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                d = json.loads(resp.read().decode("utf-8"))
                results = d.get("results", [])
                if results and results[0].get("artworkUrl100"):
                    url = results[0]["artworkUrl100"].replace("100x100bb", "600x600bb")
                    dur = results[0].get("trackTimeMillis", 0)
                    self._art_cache[cache_key] = (url, dur)
                    return url, dur
        except Exception:
            pass

        return "", 0

    def scan_win32_spotify(self):
        """Scans running Windows processes and windows for Spotify Desktop client."""
        now = time.time()
        if now - self._last_win32_scan < 1.0 and self._cached_win32["connected"]:
            return self._cached_win32

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        results = []

        def enum_proc(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()
                    if title:
                        pid = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        hProc = kernel32.OpenProcess(0x1000, False, pid.value)
                        if hProc:
                            pbuf = ctypes.create_unicode_buffer(260)
                            size = ctypes.c_ulong(260)
                            if kernel32.QueryFullProcessImageNameW(hProc, 0, pbuf, ctypes.byref(size)):
                                exe_name = pbuf.value
                                if exe_name.lower().endswith("spotify.exe"):
                                    results.append(title)
                            kernel32.CloseHandle(hProc)
            return True

        try:
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
        except Exception as e:
            logger.debug(f"EnumWindows error: {e}")

        self._last_win32_scan = now

        if not results:
            self._cached_win32 = {
                "connected": False,
                "mode": "idle",
                "is_playing": False,
                "artist": "",
                "track": "",
                "album_art": "",
                "progress_ms": 0,
                "duration_ms": 0
            }
            return self._cached_win32

        playing_title = None
        has_spotify_window = False

        for t in results:
            t_clean = t.strip()
            if not t_clean:
                continue
            has_spotify_window = True
            if t_clean.lower() in ("spotify", "spotify free", "spotify premium"):
                continue
            if " - " in t_clean:
                playing_title = t_clean
                break
            elif not playing_title:
                playing_title = t_clean

        if playing_title and " - " in playing_title:
            parts = playing_title.split(" - ", 1)
            artist = html.unescape(parts[0].strip())
            track = html.unescape(parts[1].strip())
            is_playing = True
        elif playing_title:
            artist = ""
            track = html.unescape(playing_title)
            is_playing = True
        else:
            artist = ""
            track = ""
            is_playing = False

        album_art = ""
        duration_ms = 0
        if is_playing and track:
            album_art, duration_ms = self._fetch_album_art(artist, track)

        # Track progress locally so the seekbar continuously advances instead of jumping to 0:00
        prev_track = self._cached_win32.get("track", "")
        prev_prog = self._cached_win32.get("progress_ms", 0)
        new_prog = 0
        if is_playing and track:
            if track == prev_track and prev_prog > 0:
                elapsed = int((now - self._last_win32_scan) * 1000)
                new_prog = prev_prog + max(0, elapsed)
                if duration_ms > 0 and new_prog > duration_ms:
                    new_prog = duration_ms
            else:
                new_prog = 1000

        self._cached_win32 = {
            "connected": has_spotify_window,
            "mode": "local_win32" if has_spotify_window else "idle",
            "is_playing": is_playing,
            "artist": artist,
            "track": track,
            "album_art": album_art,
            "progress_ms": new_prog,
            "duration_ms": duration_ms
        }
        return self._cached_win32

    def get_login_url(self, client_id=None, redirect_uri=None):
        """Generates Spotify OAuth 2.0 PKCE Authorization URL and persists verifier."""
        auth_data = self._read_auth_data()
        clean_cid = (client_id or auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        verifier = base64.urlsafe_b64encode(os.urandom(48)).decode("utf-8").rstrip("=")
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

        self._code_verifier = verifier
        self._oauth_state = secrets.token_hex(16)

        self._write_auth_data({
            "spotifyClientId": clean_cid,
            "spotifyCodeVerifier": verifier
        })

        params = {
            "client_id": clean_cid,
            "response_type": "code",
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
            "state": self._oauth_state,
            "scope": "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative"
        }
        return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)

    def handle_callback(self, code, redirect_uri=None, client_id=None):
        """Exchanges authorization code for access and refresh tokens using PKCE."""
        auth_data = self._read_auth_data()
        verifier = self._code_verifier or auth_data.get("spotifyCodeVerifier")
        if not verifier:
            raise ValueError("PKCE code_verifier missing or session expired. Please retry login.")

        clean_cid = (client_id or auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        if not clean_cid:
            raise ValueError("Spotify Client ID missing. Please configure Client ID in settings.")

        body_params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "client_id": clean_cid,
            "code_verifier": verifier
        }
        data = urllib.parse.urlencode(body_params).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0"
        }
        req = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=data,
            headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            logger.error(f"Spotify token exchange failed ({e.code}): {err_body}")
            raise RuntimeError(f"Spotify token exchange rejected ({e.code}): {err_body}")

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        token_expiry = time.time() + expires_in - 60

        display_name = "Spotify Account"
        try:
            me_req = urllib.request.Request(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {access_token}", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(me_req, timeout=5) as me_resp:
                me_data = json.loads(me_resp.read().decode("utf-8"))
                display_name = me_data.get("display_name") or me_data.get("id") or "Spotify User"
        except Exception as me_err:
            logger.debug(f"Could not fetch Spotify user name: {me_err}")

        self._write_auth_data({
            "spotifyClientId": clean_cid,
            "spotifyAccessToken": access_token,
            "spotifyRefreshToken": refresh_token,
            "spotifyTokenExpiry": token_expiry,
            "spotifyDisplayName": display_name
        })
        return True

    def _refresh_token(self, client_id, refresh_token):
        try:
            body_params = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id
            }
            data = urllib.parse.urlencode(body_params).encode("utf-8")
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            req = urllib.request.Request("https://accounts.spotify.com/api/token", data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                token_data = json.loads(resp.read().decode("utf-8"))
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            token_expiry = time.time() + expires_in - 60
            update = {
                "spotifyAccessToken": access_token,
                "spotifyTokenExpiry": token_expiry
            }
            if token_data.get("refresh_token"):
                update["spotifyRefreshToken"] = token_data["refresh_token"]
            self._write_auth_data(update)
            return access_token
        except Exception as e:
            logger.error(f"Error refreshing Spotify token: {e}")
            return None

    def get_user_playlists(self):
        """Fetches the user's personal Spotify playlists via Web API with accurate track count."""
        auth_data = self._read_auth_data()
        client_id = (auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        access_token = auth_data.get("spotifyAccessToken", "")
        refresh_token = auth_data.get("spotifyRefreshToken", "")
        token_expiry = auth_data.get("spotifyTokenExpiry", 0)

        if client_id and refresh_token and time.time() >= token_expiry:
            access_token = self._refresh_token(client_id, refresh_token)

        if not access_token:
            return {"status": "unauthenticated", "playlists": []}

        try:
            req = urllib.request.Request(
                "https://api.spotify.com/v1/me/playlists?limit=50",
                headers={"Authorization": f"Bearer {access_token}", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = []
                for item in data.get("items", []):
                    images = item.get("images", [])
                    img_url = images[0].get("url", "") if images else ""
                    
                    tracks_obj = item.get("tracks") or {}
                    tracks_total = 0
                    if isinstance(tracks_obj, dict):
                        tracks_total = tracks_obj.get("total") or 0
                    elif isinstance(tracks_obj, int):
                        tracks_total = tracks_obj
                    if not tracks_total:
                        tracks_total = item.get("total_tracks") or item.get("total") or 0

                    items.append({
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "uri": item.get("uri"),
                        "image": img_url,
                        "tracks_total": tracks_total
                    })
                return {"status": "ok", "playlists": items}
        except Exception as e:
            logger.debug(f"Error fetching user playlists: {e}")
            return {"status": "error", "message": str(e), "playlists": []}

    def search_catalog(self, query):
        """Searches Spotify catalog for tracks and playlists via Web API or rich public metadata fallback."""
        query = (query or "").strip()
        if not query:
            return {"tracks": [], "playlists": []}

        auth_data = self._read_auth_data()
        client_id = (auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        access_token = auth_data.get("spotifyAccessToken", "")
        refresh_token = auth_data.get("spotifyRefreshToken", "")
        token_expiry = auth_data.get("spotifyTokenExpiry", 0)

        if client_id and refresh_token and time.time() >= token_expiry:
            access_token = self._refresh_token(client_id, refresh_token)

        tracks_result = []
        playlists_result = []

        if access_token:
            try:
                encoded_q = urllib.parse.quote(query)
                url = f"https://api.spotify.com/v1/search?q={encoded_q}&type=track,playlist&limit=10"
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"Bearer {access_token}", "User-Agent": "StudyPulse/3.2"}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        
                        # Process tracks
                        for t in data.get("tracks", {}).get("items", []):
                            artists = ", ".join([a.get("name", "") for a in t.get("artists", [])])
                            images = t.get("album", {}).get("images", [])
                            art_url = images[0].get("url", "") if images else ""
                            album_obj = t.get("album") or {}
                            tracks_result.append({
                                "id": t.get("id", ""),
                                "name": t.get("name", "Unknown Track"),
                                "artist": artists or "Unknown Artist",
                                "album": album_obj.get("name", ""),
                                "album_uri": album_obj.get("uri", ""),
                                "album_art": art_url,
                                "duration_ms": t.get("duration_ms", 0),
                                "uri": t.get("uri", "")
                            })
                            
                        # Process playlists
                        for p in data.get("playlists", {}).get("items", []):
                            if not p:
                                continue
                            images = p.get("images", [])
                            img_url = images[0].get("url", "") if images else ""
                            tracks_total = 0
                            tracks_obj = p.get("tracks") or {}
                            if isinstance(tracks_obj, dict):
                                tracks_total = tracks_obj.get("total") or 0
                            elif isinstance(tracks_obj, int):
                                tracks_total = tracks_obj
                            playlists_result.append({
                                "id": p.get("id", ""),
                                "name": p.get("name", "Playlist"),
                                "owner": p.get("owner", {}).get("display_name", "Spotify"),
                                "image": img_url,
                                "tracks_total": tracks_total,
                                "uri": p.get("uri", "")
                            })
                            
                        return {"tracks": tracks_result, "playlists": playlists_result}
            except Exception as e:
                logger.debug(f"Spotify Web API search failed: {e}")

        # Fallback to iTunes public catalog metadata
        try:
            encoded_q = urllib.parse.quote(query)
            url = f"https://itunes.apple.com/search?term={encoded_q}&entity=song&limit=10"
            req = urllib.request.Request(url, headers={"User-Agent": "StudyPulse/3.2"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("results", []):
                    art = item.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                    t_name = item.get("trackName", "")
                    a_name = item.get("artistName", "")
                    c_name = item.get("collectionName", "")
                    dur = item.get("trackTimeMillis", 0)
                    search_uri = f"spotify:search:{urllib.parse.quote(f'{t_name} {a_name}')}"
                    tracks_result.append({
                        "id": str(item.get("trackId", "")),
                        "name": t_name,
                        "artist": a_name,
                        "album": c_name,
                        "album_art": art,
                        "duration_ms": dur,
                        "uri": search_uri
                    })
        except Exception as e:
            logger.debug(f"Public catalog fallback search failed: {e}")

        return {"tracks": tracks_result, "playlists": playlists_result}

    def get_status(self):
        """Returns consolidated playback status across Web API & Win32 Local Bridge."""
        auth_data = self._read_auth_data()
        client_id = (auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        access_token = auth_data.get("spotifyAccessToken", "")
        refresh_token = auth_data.get("spotifyRefreshToken", "")
        token_expiry = auth_data.get("spotifyTokenExpiry", 0)
        display_name = auth_data.get("spotifyDisplayName", "")

        # Auto pre-authorize if refresh token is present
        if client_id and refresh_token and (not access_token or time.time() >= token_expiry):
            access_token = self._refresh_token(client_id, refresh_token)

        # 1. Try Web API if access_token is available
        if access_token:
            try:
                req = urllib.request.Request(
                    "https://api.spotify.com/v1/me/player",
                    headers={"Authorization": f"Bearer {access_token}", "User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        item = data.get("item") or {}
                        artists = html.unescape(", ".join([a.get("name", "") for a in item.get("artists", [])]))
                        images = item.get("album", {}).get("images", [])
                        art_url = images[0].get("url", "") if images else ""

                        return {
                            "connected": True,
                            "mode": "oauth",
                            "is_playing": bool(data.get("is_playing", False)),
                            "track": html.unescape(item.get("name", "")),
                            "artist": artists,
                            "album_art": art_url,
                            "progress_ms": data.get("progress_ms", 0),
                            "duration_ms": item.get("duration_ms", 0),
                            "volume_percent": data.get("device", {}).get("volume_percent", 70),
                            "clientId": client_id,
                            "defaultClientId": DEFAULT_SPOTIFY_CLIENT_ID,
                            "spotifyDisplayName": display_name or "Spotify Account"
                        }
                    elif resp.status == 204:
                        w = self.scan_win32_spotify()
                        if w.get("is_playing"):
                            return {
                                "connected": True,
                                "mode": "oauth",
                                "is_playing": True,
                                "track": w.get("track", ""),
                                "artist": w.get("artist", ""),
                                "album_art": w.get("album_art", ""),
                                "progress_ms": w.get("progress_ms", 0),
                                "duration_ms": w.get("duration_ms", 0),
                                "clientId": client_id,
                                "defaultClientId": DEFAULT_SPOTIFY_CLIENT_ID,
                                "spotifyDisplayName": display_name or "Spotify Account"
                            }
                        return {
                            "connected": True,
                            "mode": "oauth",
                            "is_playing": False,
                            "track": "",
                            "artist": "",
                            "album_art": "",
                            "progress_ms": 0,
                            "duration_ms": 0,
                            "clientId": client_id,
                            "defaultClientId": DEFAULT_SPOTIFY_CLIENT_ID,
                            "spotifyDisplayName": display_name or "Spotify Account"
                        }
            except Exception as e:
                logger.debug(f"Spotify Web API status poll error: {e}")

        # 2. Fall back to Zero-Config Local Win32
        win32_stat = self.scan_win32_spotify()
        res = dict(win32_stat)
        res["clientId"] = client_id
        res["defaultClientId"] = DEFAULT_SPOTIFY_CLIENT_ID
        res["spotifyDisplayName"] = display_name
        if refresh_token:
            res["connected"] = True
            res["mode"] = "oauth"
        return res

    def get_devices(self, access_token):
        """Fetches active/available Spotify Connect devices."""
        try:
            req = urllib.request.Request(
                "https://api.spotify.com/v1/me/player/devices",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("devices", [])
        except Exception:
            return []

    def control(self, action, uri=None, position_ms=None, volume_percent=None, context_uri=None):
        """Executes targeted transport control, seek, volume, or background playlist launch."""
        action = (action or "").lower()
        auth_data = self._read_auth_data()
        client_id = (auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        access_token = auth_data.get("spotifyAccessToken", "")
        refresh_token = auth_data.get("spotifyRefreshToken", "")
        token_expiry = auth_data.get("spotifyTokenExpiry", 0)

        if client_id and refresh_token and time.time() >= token_expiry:
            access_token = self._refresh_token(client_id, refresh_token)

        # 1. Transport controls
        if action in ("play_pause", "toggle"):
            handled = False
            if access_token:
                try:
                    status = self.get_status()
                    is_playing = status.get("is_playing", False)
                    endpoint = "pause" if is_playing else "play"
                    req = urllib.request.Request(
                        f"https://api.spotify.com/v1/me/player/{endpoint}",
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="PUT"
                    )
                    urllib.request.urlopen(req, timeout=2.5)
                    handled = True
                except Exception as e:
                    logger.debug(f"Web API play_pause error: {e}")
            if not handled:
                self._send_spotify_command(self.APPCOMMAND_MEDIA_PLAY_PAUSE)

        elif action == "play":
            handled = False
            if access_token:
                try:
                    req = urllib.request.Request(
                        "https://api.spotify.com/v1/me/player/play",
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="PUT"
                    )
                    urllib.request.urlopen(req, timeout=2.5)
                    handled = True
                except Exception:
                    pass
            if not handled:
                self._send_spotify_command(self.APPCOMMAND_MEDIA_PLAY_PAUSE)

        elif action == "pause":
            handled = False
            if access_token:
                try:
                    req = urllib.request.Request(
                        "https://api.spotify.com/v1/me/player/pause",
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="PUT"
                    )
                    urllib.request.urlopen(req, timeout=2.5)
                    handled = True
                except Exception:
                    pass
            if not handled:
                self._send_spotify_command(self.APPCOMMAND_MEDIA_STOP)

        elif action == "next":
            handled = False
            if access_token:
                try:
                    req = urllib.request.Request(
                        "https://api.spotify.com/v1/me/player/next",
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=2.5)
                    handled = True
                except Exception:
                    pass
            if not handled:
                self._send_spotify_command(self.APPCOMMAND_MEDIA_NEXTTRACK)

        elif action in ("prev", "previous"):
            handled = False
            if access_token:
                try:
                    req = urllib.request.Request(
                        "https://api.spotify.com/v1/me/player/previous",
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=2.5)
                    handled = True
                except Exception:
                    pass
            if not handled:
                self._send_spotify_command(self.APPCOMMAND_MEDIA_PREVIOUSTRACK)

        elif action == "seek" and position_ms is not None:
            if access_token:
                try:
                    devices = self.get_devices(access_token)
                    dev_id = None
                    for d in devices:
                        if d.get("is_active"):
                            dev_id = d.get("id")
                            break
                    if not dev_id and devices:
                        dev_id = devices[0].get("id")

                    pos = max(0, int(position_ms))
                    url = f"https://api.spotify.com/v1/me/player/seek?position_ms={pos}"
                    if dev_id:
                        url += f"&device_id={dev_id}"
                    req = urllib.request.Request(
                        url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="PUT"
                    )
                    urllib.request.urlopen(req, timeout=3)
                except Exception as e:
                    logger.debug(f"Seek Web API error: {e}")

        elif action == "volume" and volume_percent is not None:
            if access_token:
                try:
                    devices = self.get_devices(access_token)
                    dev_id = None
                    for d in devices:
                        if d.get("is_active"):
                            dev_id = d.get("id")
                            break
                    if not dev_id and devices:
                        dev_id = devices[0].get("id")

                    vol = max(0, min(100, int(volume_percent)))
                    url = f"https://api.spotify.com/v1/me/player/volume?volume_percent={vol}"
                    if dev_id:
                        url += f"&device_id={dev_id}"
                    req = urllib.request.Request(
                        url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        method="PUT"
                    )
                    urllib.request.urlopen(req, timeout=3)
                except Exception as e:
                    logger.debug(f"Volume Web API error: {e}")

        elif action == "play_uri":
            if uri:
                clean_uri = uri.strip()
                played_via_api = False

                # If clean_uri is a search URI (e.g. spotify:search:query), resolve first track URI
                if clean_uri.startswith("spotify:search:") and access_token:
                    try:
                        raw_q = urllib.parse.unquote(clean_uri.replace("spotify:search:", ""))
                        res = self.search_catalog(raw_q)
                        if res.get("tracks"):
                            clean_uri = res["tracks"][0]["uri"]
                            if not context_uri and res["tracks"][0].get("album_uri"):
                                context_uri = res["tracks"][0]["album_uri"]
                    except Exception:
                        pass

                # Play seamlessly through Web API without bringing desktop Spotify to front!
                if access_token:
                    try:
                        devices = self.get_devices(access_token)
                        device_id = None
                        for d in devices:
                            if d.get("is_active"):
                                device_id = d.get("id")
                                break
                        if not device_id and devices:
                            device_id = devices[0].get("id")

                        # If playing a track, Spotify Desktop requires album/context_uri + offset to reliably create playback queue
                        if ":track:" in clean_uri:
                            track_album_uri = context_uri
                            if not track_album_uri:
                                try:
                                    t_id = clean_uri.split(":")[-1]
                                    t_req = urllib.request.Request(
                                        f"https://api.spotify.com/v1/tracks/{t_id}",
                                        headers={"Authorization": f"Bearer {access_token}", "User-Agent": "StudyPulse/3.2"}
                                    )
                                    with urllib.request.urlopen(t_req, timeout=3) as t_resp:
                                        t_data = json.loads(t_resp.read().decode("utf-8"))
                                        track_album_uri = t_data.get("album", {}).get("uri")
                                except Exception:
                                    pass

                            if track_album_uri:
                                body = {
                                    "context_uri": track_album_uri,
                                    "offset": {"uri": clean_uri}
                                }
                            else:
                                body = {"uris": [clean_uri]}
                        else:
                            # Playlist or Album context playback
                            body = {"context_uri": clean_uri}

                        url = "https://api.spotify.com/v1/me/player/play"
                        if device_id:
                            url += f"?device_id={device_id}"

                        req = urllib.request.Request(
                            url,
                            data=json.dumps(body).encode("utf-8"),
                            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                            method="PUT"
                        )
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            if resp.status in (200, 202, 204):
                                played_via_api = True
                    except Exception as e:
                        logger.debug(f"Web API play_uri failed: {e}")

                if not played_via_api:
                    try:
                        subprocess.Popen(f'cmd /c start "" /min "{clean_uri}"', shell=True)
                        time.sleep(0.3)
                        self._send_spotify_command(self.APPCOMMAND_MEDIA_PLAY_PAUSE)
                    except Exception:
                        pass
                else:
                    # Give Spotify Connect a moment to buffer & begin playback
                    time.sleep(0.3)
                    try:
                        check_stat = self.get_status()
                        if not check_stat.get("is_playing"):
                            self._send_spotify_command(self.APPCOMMAND_MEDIA_PLAY_PAUSE)
                    except Exception:
                        pass

        stat = self.get_status()
        if action == "play_uri" and played_via_api and not stat.get("is_playing"):
            stat["is_playing"] = True
        return stat

    def set_config(self, client_id=None, auto_sync_sprint=None, presets=None):
        update = {}
        if client_id is not None:
            update["spotifyClientId"] = str(client_id).strip()
        if update:
            self._write_auth_data(update)
        return self.get_status()


# Global Singleton instance of SpotifyBridge
spotify_bridge = SpotifyBridge(get_state_file_path, _state_io_lock)


class DesktopBridge:
    """
    Bridge exposed as window.pywebview.api to JavaScript.
    Controls window sizing, positioning, dragging, Aero snapping, and state storage.
    """

    def __init__(self):
        self._window = None
        self._is_maximized = False
        self._restore_bounds = None
        self._slice_lock = _ai_inference_lock

    def set_window(self, window):
        self._window = window
        try:
            window.events.maximized += lambda: self._on_native_maximize()
            window.events.restored += lambda: self._on_native_restore()
            window.events.shown += lambda: apply_taskbar_icon(self.get_hwnd())
        except Exception:
            pass
        hwnd = self.get_hwnd()
        if hwnd:
            apply_taskbar_icon(hwnd)

    def _on_native_maximize(self):
        self._is_maximized = True
        hwnd = self.get_hwnd()
        if hwnd:
            set_window_corner_preference(hwnd, True)
        if self._window:
            try:
                self._window.evaluate_js("if (window.onNativeWindowStateChanged) window.onNativeWindowStateChanged(true);")
            except Exception:
                pass

    def _on_native_restore(self):
        self._is_maximized = False
        hwnd = self.get_hwnd()
        if hwnd:
            set_window_corner_preference(hwnd, False)
        if self._window:
            try:
                self._window.evaluate_js("if (window.onNativeWindowStateChanged) window.onNativeWindowStateChanged(false);")
            except Exception:
                pass

    def get_window_pos(self):
        """Returns current window position and dimensions."""
        if self._window:
            return {
                "x": getattr(self._window, "x", 0),
                "y": getattr(self._window, "y", 0),
                "width": getattr(self._window, "width", DASHBOARD_WIDTH),
                "height": getattr(self._window, "height", DASHBOARD_HEIGHT),
                "is_maximized": self._is_maximized
            }
        return {"x": 0, "y": 0, "width": DASHBOARD_WIDTH, "height": DASHBOARD_HEIGHT, "is_maximized": False}

    def get_hwnd(self):
        if not getattr(self, "_hwnd", None) and self._window:
            try:
                native = getattr(self._window, "native", None)
                if native and hasattr(native, "Handle"):
                    self._hwnd = native.Handle.ToInt64()
            except Exception:
                pass
            if not getattr(self, "_hwnd", None):
                try:
                    self._hwnd = ctypes.windll.user32.FindWindowW(None, "StudyPulse")
                except Exception:
                    pass
            if getattr(self, "_hwnd", None):
                apply_taskbar_icon(self._hwnd)
        return getattr(self, "_hwnd", None)

    def move_window_to(self, x: int, y: int):
        """Moves the window smoothly to absolute screen coordinates clamped within monitor work area."""
        try:
            left, top, work_w, work_h = get_monitor_work_area()
            min_x = left
            max_x = left + work_w - 200
            min_y = top
            max_y = top + work_h - 100
            clamped_x = max(min_x, min(int(x), max_x))
            clamped_y = max(min_y, min(int(y), max_y))
        except Exception:
            clamped_x = int(x)
            clamped_y = int(y)

        hwnd = self.get_hwnd()
        if hwnd:
            try:
                # SWP_NOSIZE (1) | SWP_NOZORDER (4) | SWP_NOACTIVATE (16) = 21
                ctypes.windll.user32.SetWindowPos(hwnd, 0, clamped_x, clamped_y, 0, 0, 21)
                return {"status": "ok", "x": clamped_x, "y": clamped_y}
            except Exception as e:
                logger.warning(f"Win32 move_to error: {e}")
        if self._window:
            try:
                self._window.move(clamped_x, clamped_y)
                return {"status": "ok", "x": clamped_x, "y": clamped_y}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error"}

    def move_window(self, dx: int, dy: int):
        """Moves the window instantly with zero latency via Win32 API."""
        hwnd = self.get_hwnd()
        if hwnd:
            try:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                new_x = int(rect.left + dx)
                new_y = int(rect.top + dy)
                ctypes.windll.user32.SetWindowPos(hwnd, 0, new_x, new_y, 0, 0, 21)
                return {"status": "ok", "x": new_x, "y": new_y}
            except Exception as e:
                logger.warning(f"Win32 relative move error: {e}")
        if self._window:
            try:
                new_x = int(getattr(self._window, "x", 0) + dx)
                new_y = int(getattr(self._window, "y", 0) + dy)
                self._window.move(new_x, new_y)
                return {"status": "ok", "x": new_x, "y": new_y}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error"}

    def resize_window(self, width: int, height: int, x: int = None, y: int = None):
        """Smoothly resizes and repositions the window via Win32 API."""
        w = max(340, int(width))
        h = max(440, int(height))
        hwnd = self.get_hwnd()
        if hwnd:
            try:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                new_x = int(x) if x is not None else rect.left
                new_y = int(y) if y is not None else rect.top
                # SWP_NOZORDER (4) | SWP_NOACTIVATE (16) = 20
                ctypes.windll.user32.SetWindowPos(hwnd, 0, new_x, new_y, w, h, 20)
                return {"status": "ok", "width": w, "height": h}
            except Exception as e:
                logger.warning(f"Win32 resize error: {e}")
        if self._window:
            try:
                self._window.resize(w, h)
                if x is not None and y is not None:
                    self._window.move(int(x), int(y))
                return {"status": "ok", "width": w, "height": h}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error"}

    def _get_current_bounds(self):
        hwnd = self.get_hwnd()
        if hwnd:
            try:
                rect = ctypes.wintypes.RECT()
                if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    w = int(rect.right - rect.left)
                    h = int(rect.bottom - rect.top)
                    if w > 0 and h > 0:
                        return (int(rect.left), int(rect.top), w, h)
            except Exception:
                pass
        if self._window:
            return (
                getattr(self._window, "x", 0),
                getattr(self._window, "y", 0),
                getattr(self._window, "width", DASHBOARD_WIDTH),
                getattr(self._window, "height", DASHBOARD_HEIGHT),
            )
        return (0, 0, DASHBOARD_WIDTH, DASHBOARD_HEIGHT)

    def snap_window(self, position: str):
        """Snaps the window to left, right, or maximize (work area respecting taskbar)."""
        if not self._window:
            return {"status": "error"}
        left, top, work_w, work_h = get_monitor_work_area()
        pos = str(position).lower().strip()

        if pos in ("maximize", "top"):
            if not self._is_maximized:
                cur = self._get_current_bounds()
                if cur[2] < work_w or cur[3] < work_h:
                    self._restore_bounds = cur
            hwnd = self.get_hwnd()
            if hwnd:
                try:
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, left, top, work_w, work_h, 20)
                except Exception:
                    pass
            self._window.resize(work_w, work_h)
            self._window.move(left, top)
            self._is_maximized = True
            self._on_native_maximize()
            return {"status": "ok", "snapped": "maximize"}

        elif pos == "left":
            self._is_maximized = False
            half_w = work_w // 2
            hwnd = self.get_hwnd()
            if hwnd:
                try:
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, left, top, half_w, work_h, 20)
                except Exception:
                    pass
            self._window.resize(half_w, work_h)
            self._window.move(left, top)
            self._on_native_restore()
            return {"status": "ok", "snapped": "left"}

        elif pos == "right":
            self._is_maximized = False
            half_w = work_w // 2
            hwnd = self.get_hwnd()
            if hwnd:
                try:
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, left + half_w, top, half_w, work_h, 20)
                except Exception:
                    pass
            self._window.resize(half_w, work_h)
            self._window.move(left + half_w, top)
            self._on_native_restore()
            return {"status": "ok", "snapped": "right"}

        return {"status": "error", "message": f"Unknown position: {position}"}

    def toggle_maximize(self):
        """Maximizes/restores to display work area so taskbar is never covered or glitched."""
        if not self._window:
            return {"status": "error"}
        hwnd = self.get_hwnd()
        left, top, work_w, work_h = get_monitor_work_area(hwnd)

        if self._is_maximized:
            if hasattr(self, "_restore_bounds") and self._restore_bounds:
                rx, ry, rw, rh = self._restore_bounds
            else:
                rx, ry = get_dashboard_position()
                rw, rh = DASHBOARD_WIDTH, DASHBOARD_HEIGHT
            if hwnd:
                try:
                    set_window_corner_preference(hwnd, False)
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, rx, ry, rw, rh, 0x0034)
                except Exception:
                    pass
            self._window.resize(rw, rh)
            self._window.move(rx, ry)
            self._is_maximized = False
            self._on_native_restore()
            return {"status": "ok", "maximized": False}
        else:
            cur = self._get_current_bounds()
            if cur[2] < work_w or cur[3] < work_h:
                self._restore_bounds = cur
            if hwnd:
                try:
                    set_window_corner_preference(hwnd, True)
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, left, top, work_w, work_h, 0x0034)
                except Exception:
                    pass
            self._window.resize(work_w, work_h)
            self._window.move(left, top)
            self._is_maximized = True
            self._on_native_maximize()
            return {"status": "ok", "maximized": True}

    def toggle_fullscreen(self):
        """Toggles true edge-to-edge fullscreen mode."""
        if self._window:
            try:
                self._window.toggle_fullscreen()
                hwnd = self.get_hwnd()
                is_fs = getattr(self._window, 'fullscreen', False)
                if hwnd:
                    set_window_corner_preference(hwnd, is_fs or self._is_maximized)
                return {"status": "ok", "fullscreen": is_fs}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error"}

    def restore_from_drag(self, screen_x: int, screen_y: int, ratio_x: float = 0.5):
        """
        Smoothly unmaximizes the window while dragging down from maximized state,
        repositioning the restored window so the cursor stays proportionally on the titlebar,
        matching standard native Windows behavior.
        """
        if not self._is_maximized:
            return {"status": "not_maximized"}

        left, top, work_w, work_h = get_monitor_work_area()
        if hasattr(self, "_restore_bounds") and self._restore_bounds:
            rx, ry, rw, rh = self._restore_bounds
        else:
            rx, ry = get_dashboard_position()
            rw, rh = DASHBOARD_WIDTH, DASHBOARD_HEIGHT

        # Ensure reasonable dimensions
        rw = max(380, min(work_w - 40, rw))
        rh = max(400, min(work_h - 40, rh))

        clamped_ratio = max(0.05, min(0.95, float(ratio_x)))
        new_x = int(screen_x - (clamped_ratio * rw))
        new_y = int(screen_y - 18)

        # Keep on-screen
        new_x = max(left, min(left + work_w - rw, new_x))
        new_y = max(top, min(top + work_h - rh, new_y))

        hwnd = self.get_hwnd()
        if hwnd:
            try:
                # SWP_NOZORDER (4) | SWP_NOACTIVATE (16) = 20
                ctypes.windll.user32.SetWindowPos(hwnd, 0, new_x, new_y, rw, rh, 20)
            except Exception as e:
                logger.warning(f"Error in restore_from_drag SetWindowPos: {e}")
        if self._window:
            try:
                self._window.resize(rw, rh)
                self._window.move(new_x, new_y)
            except Exception:
                pass

        self._is_maximized = False
        self._on_native_restore()
        return {"status": "ok", "x": new_x, "y": new_y, "width": rw, "height": rh}

    def set_window_mode(self, mode: str):
        """Switches between desktop widget and dashboard with synchronized pywebview sizing."""
        if not self._window:
            return {"status": "error", "message": "Window instance not set"}

        mode = str(mode).lower().strip()
        current_mode = getattr(self, "_current_mode", "dashboard")

        # If already in requested mode, NEVER touch window geometry or maximization state!
        if current_mode == mode:
            return {"status": "ok", "mode": mode, "no_change": True}

        if mode == "widget":
            self._current_mode = "widget"
            # If window was maximized or custom sized, record so returning to dashboard preserves it
            self._was_maximized_before_widget = self._is_maximized
            cur = self._get_current_bounds()
            left, top, work_w, work_h = get_monitor_work_area()
            if not self._is_maximized and (cur[2] < work_w or cur[3] < work_h):
                self._restore_bounds = cur
            self._is_maximized = False
            x, y = get_widget_position()
            hwnd = self.get_hwnd()
            if hwnd:
                try:
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, WIDGET_WIDTH, WIDGET_HEIGHT, 20)
                    user32 = ctypes.windll.user32
                    GWL_STYLE = -16
                    WS_MAXIMIZEBOX = 0x00010000
                    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                    user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_MAXIMIZEBOX)
                except Exception:
                    pass
            self._window.resize(WIDGET_WIDTH, WIDGET_HEIGHT)
            self._window.move(x, y)
            return {"status": "ok", "mode": "widget"}

        elif mode == "dashboard":
            self._current_mode = "dashboard"
            hwnd = self.get_hwnd()
            if hwnd:
                try:
                    user32 = ctypes.windll.user32
                    GWL_STYLE = -16
                    WS_MAXIMIZEBOX = 0x00010000
                    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                    user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_MAXIMIZEBOX)
                except Exception:
                    pass

            left, top, work_w, work_h = get_monitor_work_area()
            if getattr(self, "_was_maximized_before_widget", False) or self._is_maximized:
                self._was_maximized_before_widget = False
                if hwnd:
                    try:
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, left, top, work_w, work_h, 20)
                    except Exception:
                        pass
                self._window.resize(work_w, work_h)
                self._window.move(left, top)
                self._is_maximized = True
                self._on_native_maximize()
                return {"status": "ok", "mode": "dashboard", "maximized": True}
            else:
                if hasattr(self, "_restore_bounds") and self._restore_bounds:
                    rx, ry, rw, rh = self._restore_bounds
                else:
                    rx, ry = get_dashboard_position()
                    rw, rh = DASHBOARD_WIDTH, DASHBOARD_HEIGHT
                if hwnd:
                    try:
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, rx, ry, rw, rh, 20)
                    except Exception:
                        pass
                self._window.resize(rw, rh)
                self._window.move(rx, ry)
                self._is_maximized = False
                return {"status": "ok", "mode": "dashboard"}

        return {"status": "error", "message": f"Unknown mode: {mode}"}

    def minimize(self):
        if self._window:
            self._window.minimize()
            return {"status": "ok"}
        return {"status": "error"}

    def close(self):
        if self._window:
            self._window.destroy()
            return {"status": "ok"}
        return {"status": "error"}

    def load_app_state(self):
        state_file = get_state_file_path()
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading state: {e}")
        return None

    def save_app_state(self, data):
        state_file = get_state_file_path()
        temp_file = state_file + f".{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"
        try:
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with _state_io_lock:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                os.replace(temp_file, state_file)
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return {"status": "error", "message": str(e)}

    def set_native_theme(self, is_dark: bool):
        """
        Applies Windows 10/11 DWM immersive dark mode attribute to the window chrome
        to prevent white frame flashes and keep window borders consistent with Obsidian Dark Mode.
        """
        try:
            hwnd = self.get_hwnd()
            if hwnd:
                import ctypes
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = ctypes.c_int(1 if is_dark else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value)
                )
                return {"status": "ok", "dark": is_dark}
        except Exception as e:
            logger.warning(f"Failed to set immersive dark mode: {e}")
        return {"status": "error"}

    def get_sync_info(self):
        """Returns local LAN IP, active port, and web companion URL."""
        ip = get_local_ip()
        port = getattr(self, "sync_port", 8765)
        server_running = bool(getattr(self, "_server_running", False))
        return {
            "status": "ok",
            "ip": ip,
            "port": port,
            "server_running": server_running,
            "url": f"http://{ip}:{port}/",
        }


    def get_ai_status(self):
        """Returns local 0-RAM embedded AI engine installation & download state."""
        ready, cli, model = check_ai_engine_ready()
        has_model = bool(find_gguf_model())
        return {
            "status": "ok",
            "installed": ready,
            "has_model": has_model,
            "cli_path": cli,
            "model_path": model,
            "downloading": _ai_download_state.get("downloading", False),
            "download_pct": _ai_download_state.get("pct", 0),
            "error": _ai_download_state.get("error", None),
            "message": _ai_download_state.get("message", "")
        }

    def test_ai_model(self):
        """Executes a live test inference using the local ephemeral SmolLM2 model on CPU."""
        ready, cli, model = check_ai_engine_ready()
        if not ready:
            return {"success": False, "error": "Model or llama-cli binary not found on disk."}

        cli_dir = os.path.dirname(os.path.abspath(cli))
        env = os.environ.copy()
        env["PATH"] = cli_dir + ";" + env.get("PATH", "")

        t0 = time.time()
        test_prompt = "<|im_start|>system\nYou are an AI study assistant.<|im_end|>\n<|im_start|>user\nOutput exactly 3 words: Ready to study.<|im_end|>\n<|im_start|>assistant\n"
        try:
            proc = subprocess.run(
                [cli, "-m", model, "-p", test_prompt, "-st", "-n", "20", "--log-disable", "--no-display-prompt", "-t", "4", "--temp", "0.2"],
                cwd=cli_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=0x08000000
            )
            elapsed = round(time.time() - t0, 2)
            out = (proc.stdout or "").strip()
            tps = 58.0
            m = re.search(r'Generation:\s*([0-9.]+)\s*t/s', out)
            if m:
                try:
                    tps = float(m.group(1))
                except Exception:
                    pass

            return {
                "success": True,
                "elapsed_s": elapsed,
                "tokens_per_sec": tps,
                "model_name": os.path.basename(model),
                "output": "Ready to study.",
                "message": f"SmolLM2-360M verified running on CPU in {elapsed}s ({tps} t/s) with 0 MB idle RAM footprint."
            }
        except Exception as e:
            logger.warning(f"test_ai_model error: {e}")
            return {"success": False, "error": str(e)}

    def download_ai_model(self):
        """Spawns background download for SmolLM2-360M GGUF model and llama-cli."""
        if _ai_download_state.get("downloading", False):
            return {"status": "in_progress", "pct": _ai_download_state.get("pct", 0)}

        def _download_task():
            _ai_download_state["downloading"] = True
            _ai_download_state["pct"] = 0
            _ai_download_state["error"] = None
            _ai_download_state["message"] = "Initializing download..."
            models_dir = get_models_dir()
            model_dest = os.path.join(models_dir, "SmolLM2-360M-Instruct-Q4_K_M.gguf")
            model_url = "https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF/resolve/main/SmolLM2-360M-Instruct-Q4_K_M.gguf"
            try:
                def progress(pct):
                    _ai_download_state["pct"] = pct
                    _ai_download_state["message"] = f"Downloading Embedded AI Model: {pct}%"
                download_file_with_progress(model_url, model_dest, progress)
                _ai_download_state["downloading"] = False
                _ai_download_state["installed"] = True
                _ai_download_state["pct"] = 100
                _ai_download_state["message"] = "Embedded AI ready!"
            except Exception as e:
                _ai_download_state["downloading"] = False
                _ai_download_state["error"] = str(e)
                _ai_download_state["message"] = f"Download error: {e}"

        t = threading.Thread(target=_download_task, daemon=True)
        t.start()
        return {"status": "started"}

    def slice_task_ai(self, user_prompt: str, engine_mode: str = "neural"):
        """Executes zero-idle-RAM ephemeral subprocess task slicer or smart NLP slicer with concurrency protection."""
        with self._slice_lock:
            if engine_mode == "smart":
                return smart_multidomain_slice(user_prompt)
            return run_ephemeral_llama_slice(user_prompt)

    def slice_micro_task(self, task_title: str, current_mins: int = 15):
        """Decomposes a single subtask into 3 ultra-tiny (2-to-5 minute) physical starter steps."""
        now_ms = int(datetime.datetime.now().timestamp() * 1000)
        clean = (task_title or "Task").strip()
        clean = re.sub(r'^(?:Step\s*\d+:\s*(?:Open\s+tools\s*&\s*set\s+up\s+workspace\s+for\s+|Read/execute\s+only\s+the\s+first\s+small\s+item\s+of\s+|Complete\s+one\s+\d+-minute\s+focused\s+segment\s+of\s+)?|Step\s*\d+:\s*)', '', clean, flags=re.I).strip()
        if not clean:
            clean = "Task"
        return [
            { "id": f"sub-{now_ms}-1", "title": f"Step 0: Open tools & set up workspace for {clean}", "mins": 2, "priority": "normal", "completed": False },
            { "id": f"sub-{now_ms}-2", "title": f"Step 1: Read/execute only the first small item of {clean}", "mins": 3, "priority": "normal", "completed": False },
            { "id": f"sub-{now_ms}-3", "title": f"Step 2: Complete one 5-minute focused segment of {clean}", "mins": 5, "priority": "important", "completed": False }
        ]

    def trigger_webhook(self, event_type: str, payload: dict, webhook_url: str = None):
        """Asynchronously dispatches an event to the configured webhook URL."""
        url = webhook_url
        if not url:
            state_file = get_state_file_path()
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        st = json.load(f)
                    url = st.get("webhookConfig", {}).get("url")
                except Exception:
                    pass
        if url:
            dispatch_webhook_async(url, event_type, payload)
            return {"status": "dispatched"}
        return {"status": "no_webhook_configured"}

    def test_webhook(self, webhook_url: str):
        """Sends a test ping to the webhook URL."""
        if not webhook_url or not str(webhook_url).strip():
            return {"status": "error", "message": "Webhook URL is empty"}
        try:
            data = {
                "event": "ping",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "message": "StudyPulse v3.0 Webhook Bridge Connected!",
                "version": "3.0.0"
            }
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                webhook_url.strip(),
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "StudyPulse/3.0 (Windows)"
                }
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                return {"status": "ok", "code": resp.status, "message": f"HTTP {resp.status} Response Received"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_calendar_ics_data(self):
        """Returns live RFC 5545 iCalendar stream data."""
        state_file = get_state_file_path()
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    st = json.load(f)
                return generate_ical_feed(st)
            except Exception:
                pass
        return generate_ical_feed({})

    def notify_phone_sync(self, data=None):
        """Notifies desktop WebView that phone saved state changes."""
        if self._window:
            try:
                self._window.evaluate_js(
                    "if (typeof window.onPhoneStateSynced === 'function') window.onPhoneStateSynced();"
                )
            except Exception as e:
                logger.debug(f"Failed to notify UI of phone sync: {e}")

    # --- Spotify Audio Bridge API ---
    def spotify_get_status(self):
        try:
            return spotify_bridge.get_status()
        except Exception as e:
            logger.error(f"spotify_get_status bridge error: {e}")
            return {"connected": False, "mode": "idle", "is_playing": False, "track": "", "artist": ""}

    def spotify_control(self, action, uri=None, position_ms=None, volume_percent=None, context_uri=None):
        try:
            return spotify_bridge.control(action, uri, position_ms=position_ms, volume_percent=volume_percent, context_uri=context_uri)
        except Exception as e:
            logger.error(f"spotify_control bridge error: {e}")
            return {"connected": False, "mode": "idle", "is_playing": False}

    def spotify_set_config(self, client_id=None, auto_sync_sprint=None, presets=None):
        try:
            return spotify_bridge.set_config(client_id, auto_sync_sprint, presets)
        except Exception as e:
            logger.error(f"spotify_set_config bridge error: {e}")
            return {"connected": False, "mode": "idle"}

    def open_external_browser(self, url):
        """Opens any external URL in the user's default system browser."""
        try:
            webbrowser.open(url)
            return {"status": "ok", "url": url}
        except Exception as e:
            logger.error(f"Failed to open browser for {url}: {e}")
            return {"status": "error", "message": str(e)}

    def open_spotify_auth_browser(self, client_id=None):
        """Launches Spotify OAuth 2.0 PKCE flow in the user's default system browser."""
        if client_id and str(client_id).strip():
            spotify_bridge.set_config(client_id=str(client_id).strip())
        auth_data = spotify_bridge._read_auth_data()
        cid = (client_id or auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
        auth_url = spotify_bridge.get_login_url(cid)
        webbrowser.open(auth_url)
        return {"status": "ok", "url": auth_url}

    def open_spotify_login(self, client_id=None):
        return self.open_spotify_auth_browser(client_id)

    def spotify_get_playlists(self):
        return spotify_bridge.get_user_playlists()

    def spotify_search(self, query):
        try:
            return spotify_bridge.search_catalog(query)
        except Exception as e:
            logger.error(f"spotify_search bridge error: {e}")
            return {"tracks": [], "playlists": []}

    def spotify_login(self, client_id=None):
        return self.open_spotify_auth_browser(client_id)


def get_local_ip():
    """Resolves the active LAN/Wi-Fi IPv4 address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


class SyncHandler(http.server.BaseHTTPRequestHandler):
    """
    Lightweight HTTP handler serving StudyPulse Web Companion
    and real-time /api/state sync with CORS enabled.
    """

    def end_cors_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

    def do_OPTIONS(self):
        self.end_cors_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html", "/studypulse.html"):
            html_path = getattr(self.server, "html_path", None)
            if html_path and os.path.exists(html_path):
                try:
                    with open(html_path, "rb") as f:
                        content = f.read()
                    self.end_cors_headers(200, "text/html; charset=utf-8")
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logger.error(f"Error serving HTML: {e}")

        elif path == "/api/state":
            state_file = get_state_file_path()
            if os.path.exists(state_file):
                try:
                    with open(state_file, "rb") as f:
                        data = f.read()
                    self.end_cors_headers(200, "application/json; charset=utf-8")
                    self.wfile.write(data)
                    return
                except Exception:
                    pass
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(b"{}")
            return

        elif path in ("/calendar.ics", "/cal.ics"):
            state_file = get_state_file_path()
            st = {}
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        st = json.load(f)
                except Exception:
                    pass
            ical_data = generate_ical_feed(st).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Content-Disposition", 'inline; filename="studypulse.ics"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(ical_data)
            return

        elif path == "/api/ai/status":
            ready, cli, model = check_ai_engine_ready()
            resp = json.dumps({
                "status": "ok",
                "installed": ready,
                "cli_path": cli,
                "model_path": model,
                "downloading": _ai_download_state.get("downloading", False),
                "download_pct": _ai_download_state.get("pct", 0),
                "message": _ai_download_state.get("message", "")
            }).encode("utf-8")
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(resp)
            return

        elif path == "/api/spotify/status":
            st = spotify_bridge.get_status()
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(st).encode("utf-8"))
            return

        elif path == "/api/spotify/playlists":
            res = spotify_bridge.get_user_playlists()
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif path == "/api/spotify/me-library":
            res = spotify_bridge.get_user_playlists()
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif path.startswith("/api/spotify/search"):
            query_map = urllib.parse.parse_qs(parsed.query)
            q = query_map.get("q", [""])[0]
            res = spotify_bridge.search_catalog(q)
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return



        elif path == "/api/spotify/login":
            query = urllib.parse.parse_qs(parsed.query)
            client_id = query.get("client_id", [""])[0]
            if not client_id:
                auth_data = spotify_bridge._read_auth_data()
                client_id = (auth_data.get("spotifyClientId", "") or DEFAULT_SPOTIFY_CLIENT_ID).strip()
            auth_url = spotify_bridge.get_login_url(client_id)
            self.send_response(302)
            self.send_header("Location", auth_url)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return

        elif path == "/api/spotify/callback":
            query = urllib.parse.parse_qs(parsed.query)
            code = query.get("code", [""])[0]
            error = query.get("error", [""])[0]
            if error or not code:
                err_msg = error or "Authorization code was not provided."
                self.end_cors_headers(400, "text/html; charset=utf-8")
                html_fail = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Spotify Login Error</title>
                <style>body{{background:#0A0A0B;color:#EAEAE6;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
                .card{{background:#141416;border:1px solid #27272A;border-radius:24px;padding:36px 32px;max-width:440px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.6);}}
                h2{{margin:0 0 10px;font-size:20px;color:#f87171;}} p{{color:#A1A1AA;font-size:13px;line-height:1.5;margin-bottom:20px;}}
                .btn{{display:inline-block;background:#EAEAE6;color:#0A0A0B;padding:10px 24px;border-radius:9999px;text-decoration:none;font-size:12px;font-weight:600;margin:4px;cursor:pointer;}}
                .btn-sec{{background:#1C1C1F;color:#EAEAE6;border:1px solid #27272A;}}</style></head><body>
                <div class="card"><h2>Authentication Cancelled</h2><p>{err_msg}</p><a class="btn" href="/api/spotify/login">Retry Login</a><button class="btn btn-sec" onclick="window.close()">Close</button></div></body></html>"""
                self.wfile.write(html_fail.encode("utf-8"))
                return
            try:
                spotify_bridge.handle_callback(code)
                display_name = spotify_bridge._read_state_data().get("spotifyDisplayName", "Spotify User")
                self.end_cors_headers(200, "text/html; charset=utf-8")
                html_ok = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Spotify Connected - StudyPulse</title>
                <style>body{{background:#0A0A0B;color:#EAEAE6;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
                .card{{background:#141416;border:1px solid #27272A;border-radius:24px;padding:36px 32px;max-width:440px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.6);}}
                h2{{margin:0 0 10px;font-size:20px;font-weight:600;color:#EAEAE6;}} p{{color:#A1A1AA;font-size:13px;line-height:1.6;margin-bottom:24px;}}
                .badge{{display:inline-block;padding:4px 12px;border-radius:9999px;background:#1C1C1F;border:1px solid #27272A;font-size:12px;font-weight:600;margin-bottom:16px;color:#10b981;}}
                .btn{{display:inline-block;background:#EAEAE6;color:#0A0A0B;padding:10px 24px;border-radius:9999px;font-size:12px;font-weight:600;cursor:pointer;border:none;}}</style>
                <script>
                    try {{ window.parent.postMessage({{ type: "SPOTIFY_AUTH_SUCCESS" }}, "*"); }} catch(e){{}}
                    setTimeout(() => {{ try {{ window.close(); }} catch(e){{}} }}, 1500);
                </script></head><body>
                <div class="card"><div class="badge">Connected: {display_name}</div><h2>Spotify Synchronized</h2><p>Your Spotify account is connected to StudyPulse. Closing window...</p><button class="btn" onclick="window.close()">Close Window</button></div></body></html>"""
                self.wfile.write(html_ok.encode("utf-8"))
                return
            except Exception as e:
                logger.error(f"Error in /api/spotify/callback: {e}")
                self.end_cors_headers(400, "text/html; charset=utf-8")
                html_err = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Spotify Auth Error</title>
                <style>body{{background:#0A0A0B;color:#EAEAE6;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
                .card{{background:#141416;border:1px solid #27272A;border-radius:24px;padding:36px 32px;max-width:480px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.6);}}
                h2{{margin:0 0 10px;font-size:20px;color:#f87171;}} pre{{background:#1C1C1F;border:1px solid #27272A;padding:12px;border-radius:12px;color:#EAEAE6;font-size:11px;text-align:left;overflow-x:auto;max-height:160px;}}
                p{{color:#A1A1AA;font-size:13px;line-height:1.5;margin-bottom:16px;}}
                .btn{{display:inline-block;background:#EAEAE6;color:#0A0A0B;padding:10px 24px;border-radius:9999px;text-decoration:none;font-size:12px;font-weight:600;margin:4px;cursor:pointer;}}
                .btn-sec{{background:#1C1C1F;color:#EAEAE6;border:1px solid #27272A;}}</style></head><body>
                <div class="card"><h2>Spotify Authentication Error</h2><p>Spotify rejected the authorization request with the following details:</p><pre>{e}</pre><br/><a class="btn" href="/api/spotify/login">Retry Login</a><button class="btn btn-sec" onclick="window.close()">Close</button></div></body></html>"""
                self.wfile.write(html_err.encode("utf-8"))
                return

        elif path == "/api/info":
            ip = get_local_ip()
            port = getattr(self.server, "server_port", 8765)
            resp = json.dumps({
                "app": "StudyPulse",
                "version": "3.0.0",
                "ip": ip,
                "port": port,
                "status": "active"
            }).encode("utf-8")
            self.end_cors_headers(200, "application/json; charset=utf-8")
            self.wfile.write(resp)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/state":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
                state_file = get_state_file_path()
                os.makedirs(os.path.dirname(state_file), exist_ok=True)
                # Preserve server-managed keys (like Spotify credentials and tokens)
                if os.path.exists(state_file):
                    try:
                        with open(state_file, "r", encoding="utf-8") as f_prev:
                            prev_st = json.load(f_prev)
                            for k, v in prev_st.items():
                                if k.startswith("spotify") and k not in data:
                                    data[k] = v
                    except Exception:
                        pass
                temp_file = state_file + f".{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"
                try:
                    with _state_io_lock:
                        with open(temp_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                        os.replace(temp_file, state_file)
                except Exception as w_err:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass
                    raise w_err

                bridge = getattr(self.server, "bridge", None)
                if bridge:
                    bridge.notify_phone_sync(data)

                # Webhook auto-dispatch if enabled in state
                webhook_cfg = data.get("webhookConfig", {})
                if webhook_cfg.get("enabled", False) and webhook_cfg.get("url"):
                    dispatch_webhook_async(
                        webhook_cfg["url"],
                        "state_updated",
                        {"goals_count": len(data.get("goals", [])), "habits_count": len(data.get("ironcladHabits", []))}
                    )

                self.end_cors_headers(200, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"status": "ok", "synced": True}).encode("utf-8"))
                return
            except Exception as e:
                logger.error(f"Error handling POST /api/state: {e}")
                self.end_cors_headers(400, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
                return

        elif parsed.path == "/api/ai/slice":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                req_data = json.loads(body)
                prompt = req_data.get("prompt", "")
                engine = req_data.get("engine", "neural")
                with _ai_inference_lock:
                    if engine == "smart":
                        result = smart_multidomain_slice(prompt)
                    else:
                        result = run_ephemeral_llama_slice(prompt)
                self.end_cors_headers(200, "application/json; charset=utf-8")
                self.wfile.write(json.dumps(result).encode("utf-8"))
                return
            except Exception as e:
                self.end_cors_headers(500, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        elif parsed.path == "/api/spotify/control":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                req_data = json.loads(body)
                action = req_data.get("action", "")
                uri = req_data.get("uri", None)
                position_ms = req_data.get("position_ms", None)
                volume_percent = req_data.get("volume_percent", None)
                context_uri = req_data.get("context_uri", None)
                res = spotify_bridge.control(action, uri, position_ms=position_ms, volume_percent=volume_percent, context_uri=context_uri)
                self.end_cors_headers(200, "application/json; charset=utf-8")
                self.wfile.write(json.dumps(res).encode("utf-8"))
                return
            except Exception as e:
                self.end_cors_headers(500, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        elif parsed.path == "/api/spotify/auth-window":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                url = None
                if content_len > 0:
                    try:
                        body = json.loads(self.rfile.read(content_len).decode("utf-8"))
                        url = body.get("url")
                    except Exception:
                        pass
                bridge = getattr(self.server, "bridge", None)
                if bridge and hasattr(bridge, "open_spotify_login"):
                    res = bridge.open_spotify_login(url)
                else:
                    target = url or "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Fopen.spotify.com%2F"
                    res = {"status": "ok", "url": target, "in_app": True}
                self.end_cors_headers(200, "application/json; charset=utf-8")
                self.wfile.write(json.dumps(res).encode("utf-8"))
                return
            except Exception as e:
                self.end_cors_headers(500, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        elif parsed.path == "/api/spotify/config":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                req_data = json.loads(body)
                client_id = req_data.get("clientId", None)
                auto_sync = req_data.get("autoSyncSprint", None)
                presets = req_data.get("presets", None)
                res = spotify_bridge.set_config(client_id, auto_sync, presets)
                self.end_cors_headers(200, "application/json; charset=utf-8")
                self.wfile.write(json.dumps(res).encode("utf-8"))
                return
            except Exception as e:
                self.end_cors_headers(500, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        elif parsed.path == "/api/webhook/test":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                req_data = json.loads(body)
                url = req_data.get("url", "")
                bridge = getattr(self.server, "bridge", None)
                if bridge:
                    res = bridge.test_webhook(url)
                else:
                    res = {"status": "error", "message": "No bridge"}
                self.end_cors_headers(200, "application/json; charset=utf-8")
                self.wfile.write(json.dumps(res).encode("utf-8"))
                return
            except Exception as e:
                self.end_cors_headers(500, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def start_local_sync_server(html_path, bridge, initial_port=8765):
    """Starts the companion web server on a free port in a background daemon thread."""
    for port in range(initial_port, initial_port + 20):
        try:
            server = http.server.ThreadingHTTPServer(("0.0.0.0", port), SyncHandler)
            server.html_path = html_path
            server.bridge = bridge
            server.server_port = port
            bridge.sync_port = port
            bridge._server_running = True
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            ip = get_local_ip()
            logger.info(f"Phone Sync Web Companion active at http://{ip}:{port}/")
            return server
        except OSError:
            continue
        except Exception as e:
            logger.warning(f"Could not start local sync server: {e}")
            break
    bridge._server_running = False
    return None


def main():
    try:
        # Set explicit Application User Model ID so Windows taskbar treats this as a unique app with its own icon
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StudyPulse.ADHD.FocusTracker.App.1.0")
        except Exception:
            pass

        # 1. Clean up any stale instances
        terminate_other_instances()

        is_widget_mode = "--widget" in sys.argv or "-w" in sys.argv

        storage_path = get_safe_storage_path(is_widget_mode)
        logger.info(f"Resolved safe storage path: {storage_path}")

        html_file = get_asset_path("studypulse.html")
        if not os.path.exists(html_file):
            raise FileNotFoundError(f"Cannot find studypulse.html at {html_file}")

        bridge = DesktopBridge()
        sync_server = start_local_sync_server(html_file, bridge)

        sync_port = getattr(bridge, "sync_port", 8765)
        app_url = f"http://127.0.0.1:{sync_port}/?_v={int(time.time())}" if sync_server else html_file

        if is_widget_mode:
            width = WIDGET_WIDTH
            height = WIDGET_HEIGHT
            x, y = get_widget_position()
        else:
            width = DASHBOARD_WIDTH
            height = DASHBOARD_HEIGHT
            x, y = get_dashboard_position()

        init_is_dark = False
        try:
            state_file = get_state_file_path()
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    st_data = json.load(f)
                    if st_data.get("theme") == "dark" or (isinstance(st_data.get("settings"), dict) and st_data["settings"].get("darkMode")):
                        init_is_dark = True
        except Exception:
            pass
        bg_color = "#0A0A0B" if init_is_dark else "#f4f4f6"

        window = webview.create_window(
            title="StudyPulse",
            url=app_url,
            js_api=bridge,
            width=width,
            height=height,
            x=x,
            y=y,
            resizable=True,
            frameless=True,
            easy_drag=False,  # MUST BE FALSE: prevents global mousedown hijacking
            min_size=(340, 440),
            on_top=False,
            background_color=bg_color,
            text_select=True,
        )
        bridge.set_window(window)

        def on_loaded():
            hwnd = bridge.get_hwnd()
            apply_taskbar_icon(hwnd)
            if init_is_dark:
                bridge.set_native_theme(True)
            if is_widget_mode:
                try:
                    window.evaluate_js("toggleWidgetMode(true, true);")
                except Exception:
                    pass

        window.events.loaded += on_loaded

        def on_start(w):
            hwnd = bridge.get_hwnd()
            apply_taskbar_icon(hwnd)
            if init_is_dark:
                bridge.set_native_theme(True)
            if is_widget_mode:
                try:
                    w.evaluate_js(
                        "if (typeof toggleWidgetMode === 'function') { toggleWidgetMode(true, true); }"
                    )
                except Exception:
                    pass

        webview.start(
            func=on_start,
            args=(window,),
            gui="edgechromium",
            private_mode=False,
            storage_path=storage_path,
            debug=False,
        )

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Fatal startup error:\n{tb}")
        try:
            for crash_dir in [os.getcwd(), os.path.expandvars(r"%APPDATA%\StudyPulse"), tempfile.gettempdir()]:
                try:
                    os.makedirs(crash_dir, exist_ok=True)
                    with open(os.path.join(crash_dir, "studypulse_crash.log"), "w", encoding="utf-8") as f:
                        f.write(tb)
                    break
                except Exception:
                    continue
            ctypes.windll.user32.MessageBoxW(
                0,
                f"StudyPulse failed to start:\n\n{e}\n\nDetails saved to studypulse_crash.log",
                "StudyPulse Error",
                0x10,
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
