# Nathan's Daily (nathanjmetz.github.io)

Read `START-HERE.md` first: it holds what's live, what's next, and what's waiting on Nathan.

## Rules for this project
- Static site, no server, no database, no secrets. Keep it that way unless Nathan agrees otherwise.
- Every story links to its original source. Curated pages (like schedules) cite their data source on the page.
- Add a topic by adding a block to `sitegen/topics.py`. Don't copy logic per topic.
- The AI wiki is one page, `ai/index.html` (served at /ai/). Its entries, sources and Nathan's-way boxes are data at the top of its script. Run `node tests/wikicheck.js ai/index.html` after any edit.
- Nathan's tool choices may be public (Nathan, 2026-10-24: "There's nothing sensitive about me putting in a public place that I use Supabase"). Never personal data: no calendar, family, or TLC people and records.
- Design values live in `DESIGN.md`. No one-off colors.
- Before pushing: `pytest -q`, `python -m sitegen.build`, and look at the pages at 390, 768, 1280, 1920, 2560 and 3440 px, light and dark.
- `data/` is written by the daily job. Don't hand-edit it.
- This folder is on an external (exFAT) drive, which makes `._*` shadow files. They're ignored by git; leave them.

## Known corners cut
- ESPN's schedule feed is public but unofficial. If ESPN changes it, schedules stop updating (old ones stay) until `parse_schedule` is fixed.
- Filters use keywords and coach names (e.g. "DeVries"). Update them if a coach changes.
- Google News often lists the same event from several outlets. Capped at 40 items per topic.
- The wiki's "Nathan's way" boxes and "Where I'm active" table are copied by hand from the private rulebook (`claude-config`: `choices/`, `in-use/`). Change the rulebook first, then copy. Reading it automatically would need a read-only key for that private repo.
