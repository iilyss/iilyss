#!/usr/bin/env python3
"""Generate a Duolingo-style GitHub streak card (SVG).

Usage:
  GH_TOKEN=xxx GH_USER=username python streak.py   # real data
  python streak.py --demo                          # sample preview
Output: assets/streak.svg
"""
import json, os, sys, urllib.request
from datetime import date, timedelta

OUT = "assets/streak.svg"
QUERY = """
query($login:String!){ user(login:$login){ contributionsCollection{
  contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }
"""


def fetch_days(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def demo_days():
    today = date.today()
    days = {}
    for i in range(365):
        d = today - timedelta(days=i)
        days[d.isoformat()] = 0 if i in (0, 40, 41, 90) else (i % 5) + 1
    return days


def stats(days):
    today = date.today()
    # Like Duolingo: streak is still alive if you haven't committed *yet* today
    cur, d = 0, today if days.get(today.isoformat(), 0) else today - timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        cur += 1
        d -= timedelta(days=1)
    best = run = 0
    for k in sorted(days):
        run = run + 1 if days[k] > 0 else 0
        best = max(best, run)
    total = sum(days.values())
    week = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    return cur, best, total, today, week


FLAME = ("M0,-34 C10,-22 22,-12 22,4 C22,20 12,30 0,30 C-12,30 -22,20 -22,4 "
         "C-22,-6 -16,-12 -12,-18 C-10,-10 -6,-6 -2,-6 C-6,-18 -4,-26 0,-34 Z")
FLAME_IN = "M0,-2 C6,6 10,12 10,18 C10,25 5,29 0,29 C-5,29 -10,25 -10,18 C-10,12 -6,8 0,-2 Z"


def render(cur, best, total, today, week, days):
    active = cur > 0
    fire, fire_in = ("#FF9600", "#FFC800") if active else ("#CFCFCF", "#E5E5E5")
    num_color = "#FF9600" if active else "#AFAFAF"
    msg = "Keep the flame alive!" if active else "Commit today to start a streak!"
    dots = []
    for i, d in enumerate(week):
        x = 200 + i * 44
        done = days.get(d.isoformat(), 0) > 0
        is_today = d == today
        label = "MTWTFSS"[d.weekday()]
        lc = "#FF9600" if is_today else "#AFAFAF"
        dots.append(f'<text x="{x}" y="122" class="day" fill="{lc}">{label}</text>')
        if done:
            dots.append(f'<circle cx="{x}" cy="146" r="15" fill="#FF9600"/>'
                        f'<path d="M{x-6},146 l4,5 l9,-10" stroke="#fff" stroke-width="3.5" '
                        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        elif is_today:
            dots.append(f'<circle cx="{x}" cy="146" r="14" fill="none" stroke="#FF9600" '
                        f'stroke-width="3" stroke-dasharray="4 4"/>')
        else:
            dots.append(f'<circle cx="{x}" cy="146" r="15" fill="#E5E5E5"/>')
    anim = ('<animateTransform attributeName="transform" type="scale" values="1;1.06;1" '
            'dur="1.6s" repeatCount="indefinite" additive="sum"/>') if active else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="200" viewBox="0 0 520 200">
<style>
  .f{{font-family:'Nunito','Segoe UI',Helvetica,Arial,sans-serif;font-weight:800}}
  .day{{font:800 13px 'Nunito','Segoe UI',Helvetica,Arial,sans-serif;text-anchor:middle}}
</style>
<rect x="1.5" y="1.5" width="517" height="197" rx="18" fill="#fff" stroke="#E5E5E5" stroke-width="3"/>
<g transform="translate(88,70)"><g>{anim}
  <path d="{FLAME}" fill="{fire}"/><path d="{FLAME_IN}" fill="{fire_in}"/></g></g>
<text x="88" y="150" class="f" font-size="44" fill="{num_color}" text-anchor="middle">{cur}</text>
<text x="88" y="176" class="f" font-size="14" fill="{num_color}" text-anchor="middle">DAY STREAK</text>
<text x="178" y="48" class="f" font-size="20" fill="#3C3C3C">{msg}</text>
<text x="178" y="80" class="f" font-size="14" fill="#777">Longest: {best} day{'s' if best != 1 else ''}  ·  {total} contribution{'s' if total != 1 else ''}</text>
{''.join(dots)}
</svg>'''


def main():
    if "--demo" in sys.argv:
        days = demo_days()
    else:
        days = fetch_days(os.environ["GH_USER"], os.environ["GH_TOKEN"])
    cur, best, total, today, week = stats(days)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(cur, best, total, today, week, days))
    print(f"streak={cur} best={best} total={total} -> {OUT}")


if __name__ == "__main__":
    main()
