#!/usr/bin/env python3
"""Convert an openfootball season .txt (e.g. england/2026-27/1-premierleague.txt)
into the schedule.json this project renders.

openfootball encodes the official released fixture list: matchday blocks, each
with dated rows and (UK-local) kickoff times. Some rows also carry a simulated
final score — those are ignored here; this schedule is for filling goals in by
hand. Kickoff times are converted from Europe/London to UTC and written as ISO
"Z" timestamps; generate_schedule.py then localises them for display.

Usage:
    python3 import_fixtures.py 1-premierleague.txt --season 2026/27 -o schedule.json
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LOGO_BASE = "https://cdn.jsdelivr.net/gh/luukhopman/football-logos@master/logos/England%20-%20Premier%20League/"

# openfootball club name -> (display name, Chinese, luukhopman crest filename)
CLUBS: dict[str, tuple[str, str, str]] = {
    "AFC Bournemouth": ("Bournemouth", "伯恩茅斯", "AFC Bournemouth.png"),
    "Arsenal FC": ("Arsenal", "阿森纳", "Arsenal FC.png"),
    "Aston Villa FC": ("Aston Villa", "阿斯顿维拉", "Aston Villa.png"),
    "Brentford FC": ("Brentford", "布伦特福德", "Brentford FC.png"),
    "Brighton & Hove Albion FC": ("Brighton", "布莱顿", "Brighton & Hove Albion.png"),
    "Chelsea FC": ("Chelsea", "切尔西", "Chelsea FC.png"),
    "Coventry City FC": ("Coventry", "考文垂", "Coventry City.png"),
    "Crystal Palace FC": ("Crystal Palace", "水晶宫", "Crystal Palace.png"),
    "Everton FC": ("Everton", "埃弗顿", "Everton FC.png"),
    "Fulham FC": ("Fulham", "富勒姆", "Fulham FC.png"),
    "Hull City AFC": ("Hull City", "赫尔城", "Hull City.png"),
    "Ipswich Town FC": ("Ipswich", "伊普斯维奇", "Ipswich Town.png"),
    "Leeds United FC": ("Leeds", "利兹联", "Leeds United.png"),
    "Liverpool FC": ("Liverpool", "利物浦", "Liverpool FC.png"),
    "Manchester City FC": ("Man City", "曼城", "Manchester City.png"),
    "Manchester United FC": ("Man Utd", "曼联", "Manchester United.png"),
    "Newcastle United FC": ("Newcastle", "纽卡斯尔", "Newcastle United.png"),
    "Nottingham Forest FC": ("Nott'm Forest", "诺丁汉森林", "Nottingham Forest.png"),
    "Sunderland AFC": ("Sunderland", "桑德兰", "Sunderland AFC.png"),
    "Tottenham Hotspur FC": ("Tottenham", "托特纳姆热刺", "Tottenham Hotspur.png"),
}

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}

LONDON = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")

MATCHDAY_RE = re.compile(r"Matchday\s+(\d+)")
DATE_RE = re.compile(r"^\s+[A-Z][a-z]{2}\s+([A-Z][a-z]{2})\s+(\d{1,2})(?:\s+(\d{4}))?\s*$")
MATCH_RE = re.compile(r"^\s+(?:(\d{1,2}:\d{2})\s+)?(.+?)\s+v\s+(.+?)\s*$")
SCORE_RE = re.compile(r"\s{2,}\d+-\d+.*$")


def logo_url(filename: str) -> str:
    return LOGO_BASE + urllib.parse.quote(filename)


def lookup(name: str) -> tuple[str, str, str]:
    club = CLUBS.get(name.strip())
    if club is None:
        raise KeyError(f"Unknown club (add to CLUBS): {name!r}")
    return club


def parse(text: str, start_year: int) -> list[dict]:
    fixtures: list[dict] = []
    gameweek = 0
    year = start_year
    prev_month = 0
    cur_date: datetime | None = None
    cur_time = "15:00"  # openfootball default before a time is stated

    for raw in text.splitlines():
        md = MATCHDAY_RE.search(raw)
        if md and raw.lstrip().startswith(("▪", "Matchday")):
            gameweek = int(md.group(1))
            continue

        date_match = DATE_RE.match(raw)
        if date_match:
            month_name, day, explicit_year = date_match.groups()
            month = MONTHS[month_name]
            if explicit_year:
                year = int(explicit_year)
            elif prev_month and month < prev_month:
                year += 1  # season rolls Dec -> Jan
            prev_month = month
            cur_date = datetime(year, month, int(day))
            continue

        cleaned = SCORE_RE.sub("", raw)
        m = MATCH_RE.match(cleaned)
        if not m or " v " not in cleaned or cur_date is None or gameweek == 0:
            continue
        time_str, home_raw, away_raw = m.groups()
        if time_str:
            cur_time = time_str
        hour, minute = (int(x) for x in cur_time.split(":"))
        kickoff = datetime(cur_date.year, cur_date.month, cur_date.day, hour, minute, tzinfo=LONDON)

        home_display, home_zh, home_file = lookup(home_raw)
        away_display, away_zh, away_file = lookup(away_raw)
        fixtures.append({
            "gameweek": gameweek,
            "kickoff": kickoff.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "home": home_display,
            "away": away_display,
            "home_logo": logo_url(home_file),
            "away_logo": logo_url(away_file),
        })
    return fixtures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="openfootball season .txt")
    parser.add_argument("-o", "--output", type=Path, default=Path("schedule.json"))
    parser.add_argument("--season", default="2026/27")
    parser.add_argument("--competition", default="English Premier League")
    parser.add_argument("--competition-zh", default="英格兰超级联赛")
    parser.add_argument("--start-year", type=int, default=2026, help="Calendar year of the first matchday")
    args = parser.parse_args()

    fixtures = parse(args.input.read_text(), args.start_year)
    teams_zh = {display: zh for display, zh, _ in CLUBS.values()}
    payload = {
        "competition": args.competition,
        "competition_zh": args.competition_zh,
        "season": args.season,
        "translations": {"teams": teams_zh, "venues": {}},
        "fixtures": fixtures,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    weeks = len({f["gameweek"] for f in fixtures})
    print(f"Wrote {len(fixtures)} fixtures across {weeks} matchweeks to {args.output}")


if __name__ == "__main__":
    main()
