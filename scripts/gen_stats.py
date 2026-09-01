#!/usr/bin/env python3
"""Generate assets/stats.svg from live GitHub data.

Self-hosted replacement for the usual third-party README widgets, which rate-limit,
run out of quota, and eventually 402. Run by .github/workflows/stats.yml.
"""
import collections
import json
import os
import urllib.request

USER = os.environ.get("GH_USER", "taha-halakoo")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = "assets/stats.svg"

QUERY = """
{
  user(login: "%s") {
    followers { totalCount }
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
        return json.load(r)["data"]["user"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(d):
    c = d["contributionsCollection"]
    pub = c["totalCommitContributions"]
    priv = c["restrictedContributionsCount"]
    total = pub + priv

    # restrictedContributionsCount is only visible to a token authenticated as the
    # user. A repo-scoped GITHUB_TOKEN silently reports 0, which would quietly
    # rewrite the private-work figure to near-zero. Fail loudly instead of
    # publishing a number that is wrong.
    has_private = any(n.get("isPrivate") for n in d["repositories"]["nodes"])
    if priv == 0 and has_private:
        raise SystemExit(
            "refusing to publish: restrictedContributionsCount is 0 but private "
            "repositories exist, so this token cannot see private contributions.\n"
            "Add a classic PAT with `repo` scope as the STATS_TOKEN repository secret."
        )
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

    tiles = [
        (f"{total:,}", "COMMITS / 12 MO", "#FFC93C"),
        (f"{pct}%", "SHIPPED PRIVATELY", "#3FB950"),
        (f"{repos}", "REPOSITORIES", "#E4E6EB"),
        (f"{stars}", "STARS EARNED", "#E4E6EB"),
    ]

    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 250" width="1000" '
         'height="250" role="img" aria-label="GitHub activity for %s">' % esc(USER),
         '<defs><pattern id="gs" width="26" height="26" patternUnits="userSpaceOnUse">'
         '<path d="M26 0H0V26" fill="none" stroke="#FFC93C" stroke-opacity="0.045"/></pattern>'
         '<clipPath id="cs"><rect width="1000" height="250" rx="14"/></clipPath></defs>',
         '<g clip-path="url(#cs)"><rect width="1000" height="250" fill="#07070A"/>',
         '<rect width="1000" height="250" fill="url(#gs)"/>',
         '<text x="34" y="34" font-family="ui-monospace,Menlo,monospace" font-size="12" '
         'fill="#FFC93C" letter-spacing="2.6">SIGNAL &#183; LAST 12 MONTHS</text>']

    # stat tiles
    for i, (val, label, colr) in enumerate(tiles):
        x = 34 + i * 238
        p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                 f'begin="{i*0.14:.2f}s" dur="0.5s" fill="freeze"/>'
                 f'<rect x="{x}" y="54" width="222" height="86" rx="8" fill="#0E1116" '
                 f'stroke="#FFC93C" stroke-opacity="0.16"/>'
                 f'<text x="{x+18}" y="106" font-family="ui-monospace,Menlo,monospace" '
                 f'font-size="34" font-weight="700" fill="{colr}">{val}</text>'
                 f'<text x="{x+18}" y="127" font-family="ui-monospace,Menlo,monospace" '
                 f'font-size="10.5" fill="#5F6672" letter-spacing="1.7">{label}</text></g>')

    # language bar
    p.append('<text x="34" y="176" font-family="ui-monospace,Menlo,monospace" font-size="11" '
             'fill="#5F6672" letter-spacing="2.2">LANGUAGE DISTRIBUTION</text>')
    x = 34.0
    for name, size in top:
        w = size / tot * 932
        p.append(f'<rect x="{x:.1f}" y="188" width="0" height="14" fill="{col[name]}">'
                 f'<animate attributeName="width" from="0" to="{w:.1f}" dur="0.9s" '
                 f'begin="0.5s" fill="freeze"/></rect>')
        x += w + 2

    lx = 34
    for name, size in top:
        pctl = size * 100 / tot
        p.append(f'<circle cx="{lx+4}" cy="224" r="4" fill="{col[name]}"/>'
                 f'<text x="{lx+15}" y="228" font-family="ui-monospace,Menlo,monospace" '
                 f'font-size="11" fill="#8B929E">{esc(name)} {pctl:.1f}%</text>')
        lx += 22 + len(name) * 6.6 + 42

    p.append('<rect x="0.5" y="0.5" width="999" height="249" rx="14" fill="none" '
             'stroke="#FFC93C" stroke-opacity="0.14"/></g></svg>')
    return "\n".join(p)


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    svg = build(fetch())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes)")
