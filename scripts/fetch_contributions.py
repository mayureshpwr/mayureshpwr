"""Fetch the public contribution calendar (no token needed) -> data/contributions.json"""
import json, os, re, sys, datetime as dt
import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def username():
    u = os.environ.get("GH_USERNAME")
    if u:
        return u
    with open(os.path.join(ROOT, "profile.config.json")) as f:
        return json.load(f)["username"]


def fetch(user):
    r = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=30,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td[data-date]"):
        text = tips.get(td.get("id"), "")
        m = re.match(r"(\d+)\s+contribution", text)
        count = int(m.group(1)) if m else 0
        days.append({"date": td["data-date"], "count": count, "level": int(td.get("data-level", 0))})
    days.sort(key=lambda d: d["date"])
    return days


def stats(days):
    total = sum(d["count"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # current streak: allow today to be empty
    cur = 0
    seq = days[:]
    if seq and seq[-1]["count"] == 0:
        seq = seq[:-1]
    for d in reversed(seq):
        if d["count"]:
            cur += 1
        else:
            break
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    return {
        "total": total,
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": best,
        "monthly": months,
    }


if __name__ == "__main__":
    user = username()
    days = fetch(user)
    if not days:
        sys.exit("No contribution cells found - check the username.")
    out = {
        "username": user,
        "generated": dt.datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats(days),
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "contributions.json"), "w") as f:
        json.dump(out, f)
    print(f"{user}: {out['stats']['total']} contributions, {len(days)} days")
