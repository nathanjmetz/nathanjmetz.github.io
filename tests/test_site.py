"""Checks for the news puller and the site builder.

They run on saved copies of real feeds (tests/fixtures), never the live web,
so they give the same answer every time.
"""

import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

import pytest

from sitegen import build, fetch
from sitegen.topics import TOPICS

FIX = Path(__file__).parent / "fixtures"
ND = next(t for t in TOPICS if t["slug"] == "nd-football")
IU = next(t for t in TOPICS if t["slug"] == "iu-basketball")


def source(topic, name):
    return next(s for s in topic["sources"] if s["name"] == name)


def parsed(fixture, topic, name):
    src = source(topic, name)
    return src, fetch.parse_feed((FIX / fixture).read_bytes(), src)


# ---------- reading feeds ----------

def test_google_news_titles_lose_the_outlet_suffix():
    _, items = parsed("google_nd.xml", ND, "Google News")
    assert items
    for item in items:
        assert item["outlet"], "Google items should name the real outlet"
        assert not item["title"].endswith(" - " + item["outlet"])
        assert item["link"].startswith("https://")


def test_every_item_has_title_link_and_time():
    for fixture, topic, name in [
        ("google_nd.xml", ND, "Google News"),
        ("onefootdown.xml", ND, "One Foot Down"),
        ("dailyhoosier.xml", IU, "The Daily Hoosier"),
    ]:
        _, items = parsed(fixture, topic, name)
        assert items, fixture
        for item in items:
            assert item["title"] and item["link"].startswith("http")
            datetime.fromisoformat(item["published"])
            assert len(item["summary"]) <= fetch.SUMMARY_CHARS + 1


def test_nd_football_drops_other_sports():
    src, items = parsed("onefootdown.xml", ND, "One Foot Down")
    kept = [i for i in items if fetch.keep(i, src)]
    assert any("Women's Basketball" in i["tags"] for i in items), "fixture should hold a basketball story"
    assert kept and len(kept) < len(items)
    assert not any("basketball" in " ".join(i["tags"]).lower() for i in kept)


def test_iu_basketball_drops_football():
    src, items = parsed("dailyhoosier.xml", IU, "The Daily Hoosier")
    kept = [i for i in items if fetch.keep(i, src)]
    assert any("IU Football" in i["tags"] for i in items), "fixture should hold a football story"
    assert kept
    for i in kept:
        assert "IU Football" not in i["tags"]
        assert not re.search(r"\bfootball\b", i["title"], re.I)


def test_filter_rules():
    src = {"must": [r"basketball"], "also": [r"Indiana"], "never": [r"football"]}
    item = lambda title: {"title": title, "tags": [], "summary": "", "link": "https://x.test/a"}
    assert fetch.keep(item("Indiana basketball wins"), src)
    assert not fetch.keep(item("Purdue basketball wins"), src)        # fails "also"
    assert not fetch.keep(item("Indiana volleyball wins"), src)       # fails "must"
    assert not fetch.keep(item("Indiana basketball and football"), src)  # hits "never"


def test_nd_football_skips_high_schools_named_notre_dame():
    src = source(ND, "Google News")
    item = lambda t: {"title": t, "tags": [], "summary": "", "link": "https://x.test"}
    assert not fetch.keep(item("H.S. FOOTBALL: Geedy's hat trick shocks Notre Dame, upsets homecoming night"), src)
    assert not fetch.keep(item("Green Bay Notre Dame cheers West football team on the way to game"), src)
    assert fetch.keep(item("Notre Dame football: Do the Irish play today?"), src)


def test_google_news_for_iu_skips_other_iu_campuses():
    src = source(IU, "Google News")
    item = {"title": "IU Northwest men's basketball targets 2026-27 season", "tags": [], "summary": "", "link": "https://x.test"}
    assert not fetch.keep(item, src)


# ---------- merging ----------

def make(title, link, source, hours_ago, now):
    return {"title": title, "link": link, "source": source, "outlet": None,
            "published": (now - timedelta(hours=hours_ago)).isoformat(), "summary": "", "tags": []}


def test_merge_dedupes_keeps_best_source_and_sorts():
    now = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
    rank = {"Official": 0, "Google News": 9}
    old = [make("Irish win big", "https://a.test/1", "Official", 30, now)]
    new = [
        make("Irish win big", "https://a.test/1", "Official", 30, now),          # same link
        make("Irish Win Big!", "https://g.test/x", "Google News", 29, now),      # same headline
        make("New story", "https://b.test/2", "Google News", 1, now),
        make("Too old", "https://b.test/3", "Google News", 24 * (fetch.KEEP_DAYS + 1), now),
    ]
    merged = fetch.merge_news(old, new, now, rank)
    assert [i["title"] for i in merged] == ["New story", "Irish win big"]
    assert merged[1]["source"] == "Official"


def test_merge_caps_the_list():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    many = [make(f"Story {n}", f"https://a.test/{n}", "X", n * 0.1, now) for n in range(fetch.MAX_ITEMS + 40)]
    merged = fetch.merge_news([], many, now, {})
    assert len(merged) == fetch.MAX_ITEMS
    assert merged[0]["title"] == "Story 0"


