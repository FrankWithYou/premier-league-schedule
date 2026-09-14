#!/usr/bin/env python3
"""Generate a print-friendly bilingual (English/中文) football schedule from fixture JSON."""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

WEEKDAY_ZH = {"Mon": "周一", "Tue": "周二", "Wed": "周三", "Thu": "周四", "Fri": "周五", "Sat": "周六", "Sun": "周日"}


def parse_kickoff(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and require an explicit timezone."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Kickoff must include a timezone: {value}")
    return parsed


def central_kickoff(value: str, timezone: str = "America/Chicago") -> tuple[str, str]:
    local = parse_kickoff(value).astimezone(ZoneInfo(timezone))
    return local.strftime("%-I:%M %p"), local.tzname() or "CT"


def bilingual(english: str, chinese: str) -> str:
    """English label followed by a muted Chinese gloss when a translation exists."""
    en = html.escape(english)
    if not chinese:
        return en
    return f'{en}<em class="zh">{html.escape(chinese)}</em>'


def team_html(name: str, chinese: str, logo: str) -> str:
    """One club on a single horizontal line: crest, English name, Chinese name."""
    zh = f'<em class="zh">{html.escape(chinese)}</em>' if chinese else ""
    src = html.escape(logo, quote=True)
    return f'<span class="team"><img src="{src}" alt=""><b class="en">{html.escape(name)}</b>{zh}</span>'


