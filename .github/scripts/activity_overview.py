import json
import os
import sys
import urllib.request

LOGIN = os.environ.get("GH_LOGIN", "Bhumika-1432006")
TOKEN = os.environ["GH_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "activity-overview.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "activity-overview"},
)
with urllib.request.urlopen(req) as resp:
    payload = json.load(resp)

if "errors" in payload:
    sys.exit(f"GraphQL error: {payload['errors']}")

c = payload["data"]["user"]["contributionsCollection"]
counts = {
    "review": c["totalPullRequestReviewContributions"],
    "issues": c["totalIssueContributions"],
    "prs": c["totalPullRequestContributions"],
    "commits": c["totalCommitContributions"],
}
total = sum(counts.values()) or 1
pct = {k: round(v * 100 / total) for k, v in counts.items()}
peak = max(counts.values()) or 1

W, H = 495, 300
CX, CY, R = 247, 150, 82
MIN_FRACTION = 0.04

def scale(key):
    return max(counts[key] / peak, MIN_FRACTION) * R

pts = {
    "review": (CX, CY - scale("review")),
    "issues": (CX + scale("issues"), CY),
    "prs": (CX, CY + scale("prs")),
    "commits": (CX - scale("commits"), CY),
}
polygon = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pts["review"], pts["issues"], pts["prs"], pts["commits"]))
dots = "\n".join(
    f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#0d1117" stroke="#3fb950" stroke-width="2"/>'
    for x, y in pts.values()
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Activity overview">
  <style>
    text {{ font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .title {{ font-size: 14px; fill: #e6edf3; font-weight: 600; }}
    .pct {{ font-size: 12px; fill: #8b949e; }}
    .label {{ font-size: 12px; fill: #8b949e; }}
  </style>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="#0d1117" stroke="#30363d"/>
  <text x="20" y="28" class="title">Activity overview</text>
  <g stroke="#3fb950" stroke-width="2" stroke-linecap="round">
    <line x1="{CX}" y1="{CY - R - 14}" x2="{CX}" y2="{CY + R + 14}"/>
    <line x1="{CX - R - 14}" y1="{CY}" x2="{CX + R + 14}" y2="{CY}"/>
  </g>
  <polygon points="{polygon}" fill="#238636" fill-opacity="0.65" stroke="#3fb950" stroke-width="1.5" stroke-linejoin="round"/>
{dots}
  <text x="{CX}" y="{CY - R - 38}" text-anchor="middle" class="pct">{pct['review']}%</text>
  <text x="{CX}" y="{CY - R - 22}" text-anchor="middle" class="label">Code review</text>
  <text x="{CX + R + 26}" y="{CY - 2}" class="pct">{pct['issues']}%</text>
  <text x="{CX + R + 26}" y="{CY + 14}" class="label">Issues</text>
  <text x="{CX}" y="{CY + R + 34}" text-anchor="middle" class="pct">{pct['prs']}%</text>
  <text x="{CX}" y="{CY + R + 50}" text-anchor="middle" class="label">Pull requests</text>
  <text x="{CX - R - 26}" y="{CY - 2}" text-anchor="end" class="pct">{pct['commits']}%</text>
  <text x="{CX - R - 26}" y="{CY + 14}" text-anchor="end" class="label">Commits</text>
</svg>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Wrote {OUT}: {counts} -> {pct}")
