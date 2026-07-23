#!/usr/bin/env python3
"""Now playing — auto-generated pixel repo cards, sorted by last push.
Runs daily in CI. Real numbers only: lines are counted from a fresh shallow
clone, commits come from the API, the flame means pushed within 7 days.
"""
import json, os, re, subprocess, tempfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER, TOP, FIRE_DAYS = "maxkle1nz", 6, 7
ROOT = Path(__file__).resolve().parent.parent
VOID, BONE, SIGNAL, GOLD, PURPLE, STEEL, STEELD = "#0F0F11", "#F2EFE9", "#E8502F", "#F2C230", "#7C4DFF", "#6E6E73", "#2B2B30"
LANG_COLORS = {"Rust": "#DEA584", "TypeScript": "#3178C6", "Python": "#3572A5", "JavaScript": "#F1E05A",
               "CSS": "#663399", "HTML": "#E34C26", "Shell": "#89E051", "TeX": "#3D6117", "Go": "#00ADD8",
               "GDScript": "#355570", "Vue": "#41B883", "C": "#555555"}

F = {
"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],
"C":["01111","10000","10000","10000","10000","10000","01111"],"D":["11110","10001","10001","10001","10001","10001","11110"],
"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],
"G":["01111","10000","10000","10111","10001","10001","01111"],"H":["10001","10001","10001","11111","10001","10001","10001"],
"I":["01110","00100","00100","00100","00100","00100","01110"],"J":["00111","00010","00010","00010","00010","10010","01100"],
"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],
"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","11001","11001","10101","10011","10011","10001"],
"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],
"Q":["01110","10001","10001","10001","10101","10010","01101"],"R":["11110","10001","10001","11110","10100","10010","10001"],
"S":["01111","10000","10000","01110","00001","00001","11110"],"T":["11111","00100","00100","00100","00100","00100","00100"],
"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","10001","01010","00100"],
"W":["10001","10001","10001","10101","10101","11011","10001"],"X":["10001","01010","00100","00100","00100","01010","10001"],
"Y":["10001","01010","00100","00100","00100","00100","00100"],"Z":["11111","00001","00010","00100","01000","10000","11111"],
"0":["01110","10001","10011","10101","11001","10001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],
"2":["01110","10001","00001","00110","01000","10000","11111"],"3":["11110","00001","00001","01110","00001","00001","11110"],
"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","10000","11110","00001","00001","11110"],
"6":["01110","10000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],
"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00001","01110"],
" ":["00000"]*7,".":["00000","00000","00000","00000","00000","01100","01100"],
"-":["00000","00000","00000","01110","00000","00000","00000"],"/":["00001","00010","00010","00100","01000","01000","10000"],
"·":["00000","00000","00000","01100","01100","00000","00000"],",":["00000","00000","00000","00000","00000","01100","01000"],
}
FLAME_A = ["....#....","....##...","...##o...","..##oo...","..#ooo#..",".##ooo#..",".#oooo#..","..####..."]
FLAME_B = ["...#.....","...##....","...#o#...","..#oo#...","..#ooo#..",".#oooo#..",".#oooo#..","..####..."]

def px_text(s, x, y, cell, color):
    out, cx = [], x
    for ch in s.upper():
        m = F.get(ch, F[" "])
        for r, row in enumerate(m):
            c = 0
            while c < len(row):
                if row[c] == "1":
                    c0 = c
                    while c < len(row) and row[c] == "1": c += 1
                    out.append(f'<rect x="{cx+c0*cell}" y="{y+r*cell}" width="{(c-c0)*cell}" height="{cell}" fill="{color}"/>')
                else: c += 1
        cx += 6 * cell
    return "".join(out), cx - x - cell

def flame(x, y, cell):
    def fr(m):
        out = []
        for r, row in enumerate(m):
            for c, ch in enumerate(row):
                if ch == "#": out.append(f'<rect x="{x+c*cell}" y="{y+r*cell}" width="{cell}" height="{cell}" fill="{SIGNAL}"/>')
                elif ch == "o": out.append(f'<rect x="{x+c*cell}" y="{y+r*cell}" width="{cell}" height="{cell}" fill="{GOLD}"/>')
        return "".join(out)
    return (f'<g>{fr(FLAME_A)}<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" dur="0.7s" calcMode="discrete" repeatCount="indefinite"/></g>'
            f'<g opacity="0">{fr(FLAME_B)}<animate attributeName="opacity" values="0;1" keyTimes="0;0.5" dur="0.7s" calcMode="discrete" repeatCount="indefinite"/></g>')

def wrap2(text, per_line):
    text = text.replace("—", "-").replace("–", "-")
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) <= per_line: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][:per_line-3].rstrip() + "..."
    return lines

def fmt_loc(n):
    return f"{n/1000:.1f}K" if n >= 1000 else str(n)