def render(payload: dict, timezone: str, theme: str = "editorial", per_page: int = 10) -> str:
    fixtures = payload["fixtures"]
    season = payload["season"]
    competition = payload.get("competition", "English Premier League")
    competition_zh = payload.get("competition_zh", "")
    translations = payload.get("translations", {})
    teams_zh = translations.get("teams", {})
    venues_zh = translations.get("venues", {})

    weeks: dict[int, list[dict]] = defaultdict(list)
    for fixture in fixtures:
        weeks[int(fixture["gameweek"])].append(fixture)

    pages = []
    for gameweek in sorted(weeks):
        matches = sorted(weeks[gameweek], key=lambda item: item["kickoff"])
        kickoff_dates = [parse_kickoff(item["kickoff"]).astimezone(ZoneInfo(timezone)) for item in matches]
        date_range = f"{min(kickoff_dates):%b %-d} – {max(kickoff_dates):%b %-d, %Y}"
        rows = []
        for match in matches:
            time, abbreviation = central_kickoff(match["kickoff"], timezone)
            local = parse_kickoff(match["kickoff"]).astimezone(ZoneInfo(timezone))
            weekday = local.strftime("%a")
            home_logo = html.escape(match.get("home_logo", ""), quote=True)
            away_logo = html.escape(match.get("away_logo", ""), quote=True)
            home = match["home"]
            away = match["away"]
            venue = match.get("venue", "")
            venue_html = f' · {bilingual(venue, venues_zh.get(venue, ""))}' if venue else ""
            month_abbr = local.strftime("%b")
            rows.append(
                f'''<article class="match" data-week="{gameweek}" data-teams="{html.escape((home + " " + away + " " + teams_zh.get(home, "") + " " + teams_zh.get(away, "")).lower())}">
  <div class="match-date"><span class="mon">{html.escape(month_abbr)}</span><strong>{html.escape(local.strftime("%-d"))}</strong><span class="dow">{html.escape(weekday)}<em class="zh">{WEEKDAY_ZH.get(weekday, "")}</em></span></div>
  <div class="teams">{team_html(home, teams_zh.get(home, ""), match.get("home_logo", ""))}{team_html(away, teams_zh.get(away, ""), match.get("away_logo", ""))}</div>
  <div class="kickoff"><strong>{time}</strong><small>{abbreviation}{venue_html}</small></div>
  <label class="score"><span class="score-cap">比分</span><input inputmode="numeric" maxlength="2" aria-label="{html.escape(home)} score"><b>–</b><input inputmode="numeric" maxlength="2" aria-label="{html.escape(away)} score"></label>
</article>'''
            )
        chunks = [rows[i:i + per_page] for i in range(0, len(rows), per_page)] or [[]]
        total = len(chunks)
        for index, chunk in enumerate(chunks, start=1):
            page_of = f'<span class="page-of">Page {index} / {total} · 第 {index}/{total} 页</span>' if total > 1 else ""
            cont = '<span class="cont"> · cont. 续</span>' if index > 1 else ""
            pages.append(
                f'''<section class="week-page" data-week-page="{gameweek}">
  <header class="week-header"><div><p class="eyebrow">{bilingual(competition, competition_zh)} · {html.escape(season)}</p><h2>Gameweek {gameweek:02d}<em class="zh">第 {gameweek:02d} 轮{cont}</em></h2><p class="date-range">{date_range}{page_of}</p></div><div class="week-mark">{gameweek:02d}</div></header>
  <div class="matches">{"".join(chunk)}</div>
  <footer><span>Kickoffs in Central Time · 开球时间为美国中部时间</span><span>Season guide · 赛季指南</span></footer>
</section>'''
            )

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(competition)} {html.escape(season)}</title>
<style>
@page {{ size: letter; margin: 0; }}
:root {{ --ink:#14251e; --muted:#718078; --line:#dbe3de; --lime:#d9f16b; --paper:#ffffff; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:#ffffff; color:var(--ink); font-family:Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", ui-sans-serif, system-ui, sans-serif; }}
.theme-dark {{ --ink:#f5f7f0; --muted:#a5b5ab; --line:#34463d; --lime:#d9f16b; --paper:#11231c; background:#07110d; }}
.theme-compact .week-page {{ padding:42px 48px 32px; }} .theme-compact h2 {{ font-size:56px; }} .theme-compact .teams {{ font-size:26px; }} .theme-compact .teams .zh {{ font-size:24px; }}
.zh {{ display:inline-block; margin-left:.4em; font-style:normal; font-weight:700; font-size:1.12em; color:var(--muted); white-space:nowrap; }}
.week-page {{ width:8.5in; min-height:11in; margin:24px auto; padding:52px 58px 40px; background:var(--paper); display:flex; flex-direction:column; }}
.page-of {{ display:inline-block; margin-left:14px; font-size:15px; font-weight:800; color:var(--muted); }} .cont {{ font-size:.6em; color:var(--muted); }}
.week-header {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid var(--ink); padding-bottom:28px; }}
.eyebrow {{ margin:0 0 14px; color:#53705e; font-size:15px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }} .eyebrow .zh {{ letter-spacing:0; text-transform:none; }} h2 {{ margin:0; font-size:68px; line-height:.95; letter-spacing:-.06em; }} h2 .zh {{ display:block; margin:10px 0 0; font-size:32px; letter-spacing:0; }} .date-range {{ margin:16px 0 0; color:var(--muted); font-size:19px; font-weight:650; }}
.week-mark {{ display:grid; place-items:center; width:78px; height:78px; border-radius:50%; background:var(--lime); font-size:26px; font-weight:900; }}
.matches {{ flex:1; display:flex; flex-direction:column; justify-content:space-between; padding-top:4px; }} .match {{ display:grid; grid-template-columns:50px minmax(0,1fr) auto auto; align-items:center; gap:0 18px; border-bottom:1.5px solid var(--line); padding:4px 0; break-inside:avoid; page-break-inside:avoid; }}
.match-date {{ text-align:center; color:var(--muted); line-height:1; }} .match-date .mon {{ display:block; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.04em; }} .match-date strong {{ display:block; color:var(--ink); font-size:30px; letter-spacing:-.05em; }} .match-date .dow {{ display:block; margin-top:2px; font-size:12px; font-weight:800; }} .match-date .zh {{ margin-left:.2em; font-size:12px; }}
.teams {{ display:flex; flex-direction:column; gap:6px; min-width:0; }} .team {{ display:flex; align-items:center; gap:11px; white-space:nowrap; font-size:24px; font-weight:800; letter-spacing:-.02em; }} .team .en {{ font-weight:800; }} .team .zh {{ font-size:21px; }} .team img {{ width:29px; height:29px; object-fit:contain; flex:0 0 29px; }}
.kickoff {{ text-align:right; white-space:nowrap; }} .kickoff strong {{ display:block; font-size:20px; }} .kickoff small {{ display:block; margin-top:2px; color:var(--muted); font-size:12px; }} .score {{ display:flex; align-items:center; gap:6px; }} .score-cap {{ color:var(--muted); font-size:13px; font-weight:800; }} .score b {{ font-size:18px; color:var(--muted); }} .score input {{ width:34px; height:32px; border:2px solid var(--muted); border-radius:6px; background:transparent; color:var(--ink); text-align:center; font-size:20px; font-weight:800; }}
footer {{ display:flex; justify-content:space-between; padding-top:24px; color:var(--muted); font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }}
.controls {{ width:8.5in; margin:24px auto -8px; display:flex; flex-wrap:wrap; align-items:center; gap:10px; }} .controls button, .controls input {{ border:1px solid #bdc9c1; border-radius:999px; background:white; color:#14251e; padding:11px 17px; font:inherit; font-size:15px; }} .controls button {{ cursor:pointer; font-weight:800; }} .controls button.active {{ background:var(--ink); color:var(--paper); }} .controls input {{ min-width:200px; }}
@media print {{ body {{ background:white; }} .controls {{ display:none; }} .week-page {{ margin:0; height:auto; min-height:0; break-before:page; padding:22px 50px 16px; }} .week-page:first-of-type {{ break-before:auto; }} .week-header {{ padding-bottom:10px; }} .eyebrow {{ margin-bottom:4px; font-size:12px; }} h2 {{ font-size:34px; }} h2 .zh {{ font-size:20px; margin-top:2px; }} .date-range {{ margin-top:4px; font-size:14px; }} .week-mark {{ width:52px; height:52px; font-size:20px; }} footer {{ padding-top:8px; font-size:11px; }} .match {{ break-inside:avoid; page-break-inside:avoid; }} .score input {{ border-color:#111; }} }}
</style></head><body class="theme-{html.escape(theme)}"><nav class="controls" aria-label="Schedule controls"><button class="active" data-show="all">All weeks 全部</button>{"".join(f'<button data-show="{week}">GW {week:02d}</button>' for week in sorted(weeks))}<input id="team-search" type="search" placeholder="Filter by club… 按球队筛选" aria-label="Filter by club"></nav>{"".join(pages)}<script>
const pages=[...document.querySelectorAll('[data-week-page]')], search=document.querySelector('#team-search');
function filter() {{ const week=document.querySelector('button.active').dataset.show, term=search.value.toLowerCase(); pages.forEach(page => {{ let count=0; page.querySelectorAll('.match').forEach(match => {{ const show=(week==='all'||match.dataset.week===week)&&match.dataset.teams.includes(term); match.hidden=!show; count+=show?1:0; }}); page.hidden=count===0; }}); }}
document.querySelectorAll('[data-show]').forEach(button => button.addEventListener('click', () => {{ document.querySelector('.active').classList.remove('active'); button.classList.add('active'); filter(); }})); search.addEventListener('input', filter);
</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Fixture JSON file")
    parser.add_argument("-o", "--output", type=Path, default=Path("schedule.html"))
    parser.add_argument("--timezone", default="America/Chicago", help="IANA timezone (default: America/Chicago)")
    parser.add_argument("--theme", choices=("editorial", "dark", "compact"), default="editorial")
    parser.add_argument("--per-page", type=int, default=10, help="Matches per printed page (default: 10 -> one matchweek per page)")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    output = render(payload, args.timezone, args.theme, args.per_page)
    args.output.write_text(output)
    weeks = len({item["gameweek"] for item in payload["fixtures"]})
    print(f"Wrote {weeks} matchweeks (~{args.per_page}/page) to {args.output}")


if __name__ == "__main__":
    main()
