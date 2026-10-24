"""Turn data/*.json into the finished website in _site/.

Reads only saved data, never the network, so a build always shows the last
good pull.
"""

import json
import shutil
from datetime import datetime, timedelta, timezone
from itertools import groupby
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .topics import TOPICS

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT = ROOT / "_site"
EASTERN = ZoneInfo("America/New_York")
HOME_HEADLINES = 6


def eastern(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(EASTERN)


def fmt_day(iso):
    d = eastern(iso)
    return f"{d:%A}, {d:%b} {d.day}"


def fmt_short_day(iso):
    d = eastern(iso)
    return f"{d:%a}, {d:%b} {d.day}"


def fmt_time(iso):
    d = eastern(iso)
    return d.strftime("%I:%M %p").lstrip("0")


def fmt_stamp(iso):
    return f"{fmt_short_day(iso)} at {fmt_time(iso)} ET"


def game_line(game):
    """'vs. #12 BYU' / 'at Syracuse' — the opponent as a fan would say it."""
    where = "at" if game["site"] == "away" else "vs."
    rank = f"#{game['opponent_rank']} " if game.get("opponent_rank") else ""
    return f"{where} {rank}{game['opponent_short']}"


def result_text(game):
    if game["state"] == "final" and game["our_score"] is not None:
        letter = "W" if game["won"] else "L"
        return f"{letter} {game['our_score']}–{game['their_score']}"
    if game["state"] == "live":
        return f"Live: {game['our_score']}–{game['their_score']}"
    if game["state"] == "off":
        return game.get("status_text") or "Postponed"
    return None


def kickoff_text(game):
    day = fmt_short_day(game["date"])
    return f"{day} · {fmt_time(game['date'])} ET" if game["time_set"] else f"{day} · Time TBA"


def prepare(topic, now, data_dir=DATA_DIR):
    path = data_dir / f"{topic['slug']}.json"
    data = json.loads(path.read_text()) if path.exists() else {"news": [], "schedule": None, "sources": {}}

    news = data.get("news", [])
    days = [
        {"label": fmt_day(day_items[0]["published"]), "items": day_items}
        for _, day_items in (
            (k, list(g)) for k, g in groupby(news, key=lambda i: eastern(i["published"]).date())
        )
    ]

    schedule = data.get("schedule") or {"games": [], "record": None, "season": None}
    games = schedule.get("games", [])
    upcoming = [g for g in games if g["state"] in ("scheduled", "live")
                and datetime.fromisoformat(g["date"].replace("Z", "+00:00")) > now - timedelta(hours=6)]
    finals = [g for g in games if g["state"] == "final"]

    source_counts = {}
    for item in news:
        source_counts[item["source"]] = source_counts.get(item["source"], 0) + 1

    sources = []
    for s in topic["sources"]:
        status = data.get("sources", {}).get(s["name"], {})
        sources.append({**s, "ok": status.get("ok", True), "shown": source_counts.get(s["name"], 0)})

    return {
        **topic,
        "updated": data.get("updated"),
        "news": news,
        "days": days,
        "headlines": news[:HOME_HEADLINES],
        "schedule": schedule,
        "next_game": upcoming[0] if upcoming else None,
        "last_game": finals[-1] if finals else None,
        "sources": sources,
        "espn_url": next((s["home"] for s in topic["sources"] if s["name"] == "ESPN"), None),
    }


def build(out=OUT, now=None, data_dir=DATA_DIR):
    now = now or datetime.now(timezone.utc)
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        day=fmt_day, short_day=fmt_short_day, time=fmt_time, stamp=fmt_stamp,
        game_line=game_line, result=result_text, kickoff=kickoff_text,
    )

    topics = [prepare(t, now, data_dir) for t in TOPICS]
    stamps = [t["updated"] for t in topics if t["updated"]]
    site = {
        "topics": topics,
        "updated": max(stamps) if stamps else None,
        "built": now.isoformat(),
        "today": fmt_day(now.isoformat()),
        "year": now.year,
    }

    # ignore_errors: macOS drives can leave "._" shadow files mid-delete
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "static", out / "static", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("._*", ".DS_Store"))
    (out / ".nojekyll").write_text("")

    def write(rel, template, **ctx):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(env.get_template(template).render(site=site, **ctx))

    write("index.html", "home.html", page="home")
    write("404.html", "404.html", page="404")
    for topic in topics:
        write(f"{topic['slug']}/index.html", "topic.html", page=topic["slug"], topic=topic)
        if topic.get("espn"):
            write(f"{topic['slug']}/schedule/index.html", "schedule.html", page=topic["slug"], topic=topic)
    return out


if __name__ == "__main__":
    print(f"Built {build()}")
