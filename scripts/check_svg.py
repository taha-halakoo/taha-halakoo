#!/usr/bin/env python3
"""Static legibility check for the README SVGs.

Two failure modes matter, and neither is visible by looking at one file:
  1. text that overruns the canvas at its own viewBox width
  2. text that lands below ~11.5px once GitHub scales the image to the column

Each layout is tested at the narrowest README column it is served into (see the
breakpoint table in diagrams.py), so the scale factor is column / viewBox width:

    wide    820 units   771px column   (a 1220px window, where wide takes over)
    medium  480 units   440px column   (a 521px window, with margin)
    narrow  300 units   293px column   (a 375px phone)
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
COLUMN = {"wide": 771.0, "medium": 440.0, "narrow": 293.0}
MIN_EFFECTIVE = 11.5
ADV = 0.605  # monospace advance per em
GLOB = os.environ.get("SVG_GLOB", "assets/*.svg")


def layout(path):
    for name in ("medium", "narrow"):
        if f"-{name}." in path:
            return name
    return "wide"


def rolling(root):
    """Digits inside a counter's roll are covers for text that is checked on its own."""
    return {id(e) for g in root.iter(NS + "g") if g.get("class") == "roll" for e in g.iter(NS + "text")}


fails = []
for path in sorted(glob.glob(GLOB)):
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    vw, vh = vb[2], vb[3]
    scale = min(1.0, COLUMN[layout(path)] / vw) if "btn-" in path else COLUMN[layout(path)] / vw
    skip = rolling(root)
    for el in root.iter(NS + "text"):
        txt = "".join(el.itertext()).strip()
        if not txt or id(el) in skip:
            continue
        size = float(el.get("font-size", 12))
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        ls = float(el.get("letter-spacing", 0) or 0)
        # a run with textLength is pinned to that width whatever the face
        w = float(el.get("textLength") or len(txt) * (size * ADV + ls))
        anchor = el.get("text-anchor", "start")
        left = x - w if anchor == "end" else (x - w / 2 if anchor == "middle" else x)
        right = left + w
        if left < -1 or right > vw + 1:
            fails.append(f"{path}: OVERFLOW x[{left:.0f},{right:.0f}] vs 0..{vw:.0f}  {txt[:44]!r}")
        if y > vh:
            fails.append(f"{path}: BELOW CANVAS y={y:.0f} > {vh:.0f}  {txt[:44]!r}")
        eff = size * scale
        if eff < MIN_EFFECTIVE:
            fails.append(f"{path}: TOO SMALL {size}px -> {eff:.1f}px rendered  {txt[:44]!r}")

print("\n".join(fails) if fails else "clean: no overflow, nothing below 11.5px rendered")
sys.exit(1 if fails else 0)
