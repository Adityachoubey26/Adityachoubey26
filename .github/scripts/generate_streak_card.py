import os
import datetime
import requests

USERNAME = os.environ.get("GH_USERNAME", "Adityachoubey26")
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"bearer {TOKEN}"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_days():
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers=HEADERS,
    )
    r.raise_for_status()
    data = r.json()
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    total = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    days.sort(key=lambda x: x[0])
    return days, total

def compute_streaks(days):
    today = datetime.date.today().isoformat()
    longest = 0
    current_run = 0
    best_start = best_end = None
    run_start = None

    for date_str, count in days:
        if count > 0:
            if current_run == 0:
                run_start = date_str
            current_run += 1
            if current_run > longest:
                longest = current_run
                best_start, best_end = run_start, date_str
        else:
            current_run = 0

    # current streak: walk backwards from today (or yesterday if today has no contribution yet)
    by_date = {d: c for d, c in days}
    cursor = datetime.date.today()
    # if today has 0 contributions, start counting from yesterday so a live streak isn't shown as broken
    if by_date.get(cursor.isoformat(), 0) == 0:
        cursor -= datetime.timedelta(days=1)

    current_streak = 0
    last_active_date = None
    while True:
        key = cursor.isoformat()
        if by_date.get(key, 0) > 0:
            current_streak += 1
            if last_active_date is None:
                last_active_date = key
            cursor -= datetime.timedelta(days=1)
        else:
            break

    return current_streak, longest, best_start, best_end, last_active_date

def render_svg(total, current_streak, longest, streak_range, last_active_date):
    range_label = f"{streak_range[0]} - {streak_range[1]}" if streak_range and streak_range[0] else "-"
    svg = f"""<svg width="700" height="200" viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="700" height="200" rx="10" fill="#0D1117" stroke="#332020" stroke-width="1.5"/>
  <line x1="233" y1="30" x2="233" y2="170" stroke="#332020" stroke-width="1.5"/>
  <line x1="466" y1="30" x2="466" y2="170" stroke="#332020" stroke-width="1.5"/>

  <text x="116" y="70" font-family="Segoe UI, sans-serif" font-size="34" font-weight="bold" fill="#FF3B6B" text-anchor="middle">{total}</text>
  <text x="116" y="98" font-family="Segoe UI, sans-serif" font-size="14" fill="#FF3B6B" text-anchor="middle">Total Contributions</text>
  <text x="116" y="120" font-family="Segoe UI, sans-serif" font-size="12" fill="#9aa4b2" text-anchor="middle">All-time</text>

  <circle cx="350" cy="72" r="38" fill="none" stroke="#FF0000" stroke-width="3" filter="url(#glow)"/>
  <text x="350" y="82" font-family="Segoe UI, sans-serif" font-size="30" font-weight="bold" fill="#FFD400" text-anchor="middle">{current_streak}</text>
  <text x="350" y="128" font-family="Segoe UI, sans-serif" font-size="14" font-weight="bold" fill="#FF0000" text-anchor="middle">Current Streak</text>
  <text x="350" y="148" font-family="Segoe UI, sans-serif" font-size="12" fill="#9aa4b2" text-anchor="middle">{last_active_date or '-'}</text>

  <text x="583" y="70" font-family="Segoe UI, sans-serif" font-size="34" font-weight="bold" fill="#FF3B6B" text-anchor="middle">{longest}</text>
  <text x="583" y="98" font-family="Segoe UI, sans-serif" font-size="14" fill="#FF3B6B" text-anchor="middle">Longest Streak</text>
  <text x="583" y="120" font-family="Segoe UI, sans-serif" font-size="12" fill="#9aa4b2" text-anchor="middle">{range_label}</text>
</svg>"""
    return svg

if __name__ == "__main__":
    days, total = fetch_days()
    current_streak, longest, best_start, best_end, last_active_date = compute_streaks(days)
    svg = render_svg(total, current_streak, longest, (best_start, best_end), last_active_date)
    with open("streak-card.svg", "w") as f:
        f.write(svg)
    print(f"total={total} current={current_streak} longest={longest} range={best_start}-{best_end}")