def ago(days):
    if days <= 0: return "TODAY"
    if days == 1: return "1D AGO"
    if days < 21: return f"{days}D AGO"
    if days < 90: return f"{days//7}W AGO"
    return f"{days//30}M AGO"

def card(repo, loc, commits, days):
    W, H = 580, 150
    e = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    e.append(f'<rect width="{W}" height="{H}" fill="{VOID}"/>')
    e.append('<g opacity="0.10">')
    for y in range(0, H, 8): e.append(f'<rect x="0" y="{y}" width="{W}" height="2" fill="#000000"/>')
    e.append('</g>')
    e.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="{STEELD}" stroke-width="2"/>')
    for (cx, cy, sx, sy) in [(6,6,1,1),(W-6,6,-1,1),(6,H-6,1,-1),(W-6,H-6,-1,-1)]:
        e.append(f'<rect x="{min(cx,cx+sx*14)}" y="{min(cy,cy+sy*3)}" width="14" height="3" fill="{SIGNAL}"/>')
        e.append(f'<rect x="{min(cx,cx+sx*3)}" y="{min(cy,cy+sy*14)}" width="3" height="14" fill="{SIGNAL}"/>')
    name = repo["name"]
    ncell = 4 if len(name) <= 20 else 3
    t, _ = px_text(name, 22, 20, ncell, BONE); e.append(t)
    when = ago(days)
    wlab, ww = px_text(when, 0, 0, 3, GOLD if days < FIRE_DAYS else STEEL)
    wx = W - 22 - ww - (38 if days < FIRE_DAYS else 0)
    tlab, _ = px_text(when, wx, 22, 3, GOLD if days < FIRE_DAYS else STEEL); e.append(tlab)
    if days < FIRE_DAYS: e.append(flame(W - 22 - 27, 10, 3))
    desc = (repo.get("description") or "no description yet").strip()
    for i, ln in enumerate(wrap2(desc, 45)[:2]):
        t, _ = px_text(ln, 22, 64 + i*20, 2, BONE); e.append(f'<g opacity="0.72">{t}</g>')
    lang = repo.get("language") or "MIXED"
    lcol = LANG_COLORS.get(lang, STEEL)
    y0 = 116
    e.append(f'<rect x="22" y="{y0+2}" width="12" height="12" fill="{lcol}"/>')
    x = 44
    t, w = px_text(lang, x, y0, 3, BONE); e.append(t); x += w + 22
    t, w = px_text(f"{fmt_loc(loc)} LINES", x, y0, 3, GOLD); e.append(t); x += w + 22
    t, w = px_text(f"{commits} COMMITS", x, y0, 3, PURPLE); e.append(t)
    e.append('</svg>')
    return "\n".join(e)

def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": USER})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read()), dict(r.headers)

def commit_count(name):
    try:
        _, h = api(f"https://api.github.com/repos/{USER}/{name}/commits?per_page=1")
        link = h.get("Link", "")
        m = re.search(r'page=(\d+)>; rel="last"', link)
        return int(m.group(1)) if m else 1
    except Exception:
        return 0

def count_lines(name):
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(["git", "clone", "--quiet", "--depth", "1", f"https://github.com/{USER}/{name}", td],
                           check=True, timeout=180, capture_output=True)
        except Exception:
            return 0
        files = subprocess.run(["git", "-C", td, "ls-files"], capture_output=True, text=True).stdout.splitlines()
        total = 0
        for f in files:
            p = Path(td) / f
            try:
                if p.stat().st_size > 2_000_000: continue
                head = p.open("rb").read(8000)
                if b"\0" in head: continue
                total += sum(1 for _ in p.open("rb"))
            except Exception:
                continue
        return total

def main():
    repos, _ = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
    now = datetime.now(timezone.utc)
    pool = [r for r in repos if not r["fork"] and not r.get("archived") and not r.get("disabled") and r["name"] != USER]
    top = pool[:TOP]
    cards_dir = ROOT / "assets" / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    imgs = []
    for r in top:
        days = (now - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days
        loc = count_lines(r["name"])
        commits = commit_count(r["name"])
        (cards_dir / f'{r["name"]}.svg').write_text(card(r, loc, commits, days))
        imgs.append(f'<a href="{r["html_url"]}"><img src="assets/cards/{r["name"]}.svg" width="415" alt="{r["name"]}"></a>')
        print(f'{r["name"]}: {loc} lines, {commits} commits, {days}d')
    rows = []
    for i in range(0, len(imgs), 2):
        rows.append("<p>\n" + "\n".join(imgs[i:i+2]) + "\n</p>")
    block = "\n".join(rows)
    readme = ROOT / "README.md"
    src = readme.read_text()
    src = re.sub(r"(<!-- now-playing:start -->).*?(<!-- now-playing:end -->)",
                 lambda m: m.group(1) + "\n" + block + "\n" + m.group(2), src, flags=re.S)
    readme.write_text(src)
    print("README patched")

if __name__ == "__main__":
    main()
