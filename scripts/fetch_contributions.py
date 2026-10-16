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


def orgs_from_config():
    try:
        with open(os.path.join(ROOT, "profile.config.json")) as f:
            return json.load(f).get("orgs", [])
    except OSError:
        return []


def fetch_org(user, org, since):
    """Commits authored by `user` in public repos of `org` since `since` (YYYY-MM-DD).

    Uses the commit search API (works with the workflow's built-in GITHUB_TOKEN, or
    unauthenticated at a lower rate limit). Never raises: on any failure it returns
    what it has so the daily job still refreshes the main heatmap.
    """
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-bot"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    per_day, repos = {}, {}
    q = f"author:{user} org:{org} author-date:>={since}"
    try:
        for page in range(1, 11):
            r = requests.get(
                "https://api.github.com/search/commits",
                params={"q": q, "per_page": 100, "page": page},
                headers=headers,
                timeout=30,
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            for it in items:
                day = it["commit"]["author"]["date"][:10]
                per_day[day] = per_day.get(day, 0) + 1
                name = it.get("repository", {}).get("name", "?")
                repos[name] = repos.get(name, 0) + 1
            if len(items) < 100:
                break
    except Exception as e:
        print(f"warning: could not fetch {org} commits ({type(e).__name__}: {e})")
    return {"days": per_day, "repos": repos, "total": sum(per_day.values())}


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
    since = days[0]["date"]
    org_data = {o: fetch_org(user, o, since) for o in orgs_from_config()}
    out = {
        "username": user,
        "generated": dt.datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats(days),
        "orgs": org_data,
    }
    for o, v in org_data.items():
        print(f"{o}: {v['total']} commits on {len(v['days'])} days")
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "contributions.json"), "w") as f:
        json.dump(out, f)
    print(f"{user}: {out['stats']['total']} contributions, {len(days)} days")
