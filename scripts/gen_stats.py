#!/usr/bin/env python3
"""Generate the README data panels from live GitHub data.

Writes assets/stats.svg, assets/contrib.svg and assets/velocity.svg.

Self-hosted replacement for the usual third-party README widgets, which
rate-limit, run out of quota, and eventually 402. Run by
.github/workflows/stats.yml, which requires a STATS_TOKEN secret: the default
GITHUB_TOKEN cannot enumerate private repositories and would silently report
public-only figures.
"""
import collections
import datetime
import json
import os
import urllib.request

USER = os.environ.get("GH_USER", "taha-halakoo")
TOKEN = os.environ["GITHUB_TOKEN"]

BG, GRID, DIM, TEXT, AMBER, GREEN = (
    "#07070A", "#FFC93C", "#5F6672", "#E4E6EB", "#FFC93C", "#3FB950")
HEAT = ["#131318", "#4A3A0E", "#8A6A0A", "#C99A12", "#FFC93C"]
MONO = "ui-monospace,Menlo,monospace"

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
        headers={"Authorization": "bearer " + TOKEN,
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit("GraphQL errors: %s" % payload["errors"])
    return payload["data"]["user"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def frame(w, h, label, uid):
    """Card background, grid and section label shared by every panel."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-label="{esc(label)}">',
        f'<defs><pattern id="g{uid}" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<path d="M26 0H0V26" fill="none" stroke="{GRID}" stroke-opacity="0.045"/></pattern>'
        f'<clipPath id="c{uid}"><rect width="{w}" height="{h}" rx="14"/></clipPath></defs>',
        f'<g clip-path="url(#c{uid})"><rect width="{w}" height="{h}" fill="{BG}"/>',
        f'<rect width="{w}" height="{h}" fill="url(#g{uid})"/>',
    ]


def close(w, h):
    return [f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="none" '
            f'stroke="{GRID}" stroke-opacity="0.14"/></g></svg>']


# --------------------------------------------------------------------------- stats

def build_stats(d):
    c = d["contributionsCollection"]
    pub, priv = c["totalCommitContributions"], c["restrictedContributionsCount"]
    total = pub + priv
    pct = round(priv * 100 / total) if total else 0
    repos = d["repositories"]["totalCount"]
    stars = sum(n["stargazerCount"] for n in d["repositories"]["nodes"])

    lang, col = collections.Counter(), {}
    for n in d["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            lang[e["node"]["name"]] += e["size"]
            col[e["node"]["name"]] = e["node"]["color"] or "#8B949E"
    tot = sum(lang.values()) or 1
    top = lang.most_common(6)

    p = frame(1000, 250, "GitHub activity for %s" % USER, "s")
    p.append(f'<text x="34" y="34" font-family="{MONO}" font-size="12" fill="{AMBER}" '
             f'letter-spacing="2.6">SIGNAL &#183; LAST 12 MONTHS</text>')

    for i, (val, label, colr) in enumerate([
            (f"{total:,}", "COMMITS / 12 MO", AMBER),
            (f"{pct}%", "SHIPPED PRIVATELY", GREEN),
            (f"{repos}", "REPOSITORIES", TEXT),
            (f"{stars}", "STARS EARNED", TEXT)]):
        x = 34 + i * 238
        p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                 f'begin="{i*0.14:.2f}s" dur="0.5s" fill="freeze"/>'
                 f'<rect x="{x}" y="54" width="222" height="86" rx="8" fill="#0E1116" '
                 f'stroke="{GRID}" stroke-opacity="0.16"/>'
                 f'<text x="{x+18}" y="106" font-family="{MONO}" font-size="34" '
                 f'font-weight="700" fill="{colr}">{val}</text>'
                 f'<text x="{x+18}" y="127" font-family="{MONO}" font-size="10.5" '
                 f'fill="{DIM}" letter-spacing="1.7">{label}</text></g>')

    p.append(f'<text x="34" y="176" font-family="{MONO}" font-size="11" fill="{DIM}" '
             f'letter-spacing="2.2">LANGUAGE DISTRIBUTION</text>')
    x = 34.0
    for name, size in top:
        w = size / tot * 932
        p.append(f'<rect x="{x:.1f}" y="188" width="0" height="14" fill="{col[name]}">'
                 f'<animate attributeName="width" from="0" to="{w:.1f}" dur="0.9s" '
                 f'begin="0.5s" fill="freeze"/></rect>')
        x += w + 2
    lx = 34
    for name, size in top:
        p.append(f'<circle cx="{lx+4}" cy="224" r="4" fill="{col[name]}"/>'
                 f'<text x="{lx+15}" y="228" font-family="{MONO}" font-size="11" '
                 f'fill="#8B929E">{esc(name)} {size*100/tot:.1f}%</text>')
        lx += 22 + len(name) * 6.6 + 42
    return "\n".join(p + close(1000, 250))


# ------------------------------------------------------------------------ contrib

def build_contrib(d):
    cal = d["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    peak = max((day["contributionCount"]
                for w in weeks for day in w["contributionDays"]), default=0) or 1
    # thresholds on the non-zero distribution so one huge day cannot flatten the scale
    nz = sorted(day["contributionCount"] for w in weeks
                for day in w["contributionDays"] if day["contributionCount"] > 0)
    def q(f):
        return nz[int(len(nz) * f)] if nz else 1
    t1, t2, t3 = q(0.25), q(0.55), q(0.85)

    def level(n):
        if n == 0:
            return 0
        if n <= t1:
            return 1
        if n <= t2:
            return 2
        if n <= t3:
            return 3
        return 4

    cell, gap, x0, y0 = 13, 3, 46, 68
    p = frame(1000, 232, "Contribution heatmap for %s" % USER, "h")
    p.append(f'<text x="34" y="34" font-family="{MONO}" font-size="12" fill="{AMBER}" '
             f'letter-spacing="2.6">CONTRIBUTION HEATMAP &#183; '
             f'{cal["totalContributions"]:,} IN 12 MONTHS</text>')

    # month ruler
    seen = set()
    for wi, w in enumerate(weeks):
        first = w["contributionDays"][0]["date"]
        mon = first[:7]
        if mon not in seen and int(first[8:]) <= 7:
            seen.add(mon)
            label = datetime.date(int(first[:4]), int(first[5:7]), 1).strftime("%b")
            p.append(f'<text x="{x0 + wi*(cell+gap)}" y="58" font-family="{MONO}" '
                     f'font-size="9.5" fill="{DIM}">{label}</text>')

    for i, dl in enumerate(["Mon", "Wed", "Fri"]):
        p.append(f'<text x="34" y="{y0 + (i*2+1)*(cell+gap) + 10}" font-family="{MONO}" '
                 f'font-size="9" fill="{DIM}" text-anchor="end">{dl}</text>')

    # one animate per week keeps the file small; the stagger reads as a fill wave
    for wi, w in enumerate(weeks):
        x = x0 + wi * (cell + gap)
        p.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                 f'begin="{wi*0.028:.2f}s" dur="0.35s" fill="freeze"/>')
        for day in w["contributionDays"]:
            y = y0 + day["weekday"] * (cell + gap)
            lv = level(day["contributionCount"])
            p.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                     f'fill="{HEAT[lv]}"/>')
        p.append('</g>')

    p.append(f'<text x="{x0}" y="212" font-family="{MONO}" font-size="10" fill="{DIM}">'
             f'peak day &#183; {peak} contributions</text>')
    lx = 790
    p.append(f'<text x="{lx-12}" y="212" font-family="{MONO}" font-size="10" '
             f'fill="{DIM}" text-anchor="end">less</text>')
    for i, c in enumerate(HEAT):
        p.append(f'<rect x="{lx + i*18}" y="202" width="13" height="13" rx="2.5" fill="{c}"/>')
    p.append(f'<text x="{lx + 5*18 + 4}" y="212" font-family="{MONO}" font-size="10" '
             f'fill="{DIM}">more</text>')
    return "\n".join(p + close(1000, 232))


# ----------------------------------------------------------------------- velocity

def build_velocity(d):
    cal = d["contributionsCollection"]["contributionCalendar"]
    by_month = collections.OrderedDict()
    for w in cal["weeks"]:
        for day in w["contributionDays"]:
            by_month[day["date"][:7]] = by_month.get(day["date"][:7], 0) + day["contributionCount"]
    months = list(by_month.items())[-13:]
    peak = max(v for _, v in months) or 1

    W, H, base, top = 1000, 270, 214, 74
    p = frame(W, H, "Monthly contribution volume for %s" % USER, "v")
    p.append(f'<text x="34" y="34" font-family="{MONO}" font-size="12" fill="{AMBER}" '
             f'letter-spacing="2.6">VELOCITY &#183; CONTRIBUTIONS PER MONTH</text>')

    for frac in (0.25, 0.5, 0.75, 1.0):
        y = base - frac * (base - top)
        p.append(f'<line x1="60" y1="{y:.1f}" x2="966" y2="{y:.1f}" stroke="{GRID}" '
                 f'stroke-opacity="0.07"/>'
                 f'<text x="52" y="{y+4:.1f}" font-family="{MONO}" font-size="9" '
                 f'fill="{DIM}" text-anchor="end">{int(peak*frac)}</text>')

    n = len(months)
    slot = 906 / n
    bw = min(46, slot - 10)
    this_month = datetime.date.today().strftime("%Y-%m")
    for i, (mon, val) in enumerate(months):
        partial = mon == this_month
        x = 60 + i * slot + (slot - bw) / 2
        h = (val / peak) * (base - top)
        is_peak = val == peak
        fill = AMBER if is_peak else "#8A6A0A"
        p.append(f'<rect x="{x:.1f}" y="{base}" width="{bw:.1f}" height="0" rx="3" fill="{fill}">'
                 f'<animate attributeName="height" from="0" to="{h:.1f}" dur="0.7s" '
                 f'begin="{0.2+i*0.06:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" to="{base-h:.1f}" dur="0.7s" '
                 f'begin="{0.2+i*0.06:.2f}s" fill="freeze"/></rect>')
        label = datetime.date(int(mon[:4]), int(mon[5:7]), 1).strftime("%b")
        p.append(f'<text x="{x+bw/2:.1f}" y="{base+18}" font-family="{MONO}" font-size="9.5" '
                 f'fill="{DIM}" text-anchor="middle">{label}</text>')
        if partial:
            p.append(f'<text x="{x+bw/2:.1f}" y="{base+30}" font-family="{MONO}" '
                     f'font-size="8" fill="#8A6A0A" text-anchor="middle">MTD</text>')
        if val:
            p.append(f'<text x="{x+bw/2:.1f}" y="{base-h-8:.1f}" font-family="{MONO}" '
                     f'font-size="9.5" fill="{AMBER if is_peak else DIM}" '
                     f'text-anchor="middle" opacity="0">'
                     f'<animate attributeName="opacity" from="0" to="1" dur="0.4s" '
                     f'begin="{0.9+i*0.06:.2f}s" fill="freeze"/>{val}</text>')

    p.append(f'<line x1="60" y1="{base}" x2="966" y2="{base}" stroke="{GRID}" stroke-opacity="0.2"/>')
    p.append(f'<text x="60" y="254" font-family="{MONO}" font-size="10.5" fill="{DIM}">'
             f'The curve is Vault-OS. Founding the company is the point where it leaves the floor.</text>')
    return "\n".join(p + close(W, H))


if __name__ == "__main__":
    data = fetch()
    c = data["contributionsCollection"]
    has_private = any(n.get("isPrivate") for n in data["repositories"]["nodes"])
    if c["restrictedContributionsCount"] == 0 and has_private:
        raise SystemExit(
            "refusing to publish: restrictedContributionsCount is 0 but private "
            "repositories exist, so this token cannot see private contributions.\n"
            "Add a classic PAT with `repo` scope as the STATS_TOKEN repository secret.")

    os.makedirs("assets", exist_ok=True)
    for name, svg in (("stats", build_stats(data)),
                      ("contrib", build_contrib(data)),
                      ("velocity", build_velocity(data))):
        path = "assets/%s.svg" % name
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote %s (%d bytes)" % (path, len(svg)))
