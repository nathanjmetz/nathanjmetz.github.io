# Nathan's Daily — design tokens

Defined once in `static/style.css` (`:root`). Change them here and there together.

| Token | Light | Dark | Why |
|---|---|---|---|
| `--paper` | `#f7f5f0` | `#131312` | Warm newsprint feel, easier on the eyes than pure white. |
| `--surface` | `#ffffff` | `#1c1c1a` | Cards sit one step above the page. |
| `--ink` / `--ink-2` / `--ink-3` | `#1b1b1a` / `#4a4945` / `#66645e` | `#eceae4` / `#bdbab1` / `#9d9a91` | Headline, body, and small print. All pass WCAG AA on paper and surface. |
| `--rule` | `#dedad0` | `#34322d` | Hairlines between stories. |
| `--win` / `--loss` | `#1d6b40` / `#a3271c` | `#5cc28a` / `#f07a6e` | Game results, readable for color-blind users because W/L letters always show too. |
| Team color | set per topic in `sitegen/topics.py` (`color`, `color_dark`) | | Each topic keeps its own school color. ND navy turns gold in dark mode so it stays visible. |

**Type:** Newsreader (headlines, a newspaper serif) and Public Sans (everything else, a plain public-service sans). Fluid sizes `--step--1` to `--step-3` scale with the screen.

**Shape:** 10 px corners on cards, 8 px on buttons, 999 px on chips. Flat color, no gradients.

**Layout:** content caps at 1920 px and centers, with fluid side gutters (16–48 px). Grids use `auto-fit`/`auto-fill`, so they add columns as the screen widens. Checked at 390, 768, 1280, 1920, 2560 and 3440 px.

**Motion:** hover and press changes take 0.15 s ease-out. Off when the reader asks for reduced motion.

**References:** The Athletic team pages (team color stripe, last/next game strip), Apple News "Today" (one lead story, quiet list below), ESPN team schedule (date | opponent | result rows).
