import json
import os
import random
import sys
import urllib.request
from collections import deque

LOGIN = os.environ.get("GH_LOGIN", "Bhumika-1432006")
TOKEN = os.environ["GH_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "contribution-snake.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionLevel weekday } }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "contribution-snake"},
)
with urllib.request.urlopen(req) as resp:
    payload = json.load(resp)
if "errors" in payload:
    sys.exit(f"GraphQL error: {payload['errors']}")

weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
COLS, ROWS = len(weeks), 7
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
level = {}
for c, week in enumerate(weeks):
    for day in week["contributionDays"]:
        level[(c, day["weekday"])] = LEVELS[day["contributionLevel"]]

LANE_TOP, LANE_BOTTOM = -1, ROWS


def passable(cell, blocked):
    c, r = cell
    if cell in blocked or not (0 <= c < COLS):
        return False
    if r in (LANE_TOP, LANE_BOTTOM):
        return True
    return level.get(cell) == 0


def reaches_goal(start, blocked):
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur[0] == COLS - 1:
            return True
        for dc, dr in ((1, 0), (0, 1), (0, -1), (-1, 0)):
            nxt = (cur[0] + dc, cur[1] + dr)
            if nxt not in seen and passable(nxt, blocked):
                seen.add(nxt)
                queue.append(nxt)
    return False


rng = random.Random(42)
starts = [(0, r) for r in range(ROWS) if level.get((0, r)) == 0] or [(0, LANE_TOP)]
start = rng.choice(starts)
path = [start]
visited = {start}
prev_dir = (1, 0)
BASE_WEIGHT = {(1, 0): 3.0, (0, -1): 1.6, (0, 1): 1.6, (-1, 0): 0.4}

while path[-1][0] != COLS - 1:
    cur = path[-1]
    options, weights = [], []
    for d, w in BASE_WEIGHT.items():
        nxt = (cur[0] + d[0], cur[1] + d[1])
        if not passable(nxt, visited) or not reaches_goal(nxt, visited | {nxt}):
            continue
        if d == prev_dir:
            w *= 1.6
        if nxt[1] in (LANE_TOP, LANE_BOTTOM):
            w *= 0.12
        options.append((nxt, d))
        weights.append(w)
    if not options:
        sys.exit("Snake got stuck; no route to the right edge")
    nxt, prev_dir = rng.choices(options, weights=weights)[0]
    path.append(nxt)
    visited.add(nxt)

for cell in path:
    if cell[1] not in (LANE_TOP, LANE_BOTTOM):
        assert level[cell] == 0, f"snake would eat contribution at {cell}"

SEGMENTS = 7
EXT = SEGMENTS + 3
full = (
    [(-i, path[0][1]) for i in range(EXT, 0, -1)]
    + path
    + [(COLS - 1 + i, path[-1][1]) for i in range(1, EXT + 1)]
)

CELL, GAP = 11, 4
PITCH = CELL + GAP
PAD_X, PAD_Y = 20, 20
rmin = min(0, min(r for _, r in path))
rmax = max(ROWS - 1, max(r for _, r in path))
W = 2 * PAD_X + COLS * PITCH - GAP
H = 2 * PAD_Y + (rmax - rmin + 1) * PITCH - GAP


def xy(cell):
    return PAD_X + cell[0] * PITCH, PAD_Y + (cell[1] - rmin) * PITCH


rects = "\n".join(
    f'    <rect class="c{lv}" x="{xy(cell)[0]}" y="{xy(cell)[1]}" width="{CELL}" height="{CELL}" rx="2"/>'
    for cell, lv in sorted(level.items())
)
path_d = "M " + " L ".join(f"{xy(cell)[0]} {xy(cell)[1]}" for cell in full)

STEP = 0.11
total = (len(full) - 1) * STEP
SNAKE_COLORS = ["#d2a8ff", "#bc8cff", "#a371f7", "#8957e5", "#6e40c9", "#5a32a3", "#472680"]
snake = "\n".join(
    f'  <rect width="{CELL}" height="{CELL}" rx="3" fill="{SNAKE_COLORS[i]}">'
    f'<animateMotion dur="{total:.2f}s" begin="-{(SEGMENTS - i) * STEP:.2f}s" repeatCount="indefinite" calcMode="paced">'
    f'<mpath xlink:href="#snake-path"/></animateMotion></rect>'
    for i in range(SEGMENTS - 1, -1, -1)
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution snake">
  <style>
    .c0 {{ fill: #161b22; }}
    .c1 {{ fill: #01311f; }}
    .c2 {{ fill: #034525; }}
    .c3 {{ fill: #0f6d31; }}
    .c4 {{ fill: #00c647; }}
  </style>
  <defs><path id="snake-path" d="{path_d}"/></defs>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="#0d1117" stroke="#30363d"/>
  <g>
{rects}
  </g>
{snake}
</svg>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Wrote {OUT}: {COLS} weeks, path {len(path)} cells, loop {total:.1f}s, {len(svg) // 1024} KB")
