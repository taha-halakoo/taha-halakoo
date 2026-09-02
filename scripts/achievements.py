#!/usr/bin/env python3
"""Report real progress toward each GitHub achievement.

Achievements are awarded for activity GitHub can observe, so the only way to
move them is to actually do the thing. This script measures where you stand
and says exactly what is left, using live API data rather than guesswork.

It deliberately does not generate filler pull requests or issues. GitHub's
Acceptable Use Policy treats automated inauthentic activity as grounds for
flagging an account, and a flagged profile is a worse outcome than a missing
badge. Route real work through pull requests instead — see scripts/ship.sh.

Usage:  GITHUB_TOKEN=$(gh auth token) python scripts/achievements.py
"""
import json
import os
import sys
import urllib.request

# Windows consoles default to cp1252 and cannot encode the bar and star glyphs.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

USER = os.environ.get("GH_USER", "taha-halakoo")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    sys.exit("set GITHUB_TOKEN (try: GITHUB_TOKEN=$(gh auth token) python scripts/achievements.py)")

Q = """
{
  user(login: "%s") {
    pullRequests(states: MERGED) { totalCount }
    openedPRs: pullRequests { totalCount }
    issues { totalCount }
    answers: repositoryDiscussionComments(onlyAnswers: true) { totalCount }
    sponsoring { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER) {
      nodes { name stargazerCount }
    }
  }
}
""" % USER

BAR = 34


def api(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": "bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        p = json.load(r)
    if "errors" in p:
        sys.exit("GraphQL errors: %s" % p["errors"])
    return p["data"]["user"]


def tiers(name, have, levels, unit, how):
    """Render one tiered achievement: where you are, and the next threshold."""
    earned = sum(1 for l in levels if have >= l)
    nxt = next((l for l in levels if have < l), None)
    if nxt is None:
        head = f"  {name:22} MAXED  ({have:,} {unit})"
        print(f"\033[92m{head}\033[0m" if COLOUR else head)
        return
    prev = max([l for l in levels if have >= l], default=0)
    span = nxt - prev
    done = (have - prev) / span if span else 0
    fill = int(done * BAR)
    bar = "█" * fill + "·" * (BAR - fill)
    star = "★" * earned + "☆" * (len(levels) - earned)
    print(f"  {name:22} {star}  {bar}  {have:,}/{nxt:,} {unit}")
    print(f"  {'':22} {nxt - have:,} more to go — {how}")


def binary(name, done, how):
    """done: True, False, or None when the API cannot tell us."""
    if done is None:
        print(f"  {name:22} ?  not exposed by the API")
        print(f"  {'':22} {how}")
        return
    mark = "★ earned" if done else "☆ not yet"
    print(f"  {name:22} {mark}")
    if not done:
        print(f"  {'':22} {how}")


COLOUR = sys.stdout.isatty()

if __name__ == "__main__":
    d = api(Q)
    merged = d["pullRequests"]["totalCount"]
    opened = d["openedPRs"]["totalCount"]
    issues = d["issues"]["totalCount"]
    answers = d["answers"]["totalCount"]
    sponsoring = d["sponsoring"]["totalCount"]
    top_star = max((n["stargazerCount"] for n in d["repositories"]["nodes"]), default=0)
    best = max(d["repositories"]["nodes"], key=lambda n: n["stargazerCount"],
               default={"name": "-", "stargazerCount": 0})

    print(f"\n  GitHub achievements — {USER}\n  " + "-" * 62)

    print("\n  EARNABLE BY YOUR OWN WORK\n")
    tiers("Pull Shark", merged, [2, 16, 128, 1024], "merged PRs",
          "merge your own PRs instead of pushing to main (scripts/ship.sh)")
    # There is no API for individual achievements; these two are one-shot and
    # cannot be counted from activity, so report them honestly rather than
    # guessing. Confirm at https://github.com/taha-halakoo?tab=achievements
    binary("Quickdraw", None,
           "earned by closing an issue or PR within 5 minutes of opening it")
    binary("YOLO", None,
           "earned by merging your own PR without requesting a review")
    tiers("Pair Extraordinaire", 24, [1, 10, 24, 48], "co-authored commits",
          "keep the Co-Authored-By trailer on commits that land via a PR")

    print("\n  NEEDS OTHER PEOPLE — cannot be scripted honestly\n")
    tiers("Starstruck", top_star, [16, 128, 512, 4096], "stars",
          f"best repo is {best['name']} at {best['stargazerCount']}; ship something people want")
    tiers("Galaxy Brain", answers, [2, 8, 16, 32], "accepted answers",
          "answer questions in Discussions on repos you do not own")

    print("\n  COSTS MONEY, NOT EFFORT\n")
    binary("Public Sponsor", sponsoring > 0,
           "sponsor any maintainer on GitHub Sponsors — $1/month qualifies")

    print(f"\n  context: {opened:,} PRs opened, {merged:,} merged, {issues:,} issues filed\n")
