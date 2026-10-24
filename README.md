# Nathan's Daily

Daily news on the topics Nathan follows, live at **https://nathanjmetz.github.io**.
Every headline links to its original source. Game info comes from ESPN.

- `sitegen/topics.py` — the topics and their news sources (add a topic here)
- `sitegen/fetch.py` — pulls news and schedules into `data/`
- `sitegen/build.py` + `templates/` + `static/` — turns `data/` into the site
- `.github/workflows/daily.yml` — runs it all every morning and publishes

Run it yourself:

    pip install -r requirements.txt
    pytest -q
    python -m sitegen.fetch     # pull fresh data
    python -m sitegen.build     # writes _site/
    python -m http.server 8765 --directory _site
