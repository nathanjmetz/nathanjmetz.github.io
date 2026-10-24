# Daily sports pages — spec (2026-10-24)

**Purpose (one sentence Nathan would say aloud):** "Every morning I can see what's new with Notre Dame football and IU basketball, and tap any story to read it where it came from."
**Who uses it:** Nathan, on his phone or computer. Public, but not promoted.
**The one main thing on the screen:** today's headlines for each team.

## What it does
- Front page: one card per topic with last game, next game, and the six newest stories.
- Topic page: every story from the last 14 days, grouped by day, with buttons to show one source at a time, and a list of every source used.
- Schedule page: the season, game by game, with results, TV, and the next game marked. Each game opens its ESPN game page.
- Every headline opens the original story. Game cards open the schedule page.
- A GitHub Action pulls news every morning at 6:17 AM Eastern, saves it, rebuilds and republishes the site.

**Nathan's words (2026-10-24):** "Everything should be able to be clicked to either go to the link where you got it or to explore the way that you've curated certain things like our season schedule."

## What it does NOT do (this round)
- No AI summaries. Headlines and the feed's own short blurbs only.
- No photos (they would come from other sites' servers and break often).
- No sign-in, no comments, nothing stored about visitors.

## Data and access
- Stores only public headlines, links and schedules in `data/*.json`, kept 14 days. No personal data. No keys or secrets.

## States
- Empty: "No stories in the last two weeks…" / "The schedule isn't posted yet…" with a link to ESPN.
- Error: if a source can't be reached, its old stories stay and the source list says "Couldn't reach it this morning."
- Success: the pages above. (No loading state: pages are built ahead of time.)

## Done when (Nathan can click through this himself)
1. Open nathanjmetz.github.io. Both team cards show stories from the last day or two.
2. Tap any headline. It opens that story on the original site.
3. Tap "Season schedule" on ND. The next game is marked "Next." Tap a game: ESPN's page for it opens.
4. On the ND page, tap "One Foot Down." Only their stories show.
5. Tomorrow after 6:30 AM, the "Last updated" line at the bottom shows tomorrow's date.
