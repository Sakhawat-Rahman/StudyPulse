import subprocess, os, re
from PIL import Image

with open("studypulse.html", "r", encoding="utf-8") as f:
    html = f.read()

# Make a direct HTML light dashboard
html = re.sub(r"<html[^>]*>", '<html lang="en">', html, count=1)
early_script = """<head>
  <script>
    try {
      localStorage.setItem('studypulse_theme', 'light');
      document.documentElement.classList.remove('dark');
    } catch(e) {}
  </script>"""
html = html.replace("<head>", early_script, 1)

with open("scratch/test_direct_light.html", "w", encoding="utf-8") as f:
    f.write(html)

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out1 = r"G:\ADHD app\scratch\shot_headless_old.png"
out2 = r"G:\ADHD app\scratch\shot_headless_new.png"

# 1. Old headless with virtual-time-budget
cmd1 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--hide-scrollbars",
    "--virtual-time-budget=2000",
    "--window-size=1440,900",
    f"--screenshot={out1}",
    "file:///" + os.path.abspath("scratch/test_direct_light.html").replace("\\", "/")
]
subprocess.run(cmd1, capture_output=True, timeout=15)
if os.path.exists(out1):
    im1 = Image.open(out1)
    print("Old headless (1440x900):", im1.size, os.path.getsize(out1), "bytes")
    print("Pixel (600, 600):", im1.getpixel((600, 600)))
    print("Pixel (100, 100):", im1.getpixel((100, 100)))
    dark_cnt = sum(1 for p in im1.getdata() if p[0] < 60 and p[1] < 60 and p[2] < 60)
    print("Dark text pixels:", dark_cnt)
else:
    print("Old headless failed")
