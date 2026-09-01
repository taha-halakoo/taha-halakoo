#!/usr/bin/env python3
"""Generate the README data panels from live GitHub data.

Writes a wide and a narrow variant of each of stats, contrib, velocity and
rhythm. The narrow ones exist because an SVG rendered as <img> scales as a
picture and its text does not reflow: at 1000px wide this type landed at 2.5px
in a phone's 293px README column.

Requires STATS_TOKEN (a classic PAT with `repo` scope). The default
GITHUB_TOKEN cannot enumerate private repositories and would report
public-only figures.
"""
import collections
import datetime
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (S, head, tail, sect, fade, card, t, pulse, sweep,  # noqa: E402
                      hsweep, burst, GRID, DIM, TEXT, AMBER, GREEN, MUTE, MONO)

USER = os.environ.get("GH_USER", "taha-halakoo")
TOKEN = os.environ["GITHUB_TOKEN"]
HEAT = ["#131318", "#4A3A0E", "#8A6A0A", "#C99A12", "#FFC93C"]

QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER) {
      totalCount
      nodes {
        isPrivate
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
""" % USER


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": "bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit("GraphQL errors: %s" % payload["errors"])
    return payload["data"]["user"]


def tile(s, x, y, w, h, val, label, colour, delay):
    return (f'<g opacity="0">{fade(delay, 0.5)}{card(s, x, y, w, h, GRID, 0.16)}'
            f'{t(x+14, y+h-28, val, s.num, colour, weight=700)}'
            f'{t(x+14, y+h-9, label, s.det, DIM, ls=1.3)}</g>')


def langbar(s, p, top, col, tot, y):
    x = float(s.pad)
    for name, size in top:
        w = size / tot * s.inner
        p.append(f'<rect x="{x:.1f}" y="{y}" width="0" height="14" fill="{col[name]}">'
                 f'<animate attributeName="width" from="0" to="{w:.1f}" dur="0.9s" '
                 f'begin="0.5s" fill="freeze"/></rect>')
        x += w


# ------------------------------------------------------------------------ stats

def build_stats(s, d):
    c = d["contributionsCollection"]
    total = c["totalCommitContributions"] + c["restrictedContributionsCount"]
    pct = round(c["restrictedContributionsCount"] * 100 / total) if total else 0
    repos = d["repositories"]["totalCount"]
    stars = sum(n["stargazerCount"] for n in d["repositories"]["nodes"])

    lang, col = collections.Counter(), {}
    for n in d["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            lang[e["node"]["name"]] += e["size"]
            col[e["node"]["name"]] = e["node"]["color"] or "#8B949E"
    tot = sum(lang.values()) or 1
    top = lang.most_common(4 if s.n else 6)

    vals = [(f"{total:,}", "COMMITS 12MO" if s.n else "COMMITS / 12 MO", AMBER),
            (f"{pct}%", "PRIVATE" if s.n else "SHIPPED PRIVATELY", GREEN),
            (f"{repos}", "REPOS" if s.n else "REPOSITORIES", TEXT),
            (f"{stars}", "STARS" if s.n else "STARS EARNED", TEXT)]

    if s.n:
        tw, th = (s.inner - 10) / 2, 72
        gy = 42 + 2 * (th + 10) + 30
        h = gy + 36 + ((len(top) + 1) // 2) * 22 + 8
        p = head(s, h, "GitHub activity for %s" % USER, "st")
        p.append(sect(s, 26, "SIGNAL · 12 MONTHS"))
        for i, (v, l, c2) in enumerate(vals):
            p.append(tile(s, s.pad + (i % 2) * (tw + 10), 42 + (i // 2) * (th + 10),
                          tw, th, v, l, c2, 0.1 * i))
        p.append(t(s.pad, gy - 10, "LANGUAGE DISTRIBUTION", s.det, DIM, ls=1.6))
        langbar(s, p, top, col, tot, gy)
        for i, (name, size) in enumerate(top):
            lx = s.pad + (i % 2) * (s.inner / 2)
            ly = gy + 36 + (i // 2) * 22
            p.append(f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="{col[name]}"/>')
            p.append(t(lx + 14, ly, f"{name} {size*100/tot:.0f}%", s.det, MUTE))
        return "\n".join(p + tail(s, h)), h

    tw, th = (s.inner - 3 * 12) / 4, 80
    gy = 44 + th + 36
    h = gy + 58
    p = head(s, h, "GitHub activity for %s" % USER, "st")
    p.append(sect(s, 28, "SIGNAL · LAST 12 MONTHS"))
    for i, (v, l, c2) in enumerate(vals):
        p.append(tile(s, s.pad + i * (tw + 12), 44, tw, th, v, l, c2, 0.12 * i))
    p.append(t(s.pad, gy - 10, "LANGUAGE DISTRIBUTION", s.det, DIM, ls=1.6))
    langbar(s, p, top, col, tot, gy)
    lx = s.pad
    for name, size in top:
        label = f"{name} {size*100/tot:.1f}%"
        p.append(f'<circle cx="{lx+4}" cy="{gy+36}" r="4.2" fill="{col[name]}"/>')
        p.append(t(lx + 14, gy + 40, label, s.det, MUTE))
        lx += 28 + len(label) * s.det * 0.605
    return "\n".join(p + tail(s, h)), h


# ---------------------------------------------------------------------- contrib

def build_contrib(s, d):
    cal = d["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    peak = max((x["contributionCount"] for w in weeks for x in w["contributionDays"]), default=0) or 1
    nz = sorted(x["contributionCount"] for w in weeks for x in w["contributionDays"]
                if x["contributionCount"] > 0)

    def q(f):
        return nz[int(len(nz) * f)] if nz else 1
    t1, t2, t3 = q(0.25), q(0.55), q(0.85)

    def lv(n):
        return 0 if n == 0 else (1 if n <= t1 else (2 if n <= t2 else (3 if n <= t3 else 4)))

    x0 = s.pad + (0 if s.n else 36)
    step = (s.W - s.pad - x0) / len(weeks)
    gap = 1 if s.n else 3
    cell = max(2.5, step - gap)
    y0 = 60 if s.n else 70
    grid_h = 7 * (cell + gap)
    h = round(y0 + grid_h + (60 if s.n else 44))

    p = head(s, h, "Contribution heatmap for %s" % USER, "ct")
    p.append(sect(s, 26 if s.n else 28,
                  f"HEATMAP · {cal['totalContributions']:,} IN 12 MONTHS" if s.n
                  else f"CONTRIBUTION HEATMAP · {cal['totalContributions']:,} IN 12 MONTHS"))
    seen, shown, every = set(), 0, (3 if s.n else 1)
    for wi, w in enumerate(weeks):
        first = w["contributionDays"][0]["date"]
        if first[:7] not in seen and int(first[8:]) <= 7:
            seen.add(first[:7])
            if shown % every == 0:
                lab = datetime.date(int(first[:4]), int(first[5:7]), 1).strftime("%b")
                p.append(t(x0 + wi * step, y0 - 9, lab, s.det, DIM))
            shown += 1
    if not s.n:
        for i, dl in enumerate(["Mon", "Wed", "Fri"]):
            p.append(t(x0 - 9, y0 + (i * 2 + 1) * (cell + gap) + 10, dl, s.det, DIM, anchor="end"))
    for wi, w in enumerate(weeks):
        x = x0 + wi * step
        p.append(f'<g opacity="0">{fade(wi * 0.024, 0.35)}')
        for day in w["contributionDays"]:
            y = y0 + day["weekday"] * (cell + gap)
            p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                     f'rx="{min(2.5, cell/3):.1f}" fill="{HEAT[lv(day["contributionCount"])]}"/>')
        p.append('</g>')

    fy = y0 + grid_h + 26
    p.append(t(s.pad, fy, f"peak day · {peak} contributions", s.det, DIM))
    if s.n:
        ly, lx = fy + 26, s.pad
    else:
        ly, lx = fy, s.W - s.pad - 5 * 18 - 84
    p.append(t(lx, ly, "less", s.det, DIM))
    bx = lx + 38
    for i, c in enumerate(HEAT):
        p.append(f'<rect x="{bx + i*18}" y="{ly-11}" width="14" height="14" rx="2.5" fill="{c}"/>')
    p.append(t(bx + 5 * 18 + 6, ly, "more", s.det, DIM))
    return "\n".join(p + tail(s, h)), h


# --------------------------------------------------------------------- velocity

def build_velocity(s, d):
    cal = d["contributionsCollection"]["contributionCalendar"]
    by = collections.OrderedDict()
    for w in cal["weeks"]:
        for day in w["contributionDays"]:
            k = day["date"][:7]
            by[k] = by.get(k, 0) + day["contributionCount"]
    months = list(by.items())[-13:]
    peak = max(v for _, v in months) or 1
    this_month = datetime.date.today().strftime("%Y-%m")

    top = 64 if s.n else 74
    base = top + (150 if s.n else 152)
    h = base + 56
    p = head(s, h, "Monthly contribution volume for %s" % USER, "vl")
    p.append(sect(s, 26 if s.n else 28,
                  "VELOCITY · PER MONTH" if s.n else "VELOCITY · CONTRIBUTIONS PER MONTH"))

    gx = s.pad + (34 if s.n else 46)
    gw = s.W - s.pad - gx
    for frac in (0.5, 1.0):
        y = base - frac * (base - top)
        p.append(f'<line x1="{gx}" y1="{y:.1f}" x2="{s.W-s.pad}" y2="{y:.1f}" stroke="{GRID}" stroke-opacity="0.08"/>')
        p.append(t(gx - 7, y + 4, str(int(peak * frac)), s.det, DIM, anchor="end"))

    slot = gw / len(months)
    bw = min(40, slot - (3 if s.n else 8))
    last_label = [-1e9]
    for i, (mon, val) in enumerate(months):
        x = gx + i * slot + (slot - bw) / 2
        bh = (val / peak) * (base - top)
        partial, is_peak = mon == this_month, val == peak
        extra = ' fill-opacity="0.35" stroke="#8A6A0A" stroke-dasharray="3 3"' if partial else ''
        p.append(f'<rect x="{x:.1f}" y="{base}" width="{bw:.1f}" height="0" rx="3" '
                 f'fill="{AMBER if is_peak else "#8A6A0A"}"{extra}>'
                 f'<animate attributeName="height" from="0" to="{bh:.1f}" dur="0.7s" '
                 f'begin="{0.2+i*0.05:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" to="{base-bh:.1f}" dur="0.7s" '
                 f'begin="{0.2+i*0.05:.2f}s" fill="freeze"/>'
                 f'{pulse(0.62, 1, 2.8, 1.4) if is_peak else ""}</rect>')
        if is_peak:
            p.append(f'<g opacity="0">{fade(1.4, 0.4)}'
                     f'{burst(x + bw / 2, base - bh, 22, 3.0, 1.6, AMBER)}</g>')
        lab = datetime.date(int(mon[:4]), int(mon[5:7]), 1).strftime("%b")
        lw = len(lab) * s.det * 0.605
        want = (not s.n) or i % 3 == 0 or is_peak
        if want and (x + bw / 2 - lw / 2) > last_label[0] + 4:
            p.append(t(x + bw / 2, base + 19, lab, s.det, DIM, anchor="middle"))
            last_label[0] = x + bw / 2 + lw / 2
        if is_peak or (not s.n and val):
            p.append(f'<text x="{x+bw/2:.1f}" y="{base-bh-8:.1f}" font-family="{MONO}" '
                     f'font-size="{s.det}" fill="{AMBER if is_peak else DIM}" text-anchor="middle" '
                     f'opacity="0">{fade(0.9+i*0.05, 0.4)}{val}</text>')
        if partial:
            p.append(t(x + bw / 2, base + 34, "MTD", s.det, "#8A6A0A", anchor="middle"))
    p.append(f'<line x1="{gx}" y1="{base}" x2="{s.W-s.pad}" y2="{base}" stroke="{GRID}" stroke-opacity="0.2"/>')
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- rhythm

def build_rhythm(s, d):
    cal = d["contributionsCollection"]["contributionCalendar"]
    today = datetime.date.today().isoformat()
    days = [x for w in cal["weeks"] for x in w["contributionDays"] if x["date"] <= today]
    active = [x for x in days if x["contributionCount"] > 0]
    best = max(days, key=lambda x: x["contributionCount"]) if days else None
    longest = run = 0
    for x in days:
        run = run + 1 if x["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for x in reversed(days):
        if x["contributionCount"] == 0:
            break
        current += 1
    wd = collections.Counter()
    for x in days:
        wd[x["weekday"]] += x["contributionCount"]
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    wpeak = max(wd.values()) if wd else 1
    avg = sum(x["contributionCount"] for x in active) / len(active) if active else 0
    pct = round(len(active) * 100 / len(days)) if days else 0
    heaviest = max(wd, key=lambda k: wd[k]) if wd else 0

    vals = [(f"{longest}", "LONGEST STREAK" if s.n else "LONGEST STREAK / DAYS", AMBER),
            (f"{best['contributionCount']}" if best else "0",
             "BUSIEST DAY" if s.n else "BUSIEST SINGLE DAY", AMBER),
            (f"{avg:.1f}", "AVG / DAY" if s.n else "AVG ON AN ACTIVE DAY", GREEN),
            (f"{pct}%", "DAYS ACTIVE" if s.n else "OF DAYS WITH COMMITS", TEXT)]

    if s.n:
        tw, th = (s.inner - 10) / 2, 72
        gy = 42 + 2 * (th + 10) + 34
        base = gy + 116
    else:
        tw, th = (s.inner - 3 * 12) / 4, 80
        gy = 44 + th + 42
        base = gy + 100
    h = base + 52
    p = head(s, h, "Working rhythm for %s" % USER, "rh")
    p.append(sect(s, 26 if s.n else 28, "WORKING RHYTHM"))
    for i, (v, l, c2) in enumerate(vals):
        if s.n:
            p.append(tile(s, s.pad + (i % 2) * (tw + 10), 42 + (i // 2) * (th + 10), tw, th, v, l, c2, 0.1 * i))
        else:
            p.append(tile(s, s.pad + i * (tw + 12), 44, tw, th, v, l, c2, 0.12 * i))
    p.append(t(s.pad, gy - 14, "WHICH DAYS THE WORK LANDS ON", s.det, DIM, ls=1.6))
    slot = s.inner / 7
    bw = min(46, slot - 8)
    for i in range(7):
        x = s.pad + i * slot + (slot - bw) / 2
        bh = (wd[i] / wpeak) * (base - gy - 6) if wpeak else 0
        p.append(f'<rect x="{x:.1f}" y="{base}" width="{bw:.1f}" height="0" rx="3" '
                 f'fill="{AMBER if i==heaviest else "#8A6A0A"}">'
                 f'<animate attributeName="height" from="0" to="{bh:.1f}" dur="0.7s" '
                 f'begin="{0.5+i*0.07:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" to="{base-bh:.1f}" dur="0.7s" '
                 f'begin="{0.5+i*0.07:.2f}s" fill="freeze"/>'
                 f'{pulse(0.62, 1, 2.8, 1.6) if i == heaviest else ""}</rect>')
        p.append(t(x + bw / 2, base + 19, names[i], s.det, DIM, anchor="middle"))
        p.append(f'<text x="{x+bw/2:.1f}" y="{base-bh-7:.1f}" font-family="{MONO}" '
                 f'font-size="{s.det}" fill="{AMBER if i==heaviest else DIM}" text-anchor="middle" '
                 f'opacity="0">{fade(1.2+i*0.07, 0.4)}{wd[i]}</text>')
    p.append(f'<line x1="{s.pad}" y1="{base}" x2="{s.W-s.pad}" y2="{base}" stroke="{GRID}" stroke-opacity="0.2"/>')
    p.append(t(s.pad, base + 42, f"current streak · {current} days", s.det, DIM))
    return "\n".join(p + tail(s, h)), h


BUILDERS = {"stats": build_stats, "contrib": build_contrib,
            "velocity": build_velocity, "rhythm": build_rhythm}

if __name__ == "__main__":
    data = fetch()
    c = data["contributionsCollection"]
    if c["restrictedContributionsCount"] == 0 and any(
            n.get("isPrivate") for n in data["repositories"]["nodes"]):
        raise SystemExit(
            "refusing to publish: restrictedContributionsCount is 0 but private repositories "
            "exist, so this token cannot see private contributions.\n"
            "Add a classic PAT with `repo` scope as the STATS_TOKEN repository secret.")
    os.makedirs("assets", exist_ok=True)
    for name, fn in BUILDERS.items():
        for suffix, narrow in (("", False), ("-narrow", True)):
            svg, h = fn(S(narrow), data)
            path = f"assets/{name}{suffix}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"{path:32} {S(narrow).W}x{h}")