def test_merge_limits_one_source():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    wide = [make(f"Wide {n}", f"https://g.test/{n}", "Google News", n, now) for n in range(30)]
    team = [make(f"Team {n}", f"https://t.test/{n}", "Team", n, now) for n in range(5)]
    merged = fetch.merge_news([], wide + team, now, {"Team": 0, "Google News": 1}, {"Google News": 10})
    assert sum(i["source"] == "Google News" for i in merged) == 10
    assert sum(i["source"] == "Team" for i in merged) == 5
    assert "Wide 0" in [i["title"] for i in merged]  # newest kept


# ---------- schedules ----------

def test_nd_schedule_reads_results():
    sched = fetch.parse_schedule([json.loads((FIX / "espn_schedule_nd.json").read_text())], 87)
    games = sched["games"]
    assert len(games) == 12 and sched["record"] == "6-1"
    assert [g["date"] for g in games] == sorted(g["date"] for g in games)
    finals = [g for g in games if g["state"] == "final"]
    assert finals and all(g["our_score"] is not None and isinstance(g["won"], bool) for g in finals)
    wins = sum(g["won"] for g in finals)
    assert f"{wins}-{len(finals) - wins}" == sched["record"]
    assert games[0]["site"] == "neutral"  # Wisconsin at Lambeau Field
    assert all(g["link"].startswith("https://www.espn.com/") for g in games)


def test_iu_schedule_before_the_season():
    sched = fetch.parse_schedule([json.loads((FIX / "espn_schedule_iu.json").read_text())], 84)
    assert len(sched["games"]) > 20
    assert all(g["our_score"] is None for g in sched["games"] if g["state"] == "scheduled")
    empty = fetch.parse_schedule([json.loads((FIX / "espn_schedule_iu_preseason.json").read_text())], 84)
    assert empty["games"] == []


# ---------- the built site ----------

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs).get("href"))


def links_in(path):
    p = Links()
    p.feed(path.read_text())
    return p.hrefs


@pytest.fixture
def built(tmp_path):
    now = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for topic, fixture, team_id, feeds in [
        (ND, "espn_schedule_nd.json", 87, [("google_nd.xml", "Google News"), ("onefootdown.xml", "One Foot Down")]),
        (IU, "espn_schedule_iu.json", 84, [("dailyhoosier.xml", "The Daily Hoosier")]),
    ]:
        items = []
        for f, name in feeds:
            src, parsed_items = parsed(f, topic, name)
            items += [i for i in parsed_items if fetch.keep(i, src)]
        news = fetch.merge_news([], items, now, {})
        sched = fetch.parse_schedule([json.loads((FIX / fixture).read_text())], team_id)
        (data_dir / f"{topic['slug']}.json").write_text(json.dumps(
            {"updated": now.isoformat(), "news": news, "schedule": sched, "sources": {}}))
    out = build.build(out=tmp_path / "site", now=now, data_dir=data_dir)
    return out, data_dir


def test_build_makes_every_page(built):
    out, _ = built
    for rel in ["index.html", "404.html", "nd-football/index.html", "nd-football/schedule/index.html",
                "iu-basketball/index.html", "iu-basketball/schedule/index.html", "static/style.css"]:
        assert (out / rel).exists(), rel


def test_every_story_is_a_link_to_its_source(built):
    out, data_dir = built
    for topic in TOPICS:
        news = json.loads((data_dir / f"{topic['slug']}.json").read_text())["news"]
        hrefs = set(links_in(out / topic["slug"] / "index.html"))
        assert news
        for item in news:
            assert item["link"] in hrefs, item["title"]


def test_every_link_goes_somewhere_real(built):
    out, _ = built
    for page in out.rglob("*.html"):
        for href in links_in(page):
            assert href and href != "#", f"empty link on {page}"
            if href.startswith("http") or (href.startswith("#") and len(href) > 1):  # in-page jumps
                continue
            target = out / href.lstrip("/")
            assert target.exists() or (target / "index.html").exists(), f"{href} on {page}"


def test_schedule_shows_results_and_next_game(built):
    out, _ = built
    html = (out / "nd-football" / "schedule" / "index.html").read_text()
    assert "W 41–13" in html and "L 24–28" in html
    assert html.count('class="tag">Next') == 1


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_wiki_references_all_resolve():
    root = Path(__file__).parent.parent
    run = subprocess.run(["node", str(root / "tests" / "wikicheck.js"), str(root / "ai" / "index.html")],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_build_includes_the_wiki(built):
    out, _ = built
    page = (out / "ai" / "index.html").read_text()
    assert page.startswith("<!doctype html>") and "Nathan's AI Wiki" in page
    assert 'href="/ai/"' in (out / "index.html").read_text()


def test_empty_topic_says_so(tmp_path):
    out = build.build(out=tmp_path / "site", data_dir=tmp_path)  # no data files at all
    home = (out / "index.html").read_text()
    assert "No stories in the last two weeks" in home
    sched = (out / "nd-football" / "schedule" / "index.html").read_text()
    assert "schedule isn't posted yet" in sched
