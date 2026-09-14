# premier league schedule to pdf

i vibe coded this for my gramps

![gameweek 1](screenshot.png)

## make it

```bash
python3 generate_schedule.py schedule.json --output schedule.html
node render_pdf.cjs schedule.html schedule.pdf   # print-exact pdf
```

or just open `schedule.html` in a browser and print → save as pdf.
`schedule.pdf` in this repo is the full 2026/27 season, all 38 weeks.

## fresh fixtures

the data comes from [openfootball](https://github.com/openfootball/england).
kickoff times are only real for the first ~9 weeks — after that the premier
league hasn't set tv times yet, so everything shows the default saturday slot.
pairings and dates are the real released schedule.

```bash
curl -sO https://raw.githubusercontent.com/openfootball/england/master/2026-27/1-premierleague.txt
python3 import_fixtures.py 1-premierleague.txt --season 2026/27 -o schedule.json
```

crests are from [luukhopman/football-logos](https://github.com/luukhopman/football-logos).
