#!/usr/bin/env python3
"""Ship missing repository hygiene as one pull request per change.

Every public repo was missing a disclosure policy, most were missing a licence,
and none had dependency scanning. Those are real gaps, not filler: without a
LICENSE the code is all-rights-reserved and nobody may legally use it, and
without SECURITY.md a researcher who finds a bug in Vault-OS tooling has no
channel to report it.

Each file lands as its own branch → PR → squash merge, which is also how
Pull Shark, YOLO and Pair Extraordinaire are earned: by doing the work the
badges measure, not by manufacturing empty pull requests.

Usage:  GITHUB_TOKEN=$(gh auth token) python scripts/hygiene.py [--dry-run]
"""
import base64
import json
import subprocess
import sys
import time

OWNER = "taha-halakoo"
NAME = "Taha Halakooei"
YEAR = "2026"
CONTACT = "taha@iron-gap.com"
DRY = "--dry-run" in sys.argv


def gh(args, data=None):
    cmd = ["gh", "api"] + args
    if data is not None:
        json.dump(data, open("_h.json", "w"))
        cmd += ["--input", "_h.json"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def exists(repo, path):
    code, _, _ = gh([f"repos/{OWNER}/{repo}/contents/{path}", "--jq", ".sha"])
    return code == 0


def default_branch(repo):
    _, out, _ = gh([f"repos/{OWNER}/{repo}", "--jq", ".default_branch"])
    return out or "main"


def ship(repo, path, content, title, body):
    """One file, one branch, one PR, merged."""
    if exists(repo, path):
        print(f"  skip   {repo}/{path} (already present)")
        return False
    base = default_branch(repo)
    code, sha, err = gh([f"repos/{OWNER}/{repo}/git/ref/heads/{base}", "--jq", ".object.sha"])
    if code:
        print(f"  FAIL   {repo}: cannot read {base} ({err[:60]})")
        return False
    branch = "hygiene/" + path.replace("/", "-").replace(".", "-").lower() + "-" + str(int(time.time()) % 100000)
    if DRY:
        print(f"  would  {repo}/{path}  ->  {branch}")
        return True

    code, _, err = gh(["-X", "POST", f"repos/{OWNER}/{repo}/git/refs"],
                      {"ref": f"refs/heads/{branch}", "sha": sha})
    if code:
        print(f"  FAIL   {repo}: branch ({err[:70]})")
        return False

    code, _, err = gh(["-X", "PUT", f"repos/{OWNER}/{repo}/contents/{path}"],
                      {"message": title + "\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
                       "content": base64.b64encode(content.encode()).decode(),
                       "branch": branch})
    if code:
        print(f"  FAIL   {repo}: commit ({err[:70]})")
        return False

    code, out, err = gh(["-X", "POST", f"repos/{OWNER}/{repo}/pulls", "--jq", ".number"],
                        {"title": title, "head": branch, "base": base,
                         "body": body + "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"})
    if code:
        print(f"  FAIL   {repo}: pr ({err[:70]})")
        return False
    pr = out

    code, _, err = gh(["-X", "PUT", f"repos/{OWNER}/{repo}/pulls/{pr}/merge"],
                      {"merge_method": "squash"})
    if code:
        print(f"  FAIL   {repo}#{pr}: merge ({err[:70]})")
        return False
    gh(["-X", "DELETE", f"repos/{OWNER}/{repo}/git/refs/heads/{branch}"])
    print(f"  merged {repo}#{pr}  {path}")
    return True


MIT = """MIT License

Copyright (c) %s %s

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""" % (YEAR, NAME)


def security(repo):
    return f"""# Security Policy

## Reporting a vulnerability

Report security issues privately to **{CONTACT}**. Do not open a public issue
for anything exploitable.

Please include what you need to make the problem reproducible: affected
version or commit, environment, steps, and the impact you believe it has. A
proof of concept helps, but a clear description is enough to start.

## What to expect

| Stage | Target |
|---|---|
| Acknowledgement | within 72 hours |
| Initial assessment | within 7 days |
| Fix or mitigation plan | within 30 days for exploitable issues |

You will get a straight answer either way, including when a report is not
something we consider a vulnerability and why.

## Scope

This policy covers the `{repo}` repository. Reports about IronGap's Vault-OS
appliance should go to {CONTACT} as well and will be handled under the
coordinated disclosure terms at https://www.iron-gap.com.

## Recognition

Researchers who report a valid issue are credited in the release notes for the
fix, unless they prefer otherwise.
"""


DEPENDABOT_NPM = """version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    groups:
      minor-and-patch:
        update-types: ["minor", "patch"]

  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
"""

DEPENDABOT_PIP = """version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5

  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
"""

DEPENDABOT_ACTIONS = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
"""

GITIGNORE_PY = """__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.ipynb_checkpoints/
.env
.DS_Store
Thumbs.db
*.task
"""

PY_CI = """name: Python check

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  compile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      # Byte-compile everything: catches syntax errors without needing the
      # heavier runtime dependencies (mediapipe, opencv) to install in CI.
      - name: Byte-compile sources
        run: python -m compileall -q .
"""

BUG_TEMPLATE = """---
name: Bug report
about: Something behaves differently from what it says it does
title: ''
labels: bug
assignees: ''
---

**What happened**

**What you expected instead**

**Steps to reproduce**
1.
2.
3.

**Environment**
- OS and version:
- Runtime version:
- Commit or release:

**Anything else**
Logs, screenshots, or a minimal reproduction if you have one.

> Do not report security vulnerabilities here — see SECURITY.md.
"""

TASKS = [
    # (repo, path, content, title, body)
    ("virtual-mouse", "SECURITY.md", security("virtual-mouse"),
     "docs: add security policy and disclosure contact",
     "There was no private channel for reporting a vulnerability. This adds one, with response targets that are actually meetable."),
    ("studyhub", "SECURITY.md", security("studyhub"),
     "docs: add security policy and disclosure contact",
     "StudyHub handles auth and user data through Supabase RBAC, so it needs a private disclosure channel."),
    ("Lumo-traces", "SECURITY.md", security("Lumo-traces"),
     "docs: add security policy and disclosure contact",
     "TRACES stores user location data. A private reporting channel matters more here than in most repos."),
    ("Polaris-Python-Assignments", "SECURITY.md", security("Polaris-Python-Assignments"),
     "docs: add security policy and disclosure contact",
     "Consistent disclosure policy across public repositories."),
    ("taha-halakoo", "SECURITY.md", security("taha-halakoo"),
     "docs: add security policy and disclosure contact",
     "The profile repo runs a workflow with a token; it should carry a disclosure policy like the rest."),

    ("virtual-mouse", "LICENSE", MIT, "chore: add MIT licence",
     "Without a licence file this code is all-rights-reserved by default, so nobody can legally use, fork or modify it. MIT matches the intent of publishing it."),
    ("studyhub", "LICENSE", MIT, "chore: add MIT licence",
     "Without a licence file the repository is all-rights-reserved and cannot be reused."),
    ("Polaris-Python-Assignments", "LICENSE", MIT, "chore: add MIT licence",
     "Coursework published for reference should say what others may do with it."),
    ("taha-halakoo", "LICENSE", MIT, "chore: add MIT licence",
     "Covers the generator scripts and diagram sources in this repository."),

    ("Polaris-Python-Assignments", ".gitignore", GITIGNORE_PY,
     "chore: ignore Python build and environment artefacts",
     "`__pycache__` and virtualenvs should not be tracked."),
    ("taha-halakoo", ".gitignore", GITIGNORE_PY,
     "chore: ignore Python and OS artefacts",
     "The generator scripts leave `__pycache__` behind on every run."),

    ("studyhub", ".github/dependabot.yml", DEPENDABOT_NPM,
     "chore: enable Dependabot for npm and actions",
     "Weekly dependency scanning, with minor and patch updates grouped so the PR volume stays sane."),
    ("Lumo-traces", ".github/dependabot.yml", DEPENDABOT_NPM,
     "chore: enable Dependabot for npm and actions",
     "The Fastify backend and Flutter monorepo pull a large npm tree; this keeps known-vulnerable versions visible."),
    ("virtual-mouse", ".github/dependabot.yml", DEPENDABOT_PIP,
     "chore: enable Dependabot for pip and actions",
     "mediapipe and opencv move quickly and have had CVEs; weekly scanning surfaces them."),
    ("Polaris-Python-Assignments", ".github/dependabot.yml", DEPENDABOT_ACTIONS,
     "chore: enable Dependabot for actions",
     "Keeps any workflow actions pinned to current versions."),
    ("taha-halakoo", ".github/dependabot.yml", DEPENDABOT_ACTIONS,
     "chore: enable Dependabot for actions",
     "The stats workflow uses checkout and setup-python; this keeps them current."),

    ("virtual-mouse", ".github/workflows/python.yml", PY_CI,
     "ci: byte-compile sources on push and pull request",
     "Catches syntax errors before they land. Deliberately does not install mediapipe or opencv, which would make CI slow and flaky for no extra signal."),
    ("Polaris-Python-Assignments", ".github/workflows/python.yml", PY_CI,
     "ci: byte-compile sources on push and pull request",
     "A syntax check across the assignments, cheap enough to run on every push."),

    ("virtual-mouse", ".github/ISSUE_TEMPLATE/bug_report.md", BUG_TEMPLATE,
     "chore: add a bug report template",
     "Prompts for the environment details that are always missing from the first message."),
    ("studyhub", ".github/ISSUE_TEMPLATE/bug_report.md", BUG_TEMPLATE,
     "chore: add a bug report template",
     "Prompts for reproduction steps and points security reports at SECURITY.md instead."),
    ("Lumo-traces", ".github/ISSUE_TEMPLATE/bug_report.md", BUG_TEMPLATE,
     "chore: add a bug report template",
     "Location bugs are hard to reproduce without device and OS details; the template asks for them."),
]

if __name__ == "__main__":
    print(f"\n  Repository hygiene — {len(TASKS)} changes"
          + ("  [DRY RUN]" if DRY else "") + "\n")
    shipped = 0
    for repo, path, content, title, body in TASKS:
        if ship(repo, path, content, title, body):
            shipped += 1
    print(f"\n  {shipped} pull requests merged\n")
    import os
    if os.path.exists("_h.json"):
        os.remove("_h.json")
