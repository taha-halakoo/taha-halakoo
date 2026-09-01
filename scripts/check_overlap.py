#!/usr/bin/env python3
"""Detect text elements that collide with each other in the generated SVGs.

check_svg.py catches overflow and type size; it says nothing about two runs
occupying the same box, which is what makes a diagram look broken.
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
ADV = 0.605
GLOB = os.environ.get("SVG_GLOB", "assets/*.svg")


def box(el):
    txt = "".join(el.itertext()).strip()
    if not txt:
        return None
    size = float(el.get("font-size", 12))
    x, y = float(el.get("x", 0)), float(el.get("y", 0))
    ls = float(el.get("letter-spacing", 0) or 0)
    w = len(txt) * (size * ADV + ls)
    a = el.get("text-anchor", "start")
    left = x - w if a == "end" else (x - w / 2 if a == "middle" else x)
    return (left, y - size * 0.78, left + w, y + size * 0.24, txt, size)


def overlap(a, b):
    ix = min(a[2], b[2]) - max(a[0], b[0])
    iy = min(a[3], b[3]) - max(a[1], b[1])
    return ix > 1.0 and iy > 1.0, ix, iy


def phased(g):
    """True if this group is time-multiplexed: shown and hidden on a loop.

    The ledger deliberately draws the tampered block on top of the intact one
    at the same coordinates and alternates them, so those two never coexist on
    screen and must not be reported as a collision.
    """
    for a in g.iter(NS + "animate"):
        if (a.get("attributeName") == "opacity"
                and a.get("repeatCount") == "indefinite"
                and (a.get("values") or "").startswith("0;0;1")):
            return True
    return False


def collect(root):
    """Text boxes plus whether each sits inside a time-multiplexed group."""
    out = []
    for g in root.iter(NS + "g"):
        ph = phased(g)
        for e in g.findall(NS + "text"):
            b = box(e)
            if b:
                out.append((b, ph))
    seen = {id(e) for g in root.iter(NS + "g") for e in g.findall(NS + "text")}
    for e in root.iter(NS + "text"):
        if id(e) not in seen:
            b = box(e)
            if b:
                out.append((b, False))
    return out


fails = []
for path in sorted(glob.glob(GLOB)):
    items = collect(ET.parse(path).getroot())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (a, pa), (b, pb) = items[i], items[j]
            if pa or pb:
                continue
            hit, ix, iy = overlap(a, b)
            if hit:
                fails.append(f"{path}: {a[4][:26]!r} x {b[4][:26]!r} "
                             f"(overlap {ix:.0f}x{iy:.0f}px)")
print("\n".join(fails) if fails else "clean: no text collisions")
sys.exit(1 if fails else 0)
