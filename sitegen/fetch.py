"""Pull fresh news and schedules, and save them to data/<topic>.json.

Each run merges new items into what was saved last time, so a source that is
down for a day costs nothing: its older stories stay, and it catches up the
next day.
"""

import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

from .topics import TOPICS

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

USER_AGENT = "Mozilla/5.0 (compatible; nathanjmetz-daily/1.0; +https://nathanjmetz.github.io)"
KEEP_DAYS = 14        # stories older than this drop off
MAX_ITEMS = 150       # per topic, newest first
SUMMARY_CHARS = 220

ESPN_SCHEDULE = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/schedule"
SEASON_TYPES = [2, 3]  # regular season, postseason


# ---------- news ----------

def get(url, tries=3):
    for attempt in range(1, tries + 1):
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException:
            if attempt == tries:
                raise
            time.sleep(2 * attempt)


def clean_text(raw):
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def shorten(text, limit=SUMMARY_CHARS):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:-–— ")
    return cut + "…"


def entry_time(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime(*parsed[:6], tzinfo=timezone.utc)


def parse_feed(raw, source):
    """Turn raw feed bytes into a list of plain item dicts."""
    feed = feedparser.parse(raw)
    items = []
    for entry in feed.entries:
        title = clean_text(entry.get("title"))
        link = entry.get("link", "").strip()
        when = entry_time(entry)
        if not title or not link or not when:
            continue

        # Google News puts the real outlet in <source> and repeats it at the
        # end of the title ("Headline - Outlet").
        outlet = None
        src = entry.get("source")
        if src and src.get("title"):
            outlet = src["title"].strip()
            suffix = " - " + outlet
            if title.endswith(suffix):
                title = title[: -len(suffix)].strip()

        summary = clean_text(entry.get("summary"))
        if summary.lower().startswith(title.lower()[:40]):
            summary = ""  # some feeds just repeat the headline

        items.append({
            "title": title,
            "link": link,
            "source": source["name"],
            "outlet": outlet,
            "published": when.isoformat(),
            "summary": shorten(summary),
            "tags": [t.get("term", "") for t in entry.get("tags", []) if t.get("term")],
        })
    return items


def keep(item, source):
    """Apply the source's must/never filters."""
    text = " ".join([item["title"], " ".join(item["tags"]), item["summary"], item["link"]])
    for key in ("must", "also"):
        patterns = source.get(key)
        if patterns and not any(re.search(p, text, re.I) for p in patterns):
            return False
    never = source.get("never")
    if never and any(re.search(p, text, re.I) for p in never):
        return False
    return True


def title_key(title):
    return re.sub(r"[^a-z0-9]+", "", title.lower())[:80]


def merge_news(old, new, now, source_rank, limits=None):
    """Combine saved and fresh items: drop old ones, remove duplicates, newest first.

    When two sources carry the same headline, the one listed first in
    topics.py wins (official sites are listed first, Google News last).
    `limits` caps how many items one source may keep, so a wide source
    like Google News can't crowd out the team sites.
    """
    limits = limits or {}
    cutoff = now - timedelta(days=KEEP_DAYS)
    # best source first, and newest first within a source
    pool = sorted(old + new, key=lambda i: i["published"], reverse=True)
    pool.sort(key=lambda i: source_rank.get(i["source"], 99))
    seen_links, seen_titles, out, per_source = set(), set(), [], {}
    for item in pool:
        if datetime.fromisoformat(item["published"]) < cutoff:
            continue
        tkey = title_key(item["title"])
        if item["link"] in seen_links or tkey in seen_titles:
            continue
        seen_links.add(item["link"])
        seen_titles.add(tkey)
        count = per_source.get(item["source"], 0)
        if count >= limits.get(item["source"], MAX_ITEMS):
            continue
        per_source[item["source"]] = count + 1
        out.append(item)
    out.sort(key=lambda i: i["published"], reverse=True)
    return out[:MAX_ITEMS]


# ---------- schedule ----------

def parse_schedule(payloads, team_id):
    """Turn ESPN schedule responses into a simple season list."""
    team_id = str(team_id)
    games, record, season = {}, None, None
    for data in payloads:
        team = data.get("team", {})
        record = team.get("recordSummary") or record
        req = data.get("requestedSeason") or data.get("season") or {}
        season = req.get("displayName") or season
        for event in data.get("events", []):
            comp = event["competitions"][0]
            us = next((c for c in comp["competitors"] if str(c["id"]) == team_id), None)
            them = next((c for c in comp["competitors"] if str(c["id"]) != team_id), None)
            if not us or not them:
                continue
            status = comp["status"]["type"]
            state = {"pre": "scheduled", "in": "live", "post": "final"}.get(status.get("state"), "scheduled")
            if status.get("name") in ("STATUS_POSTPONED", "STATUS_CANCELED"):
                state = "off"

            def score(c):
                s = c.get("score")
                if isinstance(s, dict):
                    s = s.get("displayValue")
                return s

            rank = (them.get("curatedRank") or {}).get("current")
            venue = comp.get("venue") or {}
            address = venue.get("address") or {}
            game_link = next(
                (l["href"] for l in event.get("links", []) if l.get("href", "").startswith("http")),
                None,
            )
            games[event["id"]] = {
                "id": event["id"],
                "date": event["date"],
                "time_set": bool(event.get("timeValid", True)),
                "opponent": them["team"].get("displayName"),
                "opponent_short": them["team"].get("shortDisplayName") or them["team"].get("displayName"),
                "opponent_rank": rank if rank and rank < 99 else None,
                "site": "neutral" if comp.get("neutralSite") else us.get("homeAway", "home"),
                "venue": venue.get("fullName"),
                "city": ", ".join(x for x in [address.get("city"), address.get("state")] if x),
                "tv": [b.get("media", {}).get("shortName") for b in comp.get("broadcasts", []) if b.get("media")],
                "state": state,
                "status_text": status.get("shortDetail"),
                "season_type": (event.get("seasonType") or {}).get("name"),
                "our_score": score(us) if state != "scheduled" else None,
                "their_score": score(them) if state != "scheduled" else None,
                "won": us.get("winner") if state == "final" else None,
                "link": game_link,
            }
    ordered = sorted(games.values(), key=lambda g: g["date"])
    return {"season": season, "record": record, "games": ordered, "source": "ESPN"}


def fetch_schedule(espn):
    base = ESPN_SCHEDULE.format(**espn)
    payloads = [json.loads(get(f"{base}?seasontype={t}")) for t in SEASON_TYPES]
    return parse_schedule(payloads, espn["team_id"])


# ---------- run ----------

def load(slug):
    path = DATA_DIR / f"{slug}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"news": [], "schedule": None}


def update_topic(topic, now):
    saved = load(topic["slug"])
    fresh, status = [], {}
    for source in topic["sources"]:
        try:
            items = [i for i in parse_feed(get(source["feed"]), source) if keep(i, source)]
            fresh.extend(items)
            status[source["name"]] = {"ok": True, "count": len(items)}
        except Exception as exc:  # one bad feed must not stop the rest
            status[source["name"]] = {"ok": False, "error": str(exc)[:200]}
            print(f"  ! {source['name']}: {exc}", file=sys.stderr)

    rank = {s["name"]: n for n, s in enumerate(topic["sources"])}
    limits = {s["name"]: s["limit"] for s in topic["sources"] if s.get("limit")}
    news = merge_news(saved.get("news", []), fresh, now, rank, limits)

    schedule, schedule_ok = saved.get("schedule"), True
    if topic.get("espn"):
        try:
            schedule = fetch_schedule(topic["espn"])
        except Exception as exc:
            schedule_ok = False
            print(f"  ! schedule: {exc}", file=sys.stderr)

    return {
        "updated": now.isoformat(),
        "news": news,
        "schedule": schedule,
        "schedule_ok": schedule_ok,
        "sources": status,
    }


def main():
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    for topic in TOPICS:
        print(f"{topic['name']}…")
        data = update_topic(topic, now)
        ok = sum(1 for s in data["sources"].values() if s["ok"])
        print(f"  {len(data['news'])} stories, {ok}/{len(data['sources'])} sources answered")
        (DATA_DIR / f"{topic['slug']}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
