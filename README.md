# English Premier League Weekly Schedule

A small, dependency-free season tool that turns fixture JSON into a polished,
print-ready HTML guide. Every gameweek starts on a new letter-size page, and
kickoffs are converted from UTC to `America/Chicago` (so the correct CDT/CST
abbreviation is used across the season).

Club names, venues, the competition, and UI labels render bilingually (English
with a Chinese gloss). Type is sized large for easy reading, and each match is
one row with a 比分 score box to fill in by hand. One matchweek prints per
letter-size sheet.

![Gameweek 1 sample page](screenshot.png)

## Run it

```bash
python3 generate_schedule.py schedule.json --output schedule.html
open schedule.html # or open it in a browser and choose Print → Save as PDF
```

Create alternate visual mockups with `--theme dark` or `--theme compact`.

**Printing / pagination.** Each printed sheet holds `--per-page` matches
(default 10 → one whole matchweek per page). Every matchweek starts on a fresh
sheet and no match is split across a break. Each match is one row: date, both
clubs (English + Chinese on one line each), kickoff time, and a 比分 score box
to fill in by hand. Lower `--per-page` (e.g. 5) for fewer, larger rows per page.
On-screen tabs and search never print.

**Render a PDF.** Printing from the browser works, but `render_pdf.cjs` produces
a print-exact PDF headlessly via Chromium (Playwright), injecting a CJK font by
`file://` so Chinese renders without any system font setup:

```bash
node render_pdf.cjs schedule.html schedule.pdf
```

It prints a warning if any matchweek exceeds one sheet. See the file header for
the env overrides (`CHROME`, `PW_CORE`, `CJK_REG`/`CJK_BOLD`); set `TMPDIR` to a
short path and `LD_LIBRARY_PATH` if Chromium needs bundled libs.

Each fixture in `schedule.json` needs `gameweek`, an ISO-8601 `kickoff` with a
timezone, `home`, and `away`; `venue` is optional. Optional top-level
`competition_zh` and a `translations` block (`teams` and `venues` maps from
English name to Chinese) drive the Chinese glosses; any entry left out simply
renders English only. Use `--timezone America/Chicago` (the default) or any IANA
timezone supported by Python's `zoneinfo`.

## Importing a real season

`schedule.json` is generated from an [openfootball](https://github.com/openfootball/england)
season file, which mirrors the officially released fixture list. `import_fixtures.py`
parses it into the schema above — mapping every club to its crest and Chinese
name, converting UK-local kickoffs to UTC, and dropping the simulated final
scores openfootball appends (this schedule is for writing goals in by hand):

```bash
curl -sO https://raw.githubusercontent.com/openfootball/england/master/2026-27/1-premierleague.txt
python3 import_fixtures.py 1-premierleague.txt --season 2026/27 -o schedule.json
python3 generate_schedule.py schedule.json --output schedule.html
```

The current `schedule.json` is the full 2026/27 Premier League — all 380
fixtures across 38 matchweeks. Spot-checked against press fixture releases
(e.g. Matchday 1: Arsenal v Coventry City, Fri 21 Aug 2026). **Caveat on
kickoff times:** the Premier League only confirms exact kickoff times a few
weeks ahead for TV; times for later matchweeks in the source are the provisional
weekend/midweek slots and will shift as broadcast picks are announced. The
match pairings and matchweek dates are the released schedule.

To add a club (e.g. after promotion) extend the `CLUBS` map in
`import_fixtures.py`. The `competition` field also lets the same generator drive
other competitions (Champions League, etc.) from a different data file.

## Interactive page

The generated page includes gameweek tabs, club search, and editable score
boxes. Club crests use the [luukhopman/football-logos](https://github.com/luukhopman/football-logos)
current-season set via jsDelivr. The badges are shown for identification in this
prototype; confirm licensing before distributing a production version.
