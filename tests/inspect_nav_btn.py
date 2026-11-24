# -*- coding: utf-8 -*-
with open('studypulse.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'id="nav-spotify-btn"' in line:
        print(f"Line {i}: {line}")
        for j in range(max(1, i-5), min(len(lines), i+15)):
            print(f"{j}: {lines[j-1]}", end='')
        break
