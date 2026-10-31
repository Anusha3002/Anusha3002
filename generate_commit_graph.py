#!/usr/bin/env python3
"""Draws commit-graph.svg: real commits as sage squares, and the days with no
commits as dotted gold "ghost" squares (commits that only happened in my head).

Usage:
  GITHUB_TOKEN=... GH_USER=Anusha3002 python3 generate_commit_graph.py   # live data
  python3 generate_commit_graph.py --sample                              # fake data, for previews
"""
import json, os, random, sys, urllib.request
from datetime import date, timedelta

USER = os.environ.get("GH_USER", "Anusha3002")
HEAD_COMMITS = "7,342"          # <- the silly fixed number. Change it to whatever is funniest.
OUT = "commit-graph.svg"

GOLD, INK = "#c9a55c", "#3a4a3f"
LEVELS = ["#b9c9a4", "#8fae7e", "#5b7a5a", "#2f4a3c"]   # light sage -> forest


def fetch_live():
    q = """query($u:String!){user(login:$u){contributionsCollection{
      totalCommitContributions
      contributionCalendar{weeks{contributionDays{date contributionCount weekday}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
    )
    col = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]]
             for w in col["contributionCalendar"]["weeks"]]
    return weeks, col["totalCommitContributions"]


def fetch_sample():
    random.seed(11)
    end = date(2026, 10, 31)
    start = end - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)       # back up to a Sunday
    weeks, total, d = [], 0, start
    while d <= end:
        week = []
        for _ in range(7):
            if d <= end:
                busy = 0.5 if d.month in (2, 3, 4, 9, 10) else 0.18
                n = random.choice([1, 1, 2, 3, 5, 8]) if random.random() < busy else 0
                total += n
                week.append((d.isoformat(), n))
            d += timedelta(days=1)
        weeks.append(week)
    return weeks, total


def level(n):
    return 0 if n < 2 else 1 if n < 4 else 2 if n < 7 else 3


def build(weeks, commits):
    CELL, GAP = 11, 3
    X0, Y0 = 34, 92
    W, H = 800, 356
    real = ghost = 0
    cells = []
    for wi, week in enumerate(weeks):
        for (day, n) in week:
            dow = date.fromisoformat(day).weekday()
            row = (dow + 1) % 7                                # Sunday on top, like GitHub
            x, y = X0 + wi * (CELL + GAP), Y0 + row * (CELL + GAP)
            if n > 0:
                real += 1
                cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{LEVELS[level(n)]}"/>')
            else:
                ghost += 1
                cells.append(f'<rect class="g g{ghost % 7}" x="{x+.5}" y="{y+.5}" width="{CELL-1}" height="{CELL-1}" rx="2"/>')
    grid_w = len(weeks) * (CELL + GAP)
    commits_txt = f"{commits:,}"
    bar_real = max(6, min(300, int(300 * commits / 9000)))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="{commits_txt} commits on GitHub this year, {HEAD_COMMITS} in my head">
  <style>
    .serif {{ font-family: Georgia, 'Times New Roman', serif; }}
    .mono  {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
    .g {{ fill: none; stroke: {GOLD}; stroke-width: 1; stroke-dasharray: 2 2; opacity: .35; animation: twinkle 5s ease-in-out infinite; }}
    .g0 {{ animation-delay: 0s; }} .g1 {{ animation-delay: .7s; }} .g2 {{ animation-delay: 1.4s; }} .g3 {{ animation-delay: 2.1s; }}
    .g4 {{ animation-delay: 2.8s; }} .g5 {{ animation-delay: 3.5s; }} .g6 {{ animation-delay: 4.2s; }}
    @keyframes twinkle {{ 0%, 100% {{ opacity: .25; }} 50% {{ opacity: .85; }} }}
    .over {{ animation: stretch 4s ease-in-out infinite; transform-box: fill-box; transform-origin: left; }}
    @keyframes stretch {{ 0%, 100% {{ transform: scaleX(.96); }} 50% {{ transform: scaleX(1); }} }}
  </style>
  <defs>
    <linearGradient id="wall" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e9e0cb"/><stop offset="1" stop-color="#dfd3b8"/></linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="10" fill="url(#wall)"/>

  <text class="serif" x="{W/2}" y="38" text-anchor="middle" font-size="22" fill="{INK}" font-weight="bold">Commits: the official record vs. the real story</text>
  <text class="serif" x="{W/2}" y="60" text-anchor="middle" font-size="13" font-style="italic" fill="#8a7a5c">solid squares happened. dotted squares happened in my head.</text>

  {"".join(cells)}

  <!-- legend -->
  <g class="serif" font-size="12" fill="#6b5f45">
    <rect x="{X0}" y="{Y0+7*(CELL+GAP)+10}" width="{CELL}" height="{CELL}" rx="2" fill="{LEVELS[2]}"/>
    <text x="{X0+CELL+6}" y="{Y0+7*(CELL+GAP)+20}">pushed to GitHub</text>
    <rect class="g g2" x="{X0+150.5}" y="{Y0+7*(CELL+GAP)+10.5}" width="{CELL-1}" height="{CELL-1}" rx="2"/>
    <text x="{X0+150+CELL+6}" y="{Y0+7*(CELL+GAP)+20}">committed (mentally)</text>
  </g>

  <!-- git status joke -->
  <g class="mono" font-size="12.5">
    <rect x="{X0}" y="228" width="{grid_w//2 - 6}" height="108" rx="8" fill="#2f3a33"/>
    <text x="{X0+14}" y="250" fill="#a9bf96">$ git status</text>
    <text x="{X0+14}" y="270" fill="#e8dfc9">Changes not staged for commit:</text>
    <text x="{X0+28}" y="288" fill="#d98c7a">modified:   my entire personality</text>
    <text x="{X0+14}" y="306" fill="#e8dfc9">Untracked: a novel, 3 startups,</text>
    <text x="{X0+14}" y="324" fill="#e8dfc9">and "one more quick idea"</text>
  </g>

  <!-- counters -->
  <g class="serif" fill="{INK}">
    <text x="{X0 + grid_w//2 + 14}" y="248" font-size="13">On GitHub: <tspan font-size="18" font-weight="bold" fill="#2f4a3c">{commits_txt}</tspan></text>
    <rect x="{X0 + grid_w//2 + 14}" y="256" width="{bar_real}" height="10" rx="5" fill="#5b7a5a"/>
    <text x="{X0 + grid_w//2 + 14 + bar_real + 8}" y="265" font-size="11" font-style="italic" fill="#8a7a5c">(tiny, but tried its best)</text>

    <text x="{X0 + grid_w//2 + 14}" y="292" font-size="13">In my head: <tspan font-size="18" font-weight="bold" fill="#8a5a3c">{HEAD_COMMITS}</tspan> <tspan font-size="11" font-style="italic" fill="#8a7a5c">(unpushed)</tspan></text>
    <rect class="over" x="{X0 + grid_w//2 + 14}" y="302" width="{grid_w - grid_w//2 - 14}" height="10" rx="5" fill="{GOLD}"/>
    <text x="{X0 + grid_w - 4}" y="326" text-anchor="end" font-size="11" font-style="italic" fill="#8a7a5c">bar exceeds container width</text>
  </g>
</svg>
'''


if __name__ == "__main__":
    weeks, commits = fetch_sample() if "--sample" in sys.argv or "GITHUB_TOKEN" not in os.environ else fetch_live()
    open(OUT, "w").write(build(weeks, commits))
    print(f"wrote {OUT}: {commits} commits")
