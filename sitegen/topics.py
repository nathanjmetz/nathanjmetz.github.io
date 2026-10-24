"""The topics on the site, and where each one gets its news.

To add a topic: copy one block below, give it a new slug, list its feeds,
and (for a sports team) add its ESPN team id. Everything else is automatic.

Filters on a source:
  must  - keep an item only if at least one of these patterns appears
  also  - and at least one of these too (for wide sources like Google News)
  never - drop an item if any of these patterns appears
  limit - most items this source may keep at once (newest win)
Patterns are checked (case-insensitive) against the title, tags, summary
and link of each item.
"""

# Sports that should never show up in a single-sport topic.
OTHER_SPORTS = [
    r"\bvolleyball\b", r"\bsoccer\b", r"\bhockey\b", r"\blacrosse\b",
    r"\bbaseball\b", r"\bsoftball\b", r"\bswim", r"\bfencing\b",
    r"\bgolf\b", r"\btennis\b", r"\browing\b", r"\bcross country\b",
    r"\btrack and field\b", r"\bwrestling\b",
]

# High schools named Notre Dame turn up in "Notre Dame" searches.
HIGH_SCHOOL = [r"\bH\.\s?S\.", r"homecoming", r"Notre Dame (Academy|High|College Prep|Prep)\b",
               r"Green Bay Notre Dame"]

# College football has no exhibitions, so "exhibition" means another sport.
NOT_FOOTBALL = [r"basketball", r"\bexhibition\b", r"women's"] + OTHER_SPORTS + HIGH_SCHOOL

# Words that only show up in basketball stories.
HOOPS_WORDS = [r"basketball", r"\bhoops\b", r"DeVries", r"\bexhibition\b",
               r"Assembly Hall", r"Bob(by)? Knight", r"March Madness"]

TOPICS = [
    {
        "slug": "nd-football",
        "name": "Notre Dame Football",
        "short": "ND Football",
        "kicker": "Fighting Irish",
        "color": "#0c2340",       # team color on light backgrounds
        "color_dark": "#c9a94f",  # team color on dark backgrounds
        "espn": {"sport": "football", "league": "college-football", "team_id": 87},
        "sources": [
            {
                "name": "Fighting Irish Athletics",
                "kind": "Official",
                "home": "https://fightingirish.com/sports/football",
                "feed": "https://fightingirish.com/sports/football/rss",
            },
            {
                "name": "Blue & Gold (On3)",
                "kind": "Team site",
                "home": "https://www.on3.com/teams/notre-dame-fighting-irish/",
                "feed": "https://www.on3.com/teams/notre-dame-fighting-irish/feed/",
                "must": [r"Blue and Gold Football"],
                "never": NOT_FOOTBALL,
            },
            {
                "name": "One Foot Down",
                "kind": "Fan site",
                "home": "https://www.onefootdown.com",
                "feed": "https://www.onefootdown.com/rss/index.xml",
                "must": [r"football"],
                "never": NOT_FOOTBALL,
            },
            {
                "name": "Slap the Sign",
                "kind": "Fan site",
                "home": "https://slapthesign.com",
                "feed": "https://slapthesign.com/feed/",
                "must": [r"notre-dame-football", r"Notre Dame football", r"Freeman"],
                "never": NOT_FOOTBALL,
            },
            {
                "name": "ESPN",
                "kind": "National",
                "home": "https://www.espn.com/college-football/team/_/id/87/notre-dame-fighting-irish",
                "feed": "https://www.espn.com/espn/rss/ncf/news",
                "must": [r"Notre Dame", r"Fighting Irish"],
                "never": NOT_FOOTBALL,
            },
            {
                "name": "Google News",
                "kind": "Around the web",
                "home": "https://news.google.com/search?q=%22Notre%20Dame%22%20football",
                "feed": "https://news.google.com/rss/search?q=%22Notre+Dame%22+football+when:7d&hl=en-US&gl=US&ceid=US:en",
                "limit": 40,
                "must": [r"Notre Dame", r"Fighting Irish"],
                "never": NOT_FOOTBALL,
            },
        ],
    },
    {
        "slug": "iu-basketball",
        "name": "IU Basketball",
        "short": "IU Hoops",
        "kicker": "Indiana Hoosiers",
        "color": "#990000",
        "color_dark": "#ef6b62",
        "espn": {"sport": "basketball", "league": "mens-college-basketball", "team_id": 84},
        "sources": [
            {
                "name": "IU Athletics",
                "kind": "Official",
                "home": "https://iuhoosiers.com/sports/mens-basketball",
                "feed": "https://iuhoosiers.com/rss?path=mbball",
            },
            {
                "name": "Inside the Hall",
                "kind": "Team site",
                "home": "https://www.insidethehall.com",
                "feed": "https://www.insidethehall.com/feed/",
                "never": [r"\bfootball\b", r"women's", r"\bWBB\b"] + OTHER_SPORTS,
            },
            {
                "name": "The Daily Hoosier",
                "kind": "Team site",
                "home": "https://thedailyhoosier.com",
                "feed": "https://thedailyhoosier.com/feed/",
                "must": HOOPS_WORDS,
                "never": [r"\bfootball\b", r"women's"] + OTHER_SPORTS,
            },
            {
                "name": "The Hoosier (On3)",
                "kind": "Team site",
                "home": "https://www.on3.com/teams/indiana-hoosiers/",
                "feed": "https://www.on3.com/teams/indiana-hoosiers/feed/",
                "must": [r"The Hoosier Basketball", r"Indiana Basketball"],
            },
            {
                "name": "The Crimson Quarry",
                "kind": "Fan site",
                "home": "https://www.crimsonquarry.com",
                "feed": "https://www.crimsonquarry.com/rss/index.xml",
                "must": HOOPS_WORDS,
                "never": [r"\bfootball\b", r"women's"] + OTHER_SPORTS,
            },
            {
                "name": "Hoosier State of Mind",
                "kind": "Fan site",
                "home": "https://www.hoosierstateofmind.com",
                "feed": "https://www.hoosierstateofmind.com/feed/",
                "must": HOOPS_WORDS,
                "never": [r"\bfootball\b", r"women's"] + OTHER_SPORTS,
            },
            {
                "name": "ESPN",
                "kind": "National",
                "home": "https://www.espn.com/mens-college-basketball/team/_/id/84/indiana-hoosiers",
                "feed": "https://www.espn.com/espn/rss/ncb/news",
                "must": [r"\bIndiana\b", r"Hoosiers"],
                "never": [r"Indiana State", r"women's"],
            },
            {
                "name": "Google News",
                "kind": "Around the web",
                "home": "https://news.google.com/search?q=Indiana%20Hoosiers%20men%27s%20basketball",
                "feed": "https://news.google.com/rss/search?q=Indiana+Hoosiers+men%27s+basketball+when:7d&hl=en-US&gl=US&ceid=US:en",
                "limit": 40,
                "must": HOOPS_WORDS,
                "also": [r"\bIndiana\b", r"Hoosiers", r"\bIU\b"],
                "never": [r"\bfootball\b", r"women's", r"Indiana State", r"Indiana Fever", r"Indiana Pacers",
                          r"IU (Northwest|Southeast|Kokomo|South Bend|East|Columbus|Indy)", r"IUPUI",
                          r"Purdue Fort Wayne"] + OTHER_SPORTS,
            },
        ],
    },
]
