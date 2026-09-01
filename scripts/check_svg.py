#!/usr/bin/env python3
"""Static legibility check for the README SVGs.

Two failure modes matter, and neither is visible by looking at one file:
  1. text that overruns the canvas at its own viewBox width
  2. text that lands below ~12px once GitHub scales the image to the column

GitHub's README column is 831px at a 1280px viewport and 293px on a 375px
phone, so the scale factor is column_width / viewBox_width.
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

COL_WIDE, COL_NARROW = 831.0, 293.0
MIN_EFFECTIVE = 11.5
GLOB = os.environ.get("SVG_GLOB", "assets/*.svg")
ADV = 0.605
GLOB = os.environ.get("SVG_GLOB", "assets/*.svg")  # monospace advance per em

fails = []
for path in sorted(glob.glob(GLOB)):
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    vw, vh = vb[2], vb[3]
    col = COL_NARROW if "-narrow" in path else COL_WIDE
    scale = col / vw
    for el in root.iter("{http://www.w3.org/2000/svg}text"):
        txt = "".join(el.itertext()).strip()
        if not txt:
            continue
        size = float(el.get("font-size", 12))
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        ls = float(el.get("letter-spacing", 0) or 0)
        w = len(txt) * (size * ADV + ls)
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
