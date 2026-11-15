#!/usr/bin/env python3
"""Build every hand-authored panel on the profile, in three layouts.

The content comes from the CV: two companies (IronGap in amber, VEYMEER in ice),
the measured VEYMEER figures, the Vault-OS architecture, the trajectory and the
project map. gen_stats.py draws the panels that come from live GitHub data and
borrows the primitives defined here.

Why three layouts. An SVG rendered as <img> scales as a picture: the text does
not reflow, so a layout that is legible at 820px is unreadable at 293px. And
GitHub's README column does not shrink steadily with the window. From 768px a
sidebar appears and the column drops to under 400px, narrower than on a large
phone, then widens again:

    window        README column      layout drawn here
    up to 520     240 to 455         narrow, 300 units
    521 to 767    455 to 700         medium, 480 units
    768 to 859    390 to 480         narrow
    860 to 1219   480 to 770         medium
    1220 and up   770 to 846         wide, 820 units

Markdown picks the file with <picture><source media="(max-width: …)">, and
check_svg.py holds every layout to 11.5px of rendered type at the smallest
column it is served into.

Two rules for motion. Nothing essential is hidden behind an animation: every
element's resting attributes are its final state, and the entrance is an
animation that starts from zero, so a renderer that does not run SMIL shows the
finished panel instead of an empty one. And anything that loops is laid over
the content, never in place of it.
"""
import datetime
import math
import os

OUT = "assets"
BG, GRID, DIM, TEXT = "#07070A", "#FFC93C", "#5F6672", "#E4E6EB"
AMBER, GREEN, RED, MUTE = "#FFC93C", "#3FB950", "#F85149", "#8B929E"
PANEL, LINE = "#0E1116", "#8A7A4A"
ICE = "#4CC2FF"   # VEYMEER. Amber is IronGap; the pair separates under every CVD simulation.
WHITE = "#F2F2F5"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
ADV = 0.605       # monospace advance per em; every width estimate below rests on it
EASE = "0.2 0.7 0.2 1"

# file suffix, layout
VARIANTS = (("", "w"), ("-medium", "m"), ("-narrow", "n"))


class S:
    """Per-layout geometry and type scale.

    `n` is true for both stacked layouts (medium and narrow); `m` and `w` pick
    out one. Builders branch on `n` for structure and on `mode` for copy that
    was fitted to a width by hand.
    """
    def __init__(self, mode):
        if mode is True:      # callers that predate the medium layout pass a bool
            mode = "n"
        elif mode is False:
            mode = "w"
        self.mode = mode
        self.n = mode != "w"
        self.m = mode == "m"
        self.w = mode == "w"
        self.W = {"w": 820, "m": 480, "n": 300}[mode]
        self.pad = {"w": 28, "m": 18, "n": 14}[mode]
        self.label = {"w": 13.5, "m": 13, "n": 13}[mode]
        self.title = {"w": 17, "m": 16, "n": 15.5}[mode]
        self.body = 13.5
        self.det = {"w": 12.5, "m": 13, "n": 13}[mode]
        self.num = {"w": 38, "m": 30, "n": 28}[mode]
        self.inner = self.W - 2 * self.pad


def E(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chars(width_px, size):
    """How many monospace glyphs fit in width_px. Mono advance is ~0.6em."""
    return max(6, int(width_px / (size * ADV)))


def tw(txt, size, ls=0):
    """Rendered width of a monospace run."""
    return len(txt) * (size * ADV + ls)


def wrap(text, maxch):
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > maxch:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


_UID = ["x"]      # uid of the diagram being built, so tail() can match its defs
_ACC = [AMBER]    # and its accent colour


def head(s, h, alt, uid, extra_defs="", accent=None):
    _UID[0] = uid
    _ACC[0] = acc = accent or AMBER
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.W} {h}" width="{s.W}" '
        f'height="{h}" role="img" aria-label="{E(alt)}">',
        f'<title>{E(alt)}</title>',
        f'<defs><pattern id="g{uid}" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<path d="M26 0H0V26" fill="none" stroke="{GRID}" stroke-opacity="0.04"/></pattern>'
        f'{sweepdef(uid)}{hsweepdef(uid)}'
        f'<filter id="gl{uid}" x="-70%" y="-70%" width="240%" height="240%">'
        f'<feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/>'
        f'<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<radialGradient id="rg{uid}" cx="0" cy="0" r="0.95">'
        f'<stop offset="0" stop-color="{acc}" stop-opacity="0.13"/>'
        f'<stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="ac{uid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{acc}"/><stop offset="0.55" stop-color="{acc}" stop-opacity="0.25"/>'
        f'<stop offset="1" stop-color="{acc}" stop-opacity="0"/></linearGradient>{extra_defs}'
        f'<clipPath id="c{uid}"><rect width="{s.W}" height="{h}" rx="12"/></clipPath></defs>',
        f'<g clip-path="url(#c{uid})"><rect width="{s.W}" height="{h}" fill="{BG}"/>'
        f'<rect width="{s.W}" height="{h}" fill="url(#rg{uid})">{pulse(0.5, 1, 7.0)}</rect>'
        f'<rect width="{s.W}" height="{h}" fill="url(#g{uid})"/>'
        f'<rect width="{s.W}" height="2" fill="url(#ac{uid})"/>',
    ]


def tail(s, h, motion=True, corners=True):
    """Close the card. A light runs round the border of every panel, so none is
    ever completely still and none has anything moving across its text."""
    acc = _ACC[0]
    out = [f'<rect x="0.5" y="0.5" width="{s.W-1}" height="{h-1}" rx="12" fill="none" '
           f'stroke="{GRID}" stroke-opacity="0.16"/>']
    if motion:
        dur = max(9, round((s.W + h) / 95))
        # a comet: a short bright head leading a longer faint trail
        for dash, lead, op, wd in (("150 850", 0, 0.26, 1.2), ("44 956", 106, 0.95, 1.8)):
            out.append(f'<rect x="1" y="1" width="{s.W-2}" height="{h-2}" rx="11.5" fill="none" '
                       f'stroke="{acc}" stroke-opacity="{op}" stroke-width="{wd}" stroke-linecap="round" '
                       f'pathLength="1000" stroke-dasharray="{dash}" stroke-dashoffset="{-lead}">'
                       f'<animate attributeName="stroke-dashoffset" values="{1000-lead};{-lead}" '
                       f'dur="{dur}s" repeatCount="indefinite"/></rect>')
    if corners and s.w:   # below 820 the marks would land on the section label
        a, m = 12, 9
        W, H = s.W, h
        out.append(f'<path d="M{m} {m+a}V{m}h{a}M{W-m-a} {m}h{a}v{a}M{W-m} {H-m-a}v{a}h{-a}M{m+a} {H-m}h{-a}v{-a}" '
                   f'fill="none" stroke="{GRID}" stroke-opacity="0.45" stroke-width="1.2"/>')
    out.append('</g></svg>')
    return out


def sect(s, y, t, colour=None):
    """A bare section label. Kept for the organisation diagrams; panels here use title()."""
    return (f'<text x="{s.pad}" y="{y}" font-family="{MONO}" font-size="{s.label}" '
            f'fill="{colour or AMBER}" letter-spacing="2.2">{E(t)}</text>')


def title(s, y, label, colour=None, meta=None):
    """Section label, a rule running out to the right edge, and an optional note at its end."""
    out = [sect(s, y, label, colour)]
    x0 = s.pad + tw(label, s.label, 2.2) + 8
    x1 = s.W - s.pad
    if meta:
        out.append(t(x1, y, meta, s.det, DIM, anchor="end"))
        x1 -= tw(meta, s.det) + 12
    if x1 - x0 > 18:
        out.append(f'<line x1="{x0:.1f}" y1="{y-4.5}" x2="{x1:.1f}" y2="{y-4.5}" '
                   f'stroke="{colour or AMBER}" stroke-opacity="0.22"/>')
    return "".join(out)


# ------------------------------------------------------------------ animation

def fade(delay, dur=0.45, rise=8):
    """Entrance: fade in and settle upward. The element rests visible; this starts it from zero."""
    tot = delay + dur
    k = delay / tot
    a = (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{k:.3f};1" '
         f'dur="{tot:.2f}s" fill="freeze"/>')
    if rise:
        a += (f'<animateTransform attributeName="transform" type="translate" '
              f'values="0 {rise};0 {rise};0 0" keyTimes="0;{k:.3f};1" dur="{tot:.2f}s" '
              f'calcMode="spline" keySplines="0 0 1 1;{EASE}" fill="freeze"/>')
    return a


def anim(attr, v0, v1, delay, dur=0.8):
    """Grow one attribute from v0 to its resting value v1, eased, after a delay."""
    tot = delay + dur
    return (f'<animate attributeName="{attr}" values="{v0};{v0};{v1}" keyTimes="0;{delay/tot:.3f};1" '
            f'dur="{tot:.2f}s" calcMode="spline" keySplines="0 0 1 1;{EASE}" fill="freeze"/>')


def pulse(lo=0.35, hi=1.0, dur=2.4, begin=0.0):
    return (f'<animate attributeName="opacity" values="{hi};{lo};{hi}" dur="{dur}s" '
            f'begin="{begin}s" repeatCount="indefinite"/>')


def sweepdef(uid, colour=None, op=0.22):
    c = colour or AMBER
    return (f'<linearGradient id="sw{uid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{c}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{c}" stop-opacity="{op}"/>'
            f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></linearGradient>')


def sweep(uid, w, h, band=70, dur=6.0, x=0):
    """A soft light band travelling down the card, forever."""
    return (f'<rect x="{x}" y="0" width="{w}" height="{band}" fill="url(#sw{uid})" '
            f'pointer-events="none"><animate attributeName="y" values="{-band};{h}" '
            f'dur="{dur}s" repeatCount="indefinite"/></rect>')


def hsweep(uid, w, h, band=90, dur=5.0, y=0):
    """The same band travelling left to right."""
    return (f'<rect x="0" y="{y}" width="{band}" height="{h}" fill="url(#swh{uid})" '
            f'pointer-events="none"><animate attributeName="x" values="{-band};{w}" '
            f'dur="{dur}s" repeatCount="indefinite"/></rect>')


def hsweepdef(uid, colour=None, op=0.18):
    c = colour or AMBER
    return (f'<linearGradient id="swh{uid}" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{c}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{c}" stop-opacity="{op}"/>'
            f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></linearGradient>')


def travel(path_d, dur, begin=0.0, r=4.0, colour=None, uid=""):
    """A dot running along a path, fading in and out at the ends."""
    c = colour or AMBER
    return (f'<circle r="{r}" fill="{c}" opacity="0">'
            f'<animateMotion path="{path_d}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.12;0.85;1" '
            f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>')


def burst(cx, cy, r1=20, dur=2.6, begin=0.0, colour=None):
    """An expanding ring, like something landing."""
    c = colour or AMBER
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="none" stroke="{c}" stroke-width="2" opacity="0">'
            f'<animate attributeName="r" values="3;{r1}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.9;0" dur="{dur}s" begin="{begin}s" '
            f'repeatCount="indefinite"/></circle>')


def orbit(cx, cy, r, dur=9.0, colour=None, width=2):
    c = colour or AMBER
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{c}" '
            f'stroke-width="{width}" stroke-dasharray="3 3">'
            f'<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx:.1f} {cy:.1f}" to="360 {cx:.1f} {cy:.1f}" dur="{dur}s" '
            f'repeatCount="indefinite"/></circle>')


def drawline(length, dur=2.0, begin=0.0):
    return (f' stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">'
            f'<animate attributeName="stroke-dashoffset" from="{length:.0f}" to="0" '
            f'dur="{dur}s" begin="{begin}s" fill="freeze"/>')


def typeclip(uid, x, y, w, h, dur=1.6, begin=0.2):
    """Reveals text left to right once, then leaves it visible."""
    tot = begin + dur
    return (f'<clipPath id="tc{uid}"><rect x="{x}" y="{y}" width="{w:.1f}" height="{h}">'
            f'<animate attributeName="width" values="0;0;{w:.1f}" keyTimes="0;{begin/tot:.3f};1" '
            f'dur="{tot:.2f}s" fill="freeze"/></rect></clipPath>')


def caret(x, y, h=15, colour=None, begin=0.0):
    c = colour or GREEN
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="9" height="{h}" fill="{c}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="0.1s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" '
            f'begin="{begin+0.2}s" repeatCount="indefinite"/></rect>')


def card(s, x, y, w, h, stroke=GRID, op=0.28, fill=PANEL, hl=None):
    """A panel-coloured box. `hl=(begin, period)` makes its border flare once per period."""
    r = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="7" '
         f'fill="{fill}" stroke="{stroke}" stroke-opacity="{op}"')
    if not hl:
        return r + '/>'
    begin, period = hl
    return (r + f'><animate attributeName="stroke-opacity" values="{op};1;{op};{op}" '
            f'keyTimes="0;0.05;0.2;1" dur="{period}s" begin="{begin:.2f}s" repeatCount="indefinite"/></rect>')


def t(x, y, txt, size, fill=TEXT, anchor="start", ls=None, weight=None):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    w = f' font-weight="{weight}"' if weight else ""
    sp = ' xml:space="preserve"' if "  " in txt else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}"'
            f' fill="{fill}"{a}{l}{w}{sp}>{E(txt)}</text>')


_ROLL = [0]


def num(x, y, txt, size, fill, delay=0.3, bg=PANEL, anchor="start", weight=700):
    """A figure whose digits roll up to their value, like a counter settling.

    The figure itself is ordinary text and is always there. Each rolling digit
    is a cover drawn over it for the length of the roll and then removed, so a
    renderer that skips the animation still shows the number.
    """
    out = [t(x, y, txt, size, fill, anchor=anchor, weight=weight)]
    adv = size * ADV
    x0 = x - len(txt) * adv if anchor == "end" else x
    lh = round(size * 1.15, 1)
    col = 0
    for i, ch in enumerate(txt):
        if not ch.isdigit() or ch == "0":
            continue
        d = int(ch)
        cx = x0 + i * adv
        _ROLL[0] += 1
        cid = f"r{_UID[0]}{_ROLL[0]}"
        start = delay + col * 0.09
        tot = start + 0.75 + d * 0.05
        col += 1
        strip = "".join(
            '<tspan x="%.1f" %s>%d</tspan>' % (cx, 'y="%.1f"' % y if k == d else 'dy="%s"' % lh, k)
            for k in range(d, -1, -1))
        out.append(
            f'<clipPath id="{cid}"><rect x="{cx-0.5:.1f}" y="{y-size*0.86:.1f}" width="{adv+1:.1f}" '
            f'height="{size*1.12:.1f}"/></clipPath>'
            f'<g class="roll" opacity="0" clip-path="url(#{cid})">'
            f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.995;1" dur="{tot:.2f}s" fill="freeze"/>'
            f'<rect x="{cx-0.5:.1f}" y="{y-size*0.86:.1f}" width="{adv+1:.1f}" height="{size*1.12:.1f}" fill="{bg}"/>'
            f'<text font-family="{MONO}" font-size="{size}" fill="{fill}" font-weight="{weight}">{strip}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {-d*lh:.1f};0 {-d*lh:.1f};0 0" keyTimes="0;{start/tot:.3f};1" dur="{tot:.2f}s" '
            f'calcMode="spline" keySplines="0 0 1 1;0.16 0.8 0.3 1" fill="freeze"/></text></g>')
    return "".join(out)


def name_text(s, x, y, txt, size, length):
    """The one run set in a proportional face, with a glint crossing it.

    textLength pins its width, so the layout does not depend on which system
    font the viewer ends up with.
    """
    w = s.W
    span = round(w * 0.45)
    return (f'<linearGradient id="nm" gradientUnits="userSpaceOnUse" x1="{-span}" y1="0" x2="0" y2="0">'
            f'<stop offset="0" stop-color="#F4F4F6"/><stop offset="0.38" stop-color="#F4F4F6"/>'
            f'<stop offset="0.47" stop-color="#BFE9FF"/><stop offset="0.53" stop-color="#FFE7A0"/>'
            f'<stop offset="0.62" stop-color="#F4F4F6"/><stop offset="1" stop-color="#F4F4F6"/>'
            f'<animate attributeName="x1" values="{-span};{w};{w}" keyTimes="0;0.4;1" dur="7s" '
            f'begin="1.5s" repeatCount="indefinite"/>'
            f'<animate attributeName="x2" values="0;{w+span};{w+span}" keyTimes="0;0.4;1" dur="7s" '
            f'begin="1.5s" repeatCount="indefinite"/></linearGradient>'
            f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="{size}" font-weight="800" '
            f'fill="url(#nm) #F4F4F6" textLength="{length}" lengthAdjust="spacingAndGlyphs">{E(txt)}</text>')


def chips(s, x, y, maxw, labels, colour, hot=None, delay=None):
    """Flow labels as pills, wrapping at maxw. Returns (svg, height used).

    With `delay`, the pills arrive one after another from that moment.
    """
    size, ch, gap, padx = s.det, 24, 6, 9
    cx, cy, out = x, y, []
    for i, lab in enumerate(labels):
        w = tw(lab, size) + 2 * padx
        if cx > x and cx + w > x + maxw + 0.5:
            cx, cy = x, cy + ch + gap
        c = (hot or {}).get(lab)
        pill = (f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{w:.1f}" height="{ch}" rx="12" '
                f'fill="{c or colour}" fill-opacity="{0.16 if c else 0.07}" '
                f'stroke="{c or colour}" stroke-opacity="{0.9 if c else 0.38}"/>'
                + t(cx + padx, cy + 16.5, lab, size, WHITE if c else TEXT))
        out.append(pill if delay is None else f'<g>{fade(delay + i * 0.06, 0.35, 5)}{pill}</g>')
        cx += w + gap
    return "".join(out), cy + ch - y


def packets(s, h, n=8):
    """Small lights running along the background grid lines."""
    out = []
    for k in range(n):
        col = AMBER if k % 2 == 0 else ICE
        if k % 3 == 2:
            x = 26 * (2 + (k * 7) % max(3, s.W // 26 - 3))
            d = f"M{x} {h+6}V-6"
        else:
            y = 26 * (1 + (k * 5) % max(2, h // 26 - 1))
            d = f"M-6 {y}H{s.W+6}" if k % 2 == 0 else f"M{s.W+6} {y}H-6"
        out.append(travel(d, 8 + (k * 3) % 7, k * 1.1, 1.5, col))
    return f'<g opacity="0.75">{"".join(out)}</g>'


def footnote(s, y, lines, colour=GREEN):
    """A status dot and one or more lines of muted text. Returns (svg, height used)."""
    out = [f'<circle cx="{s.pad+5}" cy="{y-4}" r="3.6" fill="{colour}">{pulse(0.3, 1, 2.2)}</circle>']
    for j, ln in enumerate(lines):
        out.append(t(s.pad + 18, y + j * 17, ln, s.det, MUTE))
    return "".join(out), len(lines) * 17


def rule(s, y):
    return (f'<line x1="{s.pad}" y1="{y}" x2="{s.W-s.pad}" y2="{y}" stroke="{GRID}" stroke-opacity="0.12"/>')


def finish(s, h, alt, uid, body, accent=None, **kw):
    """Wrap a body that was laid out top to bottom, once its height is known."""
    return "\n".join(head(s, h, alt, uid, accent=accent) + body + tail(s, h, **kw)), h


# ----------------------------------------------------------------------- header

def emblem():
    """Vault core in amber with inference tokens orbiting it in ice. Drawn about the origin."""
    g = [f'<circle r="74" fill="none" stroke="{AMBER}" stroke-opacity="0.35" '
         f'stroke-width="5" stroke-dasharray="1 8.69"/>',
         f'<circle r="62" fill="none" stroke="{AMBER}" stroke-opacity="0.55" '
         f'stroke-width="1.3" stroke-dasharray="26 10 4 10">'
         f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" '
         f'dur="38s" repeatCount="indefinite"/></circle>',
         f'<circle r="46" fill="none" stroke="{ICE}" stroke-opacity="0.45" '
         f'stroke-width="1.3" stroke-dasharray="3 5">'
         f'<animateTransform attributeName="transform" type="rotate" from="360" to="0" '
         f'dur="26s" repeatCount="indefinite"/></circle>']
    for k, a in enumerate((0, 120, 240)):
        g.append(f'<circle cx="46" r="{3.2 - k * 0.5:.1f}" fill="{ICE}" transform="rotate({a})">'
                 f'<animateTransform attributeName="transform" type="rotate" from="{a}" to="{a+360}" '
                 f'dur="3.4s" repeatCount="indefinite"/></circle>')
    g.append(f'<circle cx="62" r="3" fill="{AMBER}" transform="rotate(200)">'
             f'<animateTransform attributeName="transform" type="rotate" from="200" to="-160" '
             f'dur="11s" repeatCount="indefinite"/></circle>')
    g.append(f'<rect x="-19" y="-19" width="38" height="38" rx="3" fill="{PANEL}" '
             f'stroke="{AMBER}" stroke-width="2" transform="rotate(45)"/>')
    g.append(f'<rect x="-7" y="-7" width="14" height="14" rx="1.5" fill="{AMBER}">'
             f'{pulse(0.35, 1, 2.6)}</rect>')
    g.append(burst(0, 0, 44, 4.2, 0.6, AMBER))
    return "".join(g)


def lockup(s, x, y, w, h, brand, delay):
    """One company cell: wordmark, what it is, one live line."""
    col = AMBER if brand == "irongap" else ICE
    full = s.mode != "n"
    g = [f'<g>{fade(delay)}', card(s, x, y, w, h, col, 0.4, hl=(delay + 2.5, 9)),
         f'<rect x="{x:.1f}" y="{y:.1f}" width="4" height="{h}" rx="2" fill="{col}">'
         f'{pulse(0.45, 1, 3.0, delay)}</rect>']
    tx = x + 18
    if brand == "irongap":
        g.append(t(tx, y + 27, "IRONGAP", 17, AMBER, weight=700, ls=0.6))
        if full:
            g.append(t(tx + tw("IRONGAP", 17, 0.6), y + 27, "_TECHNOLOGIES", 17, MUTE, weight=700, ls=0.6))
        what = "air-gapped AI for zero-trust environments" if full else "air-gapped AI, zero-trust"
        live = ("VAULT-OS", "SHIPPING · WINDOWS" if full else "SHIPPING")
    else:
        g.append(t(tx, y + 27, "VEYMEER", 17, WHITE, weight=700, ls=6.5))
        what = "from-scratch LLM inference engine" if full else "from-scratch LLM inference"
        live = ("400–500 TOK/S", "RTX 3050 LAPTOP GPU" if full else "RTX 3050")
    g.append(t(tx, y + 47, what, s.det, MUTE))
    ly = y + h - 14
    g.append(f'<circle cx="{tx+4:.1f}" cy="{ly-4:.1f}" r="3.4" fill="{GREEN}">{pulse(0.25, 1, 2.2, delay)}</circle>')
    g.append(t(tx + 15, ly, live[0], s.det, TEXT))
    g.append(t(x + w - 14, ly, live[1], s.det, DIM, anchor="end"))
    g.append('</g>')
    return "".join(g)


def header(s):
    alt = ("Taha Halakooei — Founder & Chief Architect. IronGap Technologies: air-gapped AI. "
           "VEYMEER: from-scratch LLM inference engine.")
    if s.mode == "n":
        ch = 92
        h = 140 + 2 * (ch + 10) + 6
        p = head(s, h, alt, "hd")
        p.append(packets(s, h, 5))
        p.append(title(s, 30, "FOUNDER & CHIEF ARCHITECT"))
        p.append(name_text(s, s.pad, 74, "Taha Halakooei", 36, 265))
        p.append(f'<g>{fade(0.5)}{t(s.pad, 100, "secure systems · AI infrastructure", s.det, MUTE)}'
                 f'{t(s.pad, 118, "full-stack engineering · Istanbul", s.det, MUTE)}</g>')
        p.append(lockup(s, s.pad, 136, s.inner, ch, "irongap", 0.8))
        p.append(lockup(s, s.pad, 136 + ch + 10, s.inner, ch, "veymeer", 1.0))
        return "\n".join(p + tail(s, h)), h

    if s.m:
        ch = 88
        h = 150 + 2 * (ch + 10) + 8
        p = head(s, h, alt, "hd")
        p.append(packets(s, h, 6))
        p.append(title(s, 30, "FOUNDER & CHIEF ARCHITECT").replace(
            f'x2="{s.W - s.pad:.1f}"', 'x2="352.0"'))   # the rule stops short of the emblem
        p.append(name_text(s, s.pad, 86, "Taha Halakooei", 46, 338))
        p.append(f'<g>{fade(0.3, 0.9, 0)}<g transform="translate(412 74) scale(0.6)">{emblem()}</g></g>')
        p.append(f'<g>{fade(0.5)}{t(s.pad, 112, "secure systems · AI infrastructure", s.det, MUTE)}'
                 f'{t(s.pad, 130, "full-stack engineering · Istanbul, Türkiye", s.det, MUTE)}</g>')
        p.append(lockup(s, s.pad, 148, s.inner, ch, "irongap", 0.8))
        p.append(lockup(s, s.pad, 148 + ch + 10, s.inner, ch, "veymeer", 1.0))
        return "\n".join(p + tail(s, h)), h

    h = 310
    p = head(s, h, alt, "hd")
    p.append(packets(s, h, 9))
    p.append(title(s, 42, "FOUNDER & CHIEF ARCHITECT  ·  ISTANBUL, TÜRKİYE").replace(
        f'x2="{s.W - s.pad:.1f}"', 'x2="596.0"'))   # the rule stops short of the emblem
    p.append(name_text(s, s.pad, 106, "Taha Halakooei", 62, 456))
    tag = "secure systems · AI infrastructure · full-stack engineering"
    w_ = tw(tag, 15)
    p.append(f'<defs>{typeclip("hd", s.pad, 124, w_, 22, dur=2.0, begin=0.4)}</defs>')
    p.append(f'<g clip-path="url(#tchd)">{t(s.pad, 139, tag, 15, TEXT)}</g>')
    p.append(caret(s.pad + w_ + 4, 126, 16, AMBER, begin=2.4))
    p.append(f'<g>{fade(2.5)}'
             f'{t(s.pad, 163, "from TPM-bound boot chains and hand-written CUDA kernels", s.det, DIM)}'
             f'{t(s.pad, 180, "to cross-platform Flutter and React applications", s.det, DIM)}</g>')
    p.append(f'<g>{fade(0.3, 0.9, 0)}<g transform="translate(700 106) scale(1.1)">{emblem()}</g></g>')
    cw = (s.inner - 14) / 2
    p.append(lockup(s, s.pad, 200, cw, 88, "irongap", 2.7))
    p.append(lockup(s, s.pad + cw + 14, 200, cw, 88, "veymeer", 2.9))
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- whoami

WHO = [
    ("whoami", ["Taha Halakooei — founder & chief architect,", "IronGap Technologies · VEYMEER"],
     ["Taha Halakooei — founder,", "IronGap Technologies · VEYMEER"], MUTE),
    ("cat ~/.focus", ["air-gapped AI appliances · LLM inference engines", "· secure systems, silicon to interface"],
     ["air-gapped AI appliances", "LLM inference engines"], MUTE),
    ("ls ~/building", ["vault-os/   veymeer/   strada/   bme-nexus/", "lumo/   traces/   rremote/   aegis/"],
     ["vault-os/ veymeer/ strada/", "nexus/ lumo/ traces/ rremote/"], AMBER),
    ("veymeer bench --gpu rtx3050", ["qwen2.5-7b · 400–500 tok/s on code editing · 12–15×",
                                     "output identical to standard decoding"],
     ["400–500 tok/s · 12–15× faster", "output identical to standard"], ICE),
    ("locale -a", ["fa_IR  tk_TM  en (C1)  tr (B1)  de (A2)  ar (reading)"],
     ["fa tk en:C1 tr:B1 de:A2 ar:read"], MUTE),
    ("echo $PRINCIPLE", ["isolation you can verify beats assurance", "you have to trust"],
     ["isolation you can verify beats", "assurance you have to trust"], AMBER),
]


def whoami(s):
    lh = 19 if s.mode == "n" else 21
    step = 0.45
    rows = [(cmd, narrow if s.mode == "n" else wide, col) for cmd, wide, narrow, col in WHO]
    h = 62 + sum(lh * (len(ls) + 1) + 9 for _, ls, _ in rows) + 22
    p = head(s, h, "Terminal introduction: who I am, what I build, and the principle behind it", "wh")
    p.append(f'<rect width="{s.W}" height="36" fill="{PANEL}"/>')
    for i, c in enumerate([RED, AMBER, GREEN]):
        p.append(f'<circle cx="{20+i*17}" cy="18" r="4.6" fill="{c}" fill-opacity="0.8"/>')
    p.append(t(78, 22, "taha@irongap — zsh", s.det, DIM))
    p.append(f'<line x1="0" y1="36" x2="{s.W}" y2="36" stroke="{GRID}" stroke-opacity="0.16"/>')
    clips = []
    y = 62
    for i, (cmd, lines, col) in enumerate(rows):
        at = 0.25 + i * step
        g = [f'<g>{fade(at, 0.3, 0)}', t(s.pad, y, "›", s.body, GREEN),
             f'<g clip-path="url(#tcw{i})">{t(s.pad + 16, y, cmd, s.body, TEXT)}</g></g>']
        for j, ln in enumerate(lines):   # output lands a beat after the command is typed
            g.append(f'<g>{fade(at + 0.32 + j * 0.07, 0.3, 4)}{t(s.pad, y + lh * (j + 1), ln, s.body, col)}</g>')
        clips.append(typeclip(f"w{i}", s.pad + 16, y - 14, tw(cmd, s.body), 18, dur=0.3, begin=at))
        p.append("".join(g))
        y += lh * (len(lines) + 1) + 9
    p.insert(2, f'<defs>{"".join(clips)}</defs>')
    end = 0.25 + len(rows) * step + 0.2
    p.append(f'<g>{fade(end, 0.2, 0)}{t(s.pad, y, "›", s.body, GREEN)}'
             f'<rect x="{s.pad+16}" y="{y-12}" width="9" height="15" fill="{GREEN}">'
             f'<animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" '
             f'begin="{end+0.2:.2f}s" repeatCount="indefinite"/></rect></g>')
    return "\n".join(p + tail(s, h, corners=False)), h


# --------------------------------------------------------------------- timeline
# A Gantt rather than a row of dots: the point is that four of these overlap.

D = datetime.date
TRACKS = [("SAMPAD", "exceptional talents programme", None, D(2025, 6, 30), "2013 – 2025", MUTE),
          ("GOLESTAN AXON", "systems & IT · iodine plant", D(2024, 6, 1), None, "JUN 2024", GREEN),
          ("YILDIZ TECHNICAL", "B.Sc. biomedical engineering", D(2025, 9, 1), None, "SEP 2025", "#8FB63C"),
          ("IRONGAP", "founder & chief architect", D(2026, 1, 1), None, "JAN 2026", AMBER),
          ("VEYMEER", "founder & engine architect", D(2026, 9, 1), None, "SEP 2026", ICE)]
T0 = D(2024, 1, 1)


def timeline(s):
    now = D.today()
    live = sum(1 for tr in TRACKS if tr[3] is None)
    alt = ("Trajectory as a Gantt chart: Sampad 2013 to 2025, Golestan Axon since June 2024, "
           "Yıldız Technical since September 2025, IronGap since January 2026, VEYMEER since "
           "September 2026. %d tracks running concurrently." % live)
    x0 = s.pad if s.n else s.pad + 268
    x1 = s.W - s.pad - (4 if s.n else 14)
    span = (now - T0).days

    def X(d):
        return x0 + max(0, (d - T0).days) / span * (x1 - x0)

    rh = 72 if s.n else 46
    top = 58 if s.n else 74
    h = top + len(TRACKS) * rh + (30 if s.n else 40)
    p = head(s, h, alt, "tl")
    p.append(title(s, 26 if s.n else 28, "TRAJECTORY"))
    yl = 46 if s.n else 58
    foot = h - (30 if s.n else 36)
    for yr in range(T0.year, now.year + 1):
        x = X(D(yr, 1, 1))
        if x1 - x < 34:
            continue
        p.append(f'<line x1="{x:.1f}" y1="{yl+6}" x2="{x:.1f}" y2="{foot}" stroke="{GRID}" stroke-opacity="0.09"/>')
        p.append(t(x + (0 if s.n else 5), yl, str(yr), s.det, DIM))
    p.append(t(x1, yl, "NOW", s.det, TEXT, anchor="end", ls=1.2))
    p.append(f'<line x1="{x1:.1f}" y1="{yl+6}" x2="{x1:.1f}" y2="{foot}" stroke="{TEXT}" '
             f'stroke-opacity="0.4" stroke-dasharray="2 4">'
             f'<animate attributeName="stroke-dashoffset" values="0;-12" dur="1.6s" repeatCount="indefinite"/></line>')
    for i, (name, role, start, end, lab, col) in enumerate(TRACKS):
        y = top + i * rh
        xs, xe = X(start or T0), X(end or now)
        by = y + (46 if s.n else 12)
        at = 0.2 + i * 0.22
        g = [f'<g>{fade(at)}']
        if s.n:
            g.append(t(s.pad, y + 16, name, s.title, TEXT))
            g.append(t(s.W - s.pad, y + 16, lab, s.det, DIM, anchor="end"))
            g.append(t(s.pad, y + 35, role, s.det, DIM))
        else:
            g.append(t(s.pad, y + 19, name, s.body, TEXT, weight=700))
            g.append(t(s.pad, y + 36, role, s.det, DIM))
            if start is None:
                g.append(t(xe + 9, by + 11, lab, s.det, DIM))
            else:
                g.append(t(xs - 9, by + 11, lab, s.det, DIM, anchor="end"))
        g.append('</g>')
        p.append("".join(g))
        fill = f'url(#tlf{i})' if start is None else col
        if start is None:
            p.append(f'<defs><linearGradient id="tlf{i}" x1="0" y1="0" x2="1" y2="0">'
                     f'<stop offset="0" stop-color="{col}" stop-opacity="0.15"/>'
                     f'<stop offset="0.35" stop-color="{col}" stop-opacity="0.75"/>'
                     f'<stop offset="1" stop-color="{col}" stop-opacity="0.75"/></linearGradient></defs>')
        p.append(f'<rect x="{xs:.1f}" y="{by}" width="{xe-xs:.1f}" height="14" rx="3" fill="{fill}">'
                 f'{anim("width", 0, f"{xe-xs:.1f}", at + 0.1, 0.9)}</rect>')
        if end is None:
            # still running: a glint travels up the bar to today, where the end pulses
            p.append(travel(f"M{xs+4:.1f} {by+7}H{x1-4:.1f}", 3.2 + (xe - xs) / 160, 1.6 + i * 0.7, 2.6, WHITE))
            p.append(f'<g>{fade(at + 1.0, 0.4, 0)}'
                     f'<circle cx="{x1:.1f}" cy="{by+7}" r="4.5" fill="{col}" stroke="{BG}" stroke-width="2">'
                     f'{pulse(0.4, 1, 2.4, i * 0.3)}</circle>'
                     f'{burst(x1, by + 7, 13, 3.0, 1.4 + i * 0.5, col)}</g>')
    svg, _ = footnote(s, h - 14, [f"{live} tracks running concurrently" if s.w
                                  else f"{live} tracks running at once"])
    p.append(svg)
    return "\n".join(p + tail(s, h)), h


# ------------------------------------------------------------------------ depth

LAYERS = [("Interface", "cross-platform clients, offline-first state, local-network discovery",
           "React 19 · Next.js · Flutter · Electron · Tauri", GREEN),
          ("Orchestration", "DAG workflow and agent engine, sandboxed execution, MCP servers",
           "Node.js · Fastify · MCP · WebSockets", "#5FB84B"),
          ("Inference", "GGUF loading, KV cache, speculative decoding, pluggable backends",
           "Rust · CUDA C++ · vLLM · TensorRT-LLM", "#8FB63C"),
          ("Data", "vector search, geofencing, row-level security, hash-chained audit",
           "PostgreSQL · pgvector · PostGIS · Supabase", "#C0BE34"),
          ("Operating system", "PID 1 init, initramfs builder, disk provisioning, QEMU harness",
           "Rust · Linux boot · LUKS2 · Bash", "#E0C630"),
          ("Silicon", "TPM-bound enclave, sealed keys, GPU kernels compiled at runtime",
           "TPM 2.0 · NVRTC · AES-GCM · ECDSA", AMBER)]


def depth(s):
    if s.n:
        budget = chars(s.inner - 28, s.det)
        laid = [(n, wrap(d, budget), wrap(tc, budget), c) for n, d, tc, c in LAYERS]
        dmax = max(len(d) for _, d, _, _ in laid)
        tmax = max(len(tc) for _, _, tc, _ in laid)
        rh = 26 + dmax * 17 + 4 + tmax * 17 + 6
    else:
        laid = [(n, [d], [tc], c) for n, d, tc, c in LAYERS]
        dmax = 1
        rh = 56
    h = 46 + len(laid) * (rh + 8) + 16
    p = head(s, h, "The six layers I work across, from interface down to silicon", "dp")
    p.append(title(s, 28, "THE STACK I WORK ACROSS", meta=None if s.mode == "n" else "interface → silicon"))
    period = 6.0
    for i, (name, dl, tl_, col) in enumerate(laid):
        y = 46 + i * (rh + 8)
        # a request falls through the stack: each layer flares as it passes
        g = [f'<g>{fade(0.2 + (len(laid)-i) * 0.12)}',
             card(s, s.pad, y, s.inner, rh, col, 0.32, hl=(1.6 + i * period / 8, period)),
             f'<rect x="{s.pad}" y="{y}" width="4" height="{rh}" rx="2" fill="{col}">'
             f'{pulse(0.45, 1, 3.0, i * 0.35)}</rect>',
             t(s.pad + 15, y + 22, name, s.title, TEXT)]
        for j, ln in enumerate(dl):
            g.append(t(s.pad + 15, y + 41 + j * 17, ln, s.det, DIM))
        if s.n:
            for j, ln in enumerate(tl_):
                g.append(t(s.pad + 15, y + 41 + dmax * 17 + 4 + j * 17, ln, s.det, col))
        else:
            g.append(t(s.W - s.pad - 14, y + 22, tl_[0], s.det, col, anchor="end"))
        g.append('</g>')
        p.append("".join(g))
    p.append(travel(f"M{s.pad+2} 46V{h-24}", period * 0.75, 1.6, 3.0, WHITE))
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- method

STEPS = [("1 · REPRODUCE", "make it happen on demand", "kill power at 18 of 22GB", GRID),
         ("2 · ISOLATE", "cut until only the failure is left", "unpack, or the resume index?", GRID),
         ("3 · FALSIFY", "try hard to prove the diagnosis wrong", "what else explains this?", AMBER),
         ("4 · FIX", "smallest change that holds", "not the most clever one", GRID),
         ("5 · VERIFY", "add the check that would have caught it", "shutdown now verifies", GREEN)]


def method(s):
    period = 6.5
    if s.n:
        budget = chars(s.inner - 28, s.det)
        laid = [(n, wrap(d, budget), wrap(e, budget), c) for n, d, e, c in STEPS]
        dmax = max(len(d) for _, d, _, _ in laid)
        emax = max(len(e) for _, _, e, _ in laid)
        rh = 26 + dmax * 17 + 6 + emax * 17 + 4
        h = 46 + len(laid) * (rh + 12) + 12
        p = head(s, h, "How I work a failure", "mt")
        p.append(title(s, 28, "HOW I WORK A FAILURE"))
        for i, (name, dl, el, col) in enumerate(laid):
            y = 46 + i * (rh + 12)
            hl = AMBER if col == AMBER else (GREEN if col == GREEN else TEXT)
            g = [f'<g>{fade(0.2 + i * 0.2)}',
                 card(s, s.pad, y, s.inner, rh, col, 0.34, hl=(1.4 + i * period / 5, period)),
                 t(s.pad + 14, y + 21, name, s.title, hl)]
            for j, ln in enumerate(dl):
                g.append(t(s.pad + 14, y + 40 + j * 17, ln, s.det, DIM))
            for j, ln in enumerate(el):
                g.append(t(s.pad + 14, y + 40 + dmax * 17 + 6 + j * 17, ln, s.det, LINE))
            g.append('</g>')
            p.append("".join(g))
            if i < len(laid) - 1:
                p.append(f'<path d="M{s.pad+20} {y+rh} v12" stroke="{AMBER}" stroke-opacity="0.4" stroke-width="1.5"/>')
        p.append(travel(f"M{s.W-s.pad} 46V{h-12}", period, 1.4, 3.2, AMBER))
        return "\n".join(p + tail(s, h)), h

    bw = (s.inner - 4 * 12) / 5
    budget = chars(bw - 24, s.det)
    laid = [(n, wrap(d, budget), wrap(e, budget), c) for n, d, e, c in STEPS]
    body_h = max(len(d) for _, d, _, _ in laid)
    ex_h = max(len(e) for _, _, e, _ in laid)
    bh = body_h * 16 + ex_h * 15 + 53   # last example line sits 10px clear of the border
    top = 58
    h = top + bh + 78
    p = head(s, h, "How I work a failure: reproduce, isolate, falsify, fix, verify", "mt")
    p.append(title(s, 28, "HOW I WORK A FAILURE"))
    for i, (name, dl, el, col) in enumerate(laid):
        x = s.pad + i * (bw + 12)
        hl = AMBER if col == AMBER else (GREEN if col == GREEN else TEXT)
        g = [f'<g>{fade(0.2 + i * 0.22)}',
             card(s, x, top, bw, bh, col, 0.34, hl=(1.4 + i * period / 5, period)),
             t(x + 12, top + 22, name, s.body, hl)]
        for j, ln in enumerate(dl):
            g.append(t(x + 12, top + 42 + j * 16, ln, s.det, DIM))
        for j, ln in enumerate(el):
            g.append(t(x + 12, top + 42 + body_h * 16 + 12 + j * 15, ln, s.det, LINE))
        g.append('</g>')
        p.append("".join(g))
        if i < 4:
            p.append(f'<path d="M{x+bw+1} {top+bh/2} h8" stroke="{AMBER}" stroke-opacity="0.5" stroke-width="1.6"/>')
    # the marker rides the top edge of the cards so it never crosses the text
    p.append(travel(f"M{s.pad+bw/2:.0f} {top} H{s.pad+4*(bw+12)+bw/2:.0f}", period, 1.4, 4.0, AMBER))
    p.append(burst(s.pad + 2 * (bw + 12) + bw / 2, top, 18, 3.2, 2.6, AMBER))
    p.append(travel(f"M{s.pad+bw*2+24+bw/2:.0f} {top+bh:.0f} V{top+bh+20:.0f} "
                    f"H{s.pad+bw/2:.0f} V{top+bh:.0f}", 4.0, 3.4, 3.4, AMBER))
    ry = top + bh + 20
    p.append(f'<path d="M{s.pad+bw*2+24+bw/2} {top+bh} v20 H{s.pad+bw/2} v-20" fill="none" '
             f'stroke="{AMBER}" stroke-opacity="0.35" stroke-width="1.4" stroke-dasharray="5 4">'
             f'<animate attributeName="stroke-dashoffset" values="0;18" dur="1.8s" repeatCount="indefinite"/></path>')
    p.append(t(s.W / 2 - 90, ry + 22, "falsified → the diagnosis was wrong, start again", s.det, LINE, anchor="middle"))
    return "\n".join(p + tail(s, h)), h


# -------------------------------------------------------------------------- bme

PAIRS = [(["Fail-safe design around people", "who cannot consent to the risk"],
          ["A boot chain that halts", "rather than degrades"]),
         (["Regulation as a design input,", "not paperwork stapled on after"],
          ["HIPAA and CMMC satisfied by", "architecture, not a control matrix"]),
         (["Signal processing and the", "statistics of noisy measurement"],
          ["Embedding similarity, filter", "design, One-Euro smoothing"]),
         (["How hard device validation", "really is"],
          ["Deep suspicion of anything", "that only demos well"])]


def bme(s):
    alt = "How biomedical engineering training maps onto secure systems work"
    if s.n:
        ph = 58
        h = 52 + len(PAIRS) * (ph * 2 + 26) + 12
        p = head(s, h, alt, "bm")
        p.append(title(s, 26, "THE DEGREE IS NOT A DETOUR"))
        y = 46
        for i, (left, right) in enumerate(PAIRS):
            p.append(f'<g>{fade(0.2 + i * 0.22)}'
                     f'{card(s, s.pad, y, s.inner, ph, GREEN, 0.3)}'
                     f'{t(s.pad+12, y+23, left[0], s.det, TEXT)}'
                     f'{t(s.pad+12, y+41, left[1], s.det, TEXT)}'
                     f'<path d="M{s.W/2} {y+ph+3} v13" stroke="{AMBER}" stroke-opacity="0.5" stroke-width="1.5"/>'
                     f'{card(s, s.pad, y+ph+20, s.inner, ph, AMBER, 0.3, hl=(1.6 + i * 0.55, 2.4))}'
                     f'{t(s.pad+12, y+ph+43, right[0], s.det, TEXT)}'
                     f'{t(s.pad+12, y+ph+61, right[1], s.det, TEXT)}</g>')
            p.append(travel(f"M{s.W/2:.0f} {y+ph+3} v13", 2.4, i * 0.55, 3.2, AMBER))
            y += ph * 2 + 26
        return "\n".join(p + tail(s, h)), h

    ph, gap = 56, 14
    h = 76 + len(PAIRS) * (ph + gap) + 8
    p = head(s, h, alt, "bm")
    p.append(title(s, 28, "WHY THE BIOMEDICAL DEGREE IS NOT A DETOUR"))
    cw = (s.inner - 90) / 2
    p.append(t(s.pad, 56, "WHAT THE DEGREE TEACHES", s.det, GREEN, ls=1.6))
    p.append(t(s.pad + cw + 90, 56, "WHAT IT BECAME IN MY WORK", s.det, AMBER, ls=1.6))
    for i, (left, right) in enumerate(PAIRS):
        y = 68 + i * (ph + gap)
        rx = s.pad + cw + 90
        p.append(f'<g>{fade(0.2 + i * 0.22)}'
                 f'{card(s, s.pad, y, cw, ph, GREEN, 0.3)}'
                 f'{t(s.pad+13, y+23, left[0], s.body, TEXT)}{t(s.pad+13, y+42, left[1], s.body, TEXT)}'
                 f'<path d="M{s.pad+cw+10} {y+ph/2} h68" stroke="{AMBER}" stroke-opacity="0.4" stroke-width="1.5"/>'
                 f'<path d="M{s.pad+cw+72} {y+ph/2-4} l6 4 -6 4z" fill="{AMBER}" fill-opacity="0.6"/>'
                 f'{card(s, rx, y, cw, ph, AMBER, 0.3, hl=(2.0 + i * 0.6, 2.4))}'
                 f'{t(rx+13, y+23, right[0], s.body, TEXT)}{t(rx+13, y+42, right[1], s.body, TEXT)}</g>')
        p.append(travel(f"M{s.pad+cw+10:.0f} {y+ph/2:.0f}h62", 2.4, i * 0.6, 3.2, AMBER))
    return "\n".join(p + tail(s, h)), h


# -------------------------------------------------------------------- portfolio

DOMAINS = [("SECURE INFRA", AMBER,
            [("Vault-OS", "air-gapped AI knowledge vault", "TPM 2.0 · pgvector · RAG"),
             ("Appliance OS", "bare-metal Rust OS, own PID 1", "initramfs · LUKS2 · QEMU"),
             ("Vault clients", "five platforms plus desktop", "Flutter · Electron"),
             ("rremote", "secure remote desktop", "Rust · Tokio · WebSockets")]),
           ("INFERENCE & AGENTS", ICE,
            [("VEYMEER", "from-scratch LLM inference engine", "Rust · CUDA · WebGPU"),
             ("STRADA", "desktop IDE on the engine", "Tauri · coding agent"),
             ("Console MCP", "audited agent access to the console", "MCP · every write logged"),
             ("Content pipeline", "drafts posts from dev activity", "Edge Functions · pg_cron")]),
           ("PLATFORMS", "#5FB84B",
            [("YTU BME Nexus", "department platform, 13 languages", "React · Supabase RLS"),
             ("Traces", "content unlocked within 20 m", "PostGIS · Fastify · Flutter"),
             ("StudyHub", "modular productivity dashboard", "React · Supabase RBAC"),
             ("WidgetOS", "embeddable Notion widgets", "Next.js · Drizzle · Stripe")]),
           ("AUTONOMY & INDUSTRY", "#C0BE34",
            [("Lumo", "drone swarm collision avoidance", "717 → 0 collisions"),
             ("Aegis", "hydrogen-electric VTOL cargo drone", "systems engineering"),
             ("Virtual Mouse", "hands-free pointer control", "MediaPipe · One-Euro"),
             ("Golestan Axon", "systems & IT at an iodine plant", "since 2024")])]


def portfolio(s):
    n_items = sum(len(i) for _, _, i in DOMAINS)
    alt = "Map of %d pieces of work across secure infrastructure, inference, platforms and autonomy" % n_items
    roam = 1.1   # seconds between one card flaring and the next
    if s.mode == "n":
        budget = chars(s.inner - 24, s.det)
        body, y, k = [title(s, 26, "WHAT I HAVE BUILT")], 48, 0
        for name, col, items in DOMAINS:
            body.append(t(s.pad, y, name, s.det, col, ls=1.5))
            body.append(f'<line x1="{s.pad}" y1="{y+7}" x2="{s.W-s.pad}" y2="{y+7}" stroke="{col}" stroke-opacity="0.3"/>')
            y += 20
            for nm, desc, tech in items:
                dl = wrap(desc, budget)
                ch = 30 + len(dl) * 17
                g = [f'<g>{fade(0.15 + k * 0.07)}',
                     card(s, s.pad, y, s.inner, ch, col, 0.26, hl=(2.5 + k * roam, n_items * roam)),
                     t(s.pad + 12, y + 21, nm, s.title, TEXT)]
                for j, ln in enumerate(dl):
                    g.append(t(s.pad + 12, y + 39 + j * 17, ln, s.det, DIM))
                g.append('</g>')
                body.append("".join(g))
                y += ch + 8
                k += 1
            y += 20
        return finish(s, y - 14, alt, "pf", body)

    cols = 4 if s.w else 2
    lh = 15 if s.w else 16
    cw = (s.inner - (cols - 1) * 12) / cols
    budget = chars(cw - 24, s.det)
    laid = [(wrap(d, budget), wrap(tc, budget)) for _, _, items in DOMAINS for _, d, tc in items]
    dmax = max(len(d) for d, _ in laid)
    tmax = max(len(tc) for _, tc in laid)
    ch = 26 + dmax * lh + 8 + tmax * lh + 4
    rows = max(len(i) for _, _, i in DOMAINS)
    block = 22 + rows * (ch + 8) + 14
    h = 58 + math.ceil(len(DOMAINS) / cols) * block - 14 + 6
    p = head(s, h, alt, "pf")
    p.append(title(s, 28, "WHAT I HAVE BUILT", meta=f"{n_items} pieces of work"))
    k = 0
    for c, (name, col, items) in enumerate(DOMAINS):
        x = s.pad + (c % cols) * (cw + 12)
        y0 = 58 + (c // cols) * block
        p.append(t(x, y0, name, s.det, col, ls=1.3))
        p.append(f'<line x1="{x}" y1="{y0+8}" x2="{x+cw}" y2="{y0+8}" stroke="{col}" stroke-opacity="0.3"/>')
        for r, (nm, desc, tech) in enumerate(items):
            y = y0 + 22 + r * (ch + 8)
            dl, tl_ = wrap(desc, budget), wrap(tech, budget)
            g = [f'<g>{fade(0.15 + k * 0.07)}',
                 card(s, x, y, cw, ch, col, 0.26, hl=(2.5 + k * roam, n_items * roam)),
                 t(x + 12, y + 21, nm, s.body, TEXT, weight=700)]
            for j, ln in enumerate(dl):
                g.append(t(x + 12, y + 39 + j * lh, ln, s.det, DIM))
            for j, ln in enumerate(tl_):
                g.append(t(x + 12, y + 39 + dmax * lh + 8 + j * lh, ln, s.det, LINE))
            g.append('</g>')
            p.append("".join(g))
            k += 1
    return "\n".join(p + tail(s, h)), h


# ------------------------------------------------------------------------ vault

VAULT = [("CLIENTS", "local network only", GREEN,
          ["Android", "iOS", "Windows", "macOS", "Linux", "Electron desktop",
           "LAN discovery", "certificate pinning"]),
         ("VAULT-OS CORE", "Fastify · React 19", AMBER,
          ["offline LLM + RAG", "tiered RBAC", "DAG workflows", "sandboxed agents",
           "document ingestion", "speech-to-text", "team chat", "retention policies"]),
         ("INFERENCE", "pluggable engines", ICE,
          ["Ollama", "vLLM", "TensorRT-LLM", "OpenAI-compatible", "VEYMEER"]),
         ("ENCLAVE", "encrypted · TPM-bound", "#E0C630",
          ["PostgreSQL + pgvector", "native, no Docker", "schema repaired on every boot"]),
         ("TRUST ROOT", "fail-deadly", AMBER,
          ["AES-256-GCM sealed config", "scrypt key derivation", "hardware-tethered licence",
           "ECDSA-signed ledger", "SHA-256 hash chain", "clock-integrity checks",
           "NIST SP 800-88 erasure"]),
         ("APPLIANCE OS", "Rust · bare metal", "#C0BE34",
          ["PID 1 init", "initramfs builder", "desktop shell", "compute fabric",
           "TPM-sealed LUKS2", "QEMU test harness"])]


def perimeter(s, x, y, w, h, tag):
    """The air gap, drawn as a marching dashed boundary with its name set into the top edge."""
    tgw = tw(tag, s.det, 1.4)
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" '
            f'stroke="{AMBER}" stroke-opacity="0.5" stroke-width="1.4" stroke-dasharray="7 6">'
            f'<animate attributeName="stroke-dashoffset" from="0" to="-52" dur="6s" repeatCount="indefinite"/></rect>'
            f'<rect x="{x+w-20-tgw-8:.1f}" y="{y-8}" width="{tgw+16:.1f}" height="16" fill="{BG}"/>'
            + t(x + w - 20, y + 5, tag, s.det, AMBER, anchor="end", ls=1.4))


def vault(s):
    alt = ("Vault-OS architecture inside the air gap: clients on the local network, the Vault-OS core, "
           "a pluggable inference layer, a TPM-bound encrypted enclave holding PostgreSQL and pgvector, "
           "the fail-deadly trust root, and a Rust appliance operating system underneath.")
    hot = {"VEYMEER": ICE}
    period = 5.5
    if s.n:
        inset = 8 if s.mode == "n" else 10
        x, w = s.pad + (0 if s.mode == "n" else 2), s.inner - (0 if s.mode == "n" else 4)
        body = [title(s, 26, "VAULT-OS" if s.mode == "n" else "VAULT-OS · AIR-GAPPED AI KNOWLEDGE VAULT")]
        y0 = y = 62
        for i, (name, cap, col, labs) in enumerate(VAULT):
            svg, chh = chips(s, x + 12, y + 52, w - 24, labs, col, hot, delay=0.5 + i * 0.16)
            lh = 52 + chh + 12
            body.append(f'<g>{fade(0.2 + i * 0.16)}'
                        f'{card(s, x, y, w, lh, col, 0.3, hl=(1.6 + i * period / 7, period))}'
                        f'<rect x="{x}" y="{y}" width="4" height="{lh}" rx="2" fill="{col}">'
                        f'{pulse(0.45, 1, 3.0, i * 0.35)}</rect>'
                        f'{t(x+12, y+22, name, s.title, TEXT)}{t(x+12, y+40, cap, s.det, DIM)}</g>{svg}')
            y += lh + 10
        body.insert(1, perimeter(s, x - inset, y0 - 12, w + 2 * inset, y - y0 + 14,
                                 "AIR GAP" if s.mode == "n" else "AIR-GAPPED PERIMETER"))
        body.append(travel(f"M{x+2} {y0}V{y-10}", period, 1.6, 3.2, WHITE))
        svg, fh = footnote(s, y + 26, ["offline by design · no Docker"] if s.mode == "n"
                           else ["offline by design · native, without Docker"])
        body.append(svg)
        return finish(s, y + 26 + fh - 3, alt, "vt", body)

    x, w = s.pad + 14, s.inner - 28
    cx0 = x + 196
    laid = []
    for name, cap, col, labs in VAULT:
        _, chh = chips(s, 0, 0, w - 196 - 12, labs, col, hot)
        laid.append((name, cap, col, labs, max(52, chh + 24)))
    top = 66
    body_h = sum(l[4] + 12 for l in laid) - 12
    h = top + body_h + 14 + 44
    p = head(s, h, alt, "vt")
    p.append(title(s, 28, "VAULT-OS · THE AIR-GAPPED AI KNOWLEDGE VAULT"))
    # the perimeter: everything the product needs is drawn inside it
    p.append(perimeter(s, s.pad, 52, s.inner, body_h + 28, "AIR-GAPPED PERIMETER"))
    y = top
    for i, (name, cap, col, labs, lh) in enumerate(laid):
        svg, _ = chips(s, cx0, y + (12 if lh > 52 else 14), w - 196 - 12, labs, col, hot,
                       delay=0.5 + i * 0.16)
        p.append(f'<g>{fade(0.2 + i * 0.16)}'
                 f'{card(s, x, y, w, lh, col, 0.3, hl=(1.6 + i * period / 7, period))}'
                 f'<rect x="{x}" y="{y}" width="4" height="{lh}" rx="2" fill="{col}">'
                 f'{pulse(0.45, 1, 3.0, i * 0.35)}</rect>'
                 f'{t(x+16, y+23, name, s.body, TEXT, weight=700)}{t(x+16, y+40, cap, s.det, DIM)}</g>{svg}')
        if i < len(laid) - 1:
            p.append(f'<path d="M{x+2} {y+lh} v12" stroke="{col}" stroke-opacity="0.6" stroke-width="2"/>')
        y += lh + 12
    p.append(travel(f"M{x+2} {top} V{top+body_h}", period, 1.6, 3.2, WHITE))
    svg, _ = footnote(s, h - 16, ["offline by design · runs fully native, without Docker · shipping on Windows"])
    p.append(svg)
    return "\n".join(p + tail(s, h)), h


# ---------------------------------------------------------------------- veymeer
# Every figure below is one the engine was measured at. Nothing is derived
# except 38×, which is 1.9 / 0.05.

TILES_V = [("400–500", "TOK/S · CODE EDIT", "TOK/S"), ("12–15×", "VS STD DECODING", "FASTER"),
           ("0.05 s", "TO FIRST TOKEN", "FIRST TOKEN"), ("0", "TOKENS DIFFERENT", "OUTPUT DIFF")]
RACE = 13.5      # midpoint of the measured 12–15× range
CYC = 9.0        # seconds per loop
GREY = "#5F6672"
V_SUB = "Qwen2.5-7B · RTX 3050 laptop GPU · lossless speculative decoding"
V_CAP = "same model, same GPU, same output — bars fill at 1× and 13.5×, the midpoint of the measured range"
V_FOOT = "beats llama.cpp on a public 26-prompt benchmark, with output identical to standard decoding"


def stat(s, x, y, w, h, val, label, colour, delay, size, ls=1.3):
    return (f'<g>{fade(delay, 0.5)}{card(s, x, y, w, h, GRID, 0.16)}'
            f'<rect x="{x+14:.1f}" y="{y+12:.1f}" width="22" height="3" rx="1.5" fill="{colour}">'
            f'{anim("width", 0, 22, delay + 0.3, 0.6)}</rect>'
            f'{num(x+14, y+h-29, val, size, WHITE, delay + 0.35)}'
            f'{t(x+14, y+h-10, label, s.det, DIM, ls=ls)}</g>')


def lane(x, y, w, colour, ratio, uid):
    """A track that fills with tokens; `ratio` is how many times faster than 1×."""
    full = 0.9 / ratio
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="16" rx="3" fill="{PANEL}" '
            f'stroke="{GRID}" stroke-opacity="0.12"/>'
            f'<clipPath id="ln{uid}"><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="16">'
            f'<animate attributeName="width" values="0;{w:.1f};{w:.1f}" keyTimes="0;{full:.4f};1" '
            f'dur="{CYC}s" repeatCount="indefinite"/></rect></clipPath>'
            f'<line x1="{x+3:.1f}" y1="{y+8}" x2="{x+w-3:.1f}" y2="{y+8}" stroke="{colour}" '
            f'stroke-width="8" stroke-dasharray="7 3" clip-path="url(#ln{uid})"/>')


def finished(cx, cy, ratio, colour):
    """A ring that goes off at the instant a lane completes."""
    k = 0.9 / ratio
    return (f'<circle cx="{cx:.1f}" cy="{cy}" r="3" fill="none" stroke="{colour}" stroke-width="2" opacity="0">'
            f'<animate attributeName="r" values="3;3;20;20" keyTimes="0;{k:.4f};{k+0.12:.4f};1" '
            f'dur="{CYC}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.9;0;0" keyTimes="0;{k:.4f};{k+0.12:.4f};1" '
            f'dur="{CYC}s" repeatCount="indefinite"/></circle>')


def bar(x, y, w, colour, delay):
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="14" rx="3" fill="{colour}">'
            f'{anim("width", 0, f"{w:.1f}", delay, 0.8)}</rect>')


LANES = [("standard decoding", "1×", GREY, 1), ("VEYMEER", "12–15×", ICE, RACE)]
TTFT = [("no cache", "1.9 s", GREY, 1.0), ("prompt cache", "0.05 s · 38× sooner", ICE, 0.05 / 1.9)]


def veymeer(s):
    alt = ("VEYMEER measured on an RTX 3050 laptop GPU running Qwen2.5-7B: 400 to 500 tokens per second "
           "on code editing, 12 to 15 times faster than standard decoding, time to first token cut from "
           "1.9 seconds to 0.05 seconds by prompt caching, and output identical to standard decoding.")
    if s.n:
        budget = chars(s.inner, s.det)
        tw_, th = (s.inner - 10) / 2, (84 if s.m else 76)
        body = [title(s, 26, "VEYMEER · MEASURED", ICE)]
        for j, ln in enumerate(V_SUB.rsplit(" · ", 1)):   # broken at the last separator, not mid-phrase
            body.append(t(s.pad, 46 + j * 17, ln, s.det, DIM))
        for i, (v, wide_lab, lab) in enumerate(TILES_V):
            body.append(stat(s, s.pad + (i % 2) * (tw_ + 10), 76 + (i // 2) * (th + 10), tw_, th,
                             v, wide_lab if s.m else lab, ICE, 0.1 * i, 30 if s.m else 25,
                             1.3 if s.m else 0))
        y = 76 + 2 * (th + 10) + 24
        body.append(t(s.pad, y, "DECODE SPEED · ANIMATION TO SCALE" if s.m else "DECODE SPEED · TO SCALE",
                      s.det, DIM, ls=1.4))
        for k, (lab, val, col, ratio) in enumerate(LANES):
            ly = y + 26 + k * 50
            body.append(t(s.pad, ly, lab, s.det, MUTE if k == 0 else TEXT))
            body.append(t(s.W - s.pad, ly, val, s.det, TEXT, anchor="end"))
            body.append(lane(s.pad, ly + 9, s.inner, col, ratio, f"n{k}"))
        body.append(finished(s.W - s.pad - 6, y + 26 + 50 + 17, RACE, ICE))
        y += 26 + 2 * 50 + 4
        for ln in wrap(V_CAP, budget):
            body.append(t(s.pad, y, ln, s.det, DIM))
            y += 17
        y += 20
        body.append(t(s.pad, y, "TIME TO FIRST TOKEN", s.det, DIM, ls=1.4))
        for k, (lab, val, col, frac) in enumerate(TTFT):
            ly = y + 26 + k * 46
            body.append(t(s.pad, ly, lab, s.det, MUTE if k == 0 else TEXT))
            body.append(t(s.W - s.pad, ly, val, s.det, TEXT, anchor="end"))
            body.append(bar(s.pad, ly + 9, s.inner * frac, col, 0.6 + k * 0.2))
        y += 26 + 2 * 46 + 12
        body.append(rule(s, y - 14))
        svg, fh = footnote(s, y + 8, wrap(V_FOOT, chars(s.inner - 18, s.det)))
        body.append(svg)
        return finish(s, y + 8 + fh + 1, alt, "vm", body, accent=ICE)

    tw_, th = (s.inner - 3 * 12) / 4, 84
    h = 404
    p = head(s, h, alt, "vm", accent=ICE)
    p.append(title(s, 28, "VEYMEER · MEASURED", ICE, meta=V_SUB))
    for i, (v, lab, _) in enumerate(TILES_V):
        p.append(stat(s, s.pad + i * (tw_ + 12), 46, tw_, th, v, lab, ICE, 0.12 * i, 34))
    lx, tx = s.pad + 196, s.pad + 212
    p.append(t(s.pad, 166, "DECODE SPEED · ANIMATION TO SCALE", s.det, DIM, ls=1.6))
    for k, (lab, val, col, ratio) in enumerate(LANES):
        y = 180 + k * 30
        p.append(t(s.pad, y + 13, lab, s.det, MUTE if k == 0 else TEXT))
        p.append(t(lx, y + 13, val, s.det, TEXT, anchor="end"))
        p.append(lane(tx, y, s.W - s.pad - tx, col, ratio, f"w{k}"))
    p.append(finished(s.W - s.pad - 6, 218, RACE, ICE))
    p.append(t(s.pad, 254, "same model · same GPU · same output — bars fill at 1× and 13.5×, the midpoint",
               s.det, DIM))
    p.append(t(s.pad, 292, "TIME TO FIRST TOKEN · PROMPT CACHING", s.det, DIM, ls=1.6))
    scale = 420
    for k, (lab, val, col, frac) in enumerate(TTFT):
        y = 304 + k * 26
        p.append(t(s.pad, y + 12, lab, s.det, MUTE if k == 0 else TEXT))
        p.append(bar(tx, y, scale * frac, col, 0.6 + k * 0.2))
        p.append(f'<g>{fade(1.2 + k * 0.2, 0.4, 0)}{t(tx + scale * frac + 9, y + 12, val, s.det, TEXT)}</g>')
    p.append(rule(s, 364))
    p.append(footnote(s, 386, [V_FOOT])[0])
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- engine

STAGES = [("GGUF", "model loader"), ("BPE", "tokenizer"),
          ("KERNELS", "runtime-built CUDA via NVRTC"), ("KV CACHE", "attention state"),
          ("SCHEDULER", "decode scheduling"), ("API", "OpenAI compatible")]
BACKENDS = [("CUDA", "NVIDIA"), ("WebGPU", "AMD · Intel · Apple")]
CAPS = ["lossless speculative decoding", "prompt caching", "weight streaming beyond VRAM",
        "structured output", "tool calling", "multi-machine sharding over mTLS"]
STRADA = ["Tauri", "VS Code extensions", "integrated debugging", "autonomous coding agent"]
FLOW = 3.6   # seconds for a token to cross the pipeline


def stage_grid(s, top, cols):
    """The pipeline as boxes, `cols` to a row, lit in order as a token passes. Returns (svg, height)."""
    bw = (s.inner - (cols - 1) * 14) / cols
    budget = chars(bw - 22, s.det)
    laid = [(n, wrap(d, budget)) for n, d in STAGES]
    bh = 32 + max(len(d) for _, d in laid) * 16 + 10
    out = []
    for i, (nm, dl) in enumerate(laid):
        x = s.pad + (i % cols) * (bw + 14)
        y = top + (i // cols) * (bh + 14)
        g = [f'<g>{fade(0.2 + i * 0.18)}',
             card(s, x, y, bw, bh, ICE, 0.32, hl=(1.2 + i * FLOW / len(laid), FLOW)),
             t(x + 11, y + 23, nm, s.body, TEXT, weight=700)]
        for j, ln in enumerate(dl):
            g.append(t(x + 11, y + 43 + j * 16, ln, s.det, DIM))
        g.append('</g>')
        out.append("".join(g))
        if i % cols != cols - 1 and i < len(laid) - 1:
            out.append(f'<path d="M{x+bw+2:.1f} {y+bh/2} h7" stroke="{ICE}" stroke-opacity="0.6" stroke-width="1.6"/>'
                       f'<path d="M{x+bw+8:.1f} {y+bh/2-4} l5 4 -5 4z" fill="{ICE}" fill-opacity="0.7"/>')
    rows = math.ceil(len(laid) / cols)
    for r in range(rows):   # one token, crossing each row in turn
        y = top + r * (bh + 14) + bh
        a, b = r / rows, (r + 1) / rows
        out.append(f'<circle r="3" fill="{ICE}" opacity="0">'
                   f'<animateMotion path="M{s.pad+6} {y}H{s.W-s.pad-6}" dur="{FLOW}s" begin="1.2s" '
                   f'repeatCount="indefinite" calcMode="linear" keyPoints="0;0;1;1" '
                   f'keyTimes="0;{a:.3f};{b:.3f};1"/>'
                   f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                   f'keyTimes="0;{a:.3f};{a+0.04:.3f};{b-0.04:.3f};{b:.3f};1" dur="{FLOW}s" begin="1.2s" '
                   f'repeatCount="indefinite"/></circle>')
    return "".join(out), rows * (bh + 14) - 14


def strada_card(s, y, w_tag):
    """STRADA: the IDE built on the engine. Returns (svg, height)."""
    _, sth = chips(s, 0, 0, s.inner - 32, STRADA, ICE)
    stacked = s.mode == "n"
    hh = (54 if stacked else 44) + sth + 14
    svg, _ = chips(s, s.pad + 16, y + (54 if stacked else 44), s.inner - 32, STRADA, ICE, delay=2.2)
    out = [f'<g>{fade(2.0)}{card(s, s.pad, y, s.inner, hh, ICE, 0.5, hl=(4.0, 8))}'
           f'<rect x="{s.pad}" y="{y}" width="4" height="{hh}" rx="2" fill="{ICE}">{pulse(0.45, 1, 3.0)}</rect>'
           f'{t(s.pad+16, y+(24 if stacked else 27), "STRADA", s.title, WHITE, weight=700, ls=3)}']
    if stacked:
        out.append(t(s.pad + 16, y + 42, "desktop IDE on the engine", s.det, DIM))
    else:
        out.append(t(s.pad + 16 + w_tag, y + 27, "a desktop IDE built on the engine", s.det, DIM))
    out.append('</g>' + svg)
    return "".join(out), hh


def engine(s):
    alt = ("VEYMEER engine, built from first principles in Rust, CUDA and Python: GGUF loader, BPE "
           "tokenizer, CUDA kernels compiled at runtime via NVRTC, KV cache, scheduler and an "
           "OpenAI-compatible API, with CUDA and WebGPU backends. STRADA, a desktop IDE, is built on it.")
    if s.mode == "n":
        bh = 50
        body = [title(s, 26, "VEYMEER · THE ENGINE", ICE),
                t(s.pad, 46, "from first principles, in Rust,", s.det, DIM),
                t(s.pad, 63, "CUDA and Python", s.det, DIM)]
        y = 76
        for i, (nm, d) in enumerate(STAGES):
            body.append(f'<g>{fade(0.2 + i * 0.14)}'
                        f'{card(s, s.pad, y, s.inner, bh, ICE, 0.3, hl=(1.2 + i * FLOW / 6, FLOW))}'
                        f'{t(s.pad+14, y+21, nm, s.title, TEXT)}{t(s.pad+14, y+39, d, s.det, DIM)}</g>')
            if i < len(STAGES) - 1:
                body.append(f'<path d="M{s.pad+20} {y+bh} v8" stroke="{ICE}" stroke-opacity="0.5" stroke-width="1.5"/>')
            y += bh + 8
        body.append(travel(f"M{s.pad} 78V{y-10}", FLOW, 1.2, 3.0, ICE))
        y += 16
    else:
        body = [title(s, 28, "VEYMEER · THE ENGINE, FROM FIRST PRINCIPLES" if s.w else "VEYMEER · THE ENGINE",
                      ICE, meta="Rust · CUDA · Python")]
        svg, gh = stage_grid(s, 48, 6 if s.w else 3)
        body.append(svg)
        y = 48 + gh + 34
    body.append(t(s.pad, y - 10, "BACKENDS", s.det, DIM, ls=1.6))
    if s.n:
        for i, (nm, v) in enumerate(BACKENDS):
            body.append(f'<g>{fade(1.3 + i * 0.18)}{card(s, s.pad, y, s.inner, 44, ICE, 0.3)}'
                        f'{t(s.pad+14, y+27, nm, s.title, TEXT)}'
                        f'{t(s.W-s.pad-14, y+27, v, s.det, MUTE, anchor="end")}</g>')
            y += 52
        y -= 8
    else:
        hw = (s.inner - 14) / 2
        for i, (nm, v) in enumerate(BACKENDS):
            x = s.pad + i * (hw + 14)
            body.append(f'<g>{fade(1.3 + i * 0.18)}{card(s, x, y, hw, 44, ICE, 0.3)}'
                        f'{t(x+14, y+27, nm, s.title, TEXT, weight=700)}'
                        f'{t(x+hw-14, y+27, v, s.det, MUTE, anchor="end")}</g>')
        y += 44
    y += 34
    body.append(t(s.pad, y - 10, "ON TOP OF THE LOOP", s.det, DIM, ls=1.6))
    svg, caph = chips(s, s.pad, y, s.inner, CAPS, ICE, delay=1.7)
    body.append(svg)
    y += caph + 18
    svg, sh = strada_card(s, y, 134)
    body.append(svg)
    return finish(s, y + sh + 16, alt, "en", body, accent=ICE)


# ------------------------------------------------------------------------ swarm
# The two arenas are a schematic of the crossing, not simulator output: every
# drone starts on the ring and must reach the point opposite. Ungoverned they
# all arrive at the centre together. Governed, they slow into the congestion
# and pass around it. The 717 and the 0 are the simulation's own figures.

N_DRONES = 60
SW = 7.0


def arena(cx, cy, r, governed):
    col = GREEN if governed else RED
    b = round(r * 0.48)
    g = [f'<circle cx="{cx}" cy="{cy}" r="{r+9}" fill="{PANEL}" stroke="{GRID}" stroke-opacity="0.14"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-opacity="0.22" '
         f'stroke-dasharray="2 5"/>',
         f'<g transform="translate({cx} {cy})">']
    if governed:
        mot = (f'<animateMotion path="M0 0A{r} {b} 0 0 1 {-2*r} 0" dur="{SW}s" repeatCount="indefinite" '
               f'calcMode="spline" keyPoints="0;0.5;1;1" keyTimes="0;0.43;0.86;1" '
               f'keySplines="0.2 0.5 0.6 1;0.4 0 0.8 0.5;0 0 1 1"/>')
    else:
        mot = (f'<animateMotion path="M0 0H{-2*r}" dur="{SW}s" repeatCount="indefinite" '
               f'calcMode="linear" keyPoints="0;1;1" keyTimes="0;0.6;1"/>'
               f'<animate attributeName="opacity" values="1;1;0.22;0.22" keyTimes="0;0.29;0.33;1" '
               f'dur="{SW}s" repeatCount="indefinite"/>')
    for i in range(N_DRONES):
        # at rest each drone sits on the ring, so the arena is populated even without motion
        g.append(f'<g transform="rotate({i * 360 / N_DRONES:g})"><circle cx="{r}" r="1.7" fill="{col}">{mot}</circle></g>')
    g.append('</g>')
    if not governed:
        g.append(f'<circle cx="{cx}" cy="{cy}" r="0" fill="{RED}" opacity="0">'
                 f'<animate attributeName="r" values="0;0;{r*0.5:.0f};{r*0.5:.0f}" keyTimes="0;0.27;0.4;1" '
                 f'dur="{SW}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0.75;0;0" keyTimes="0;0.29;0.42;1" '
                 f'dur="{SW}s" repeatCount="indefinite"/></circle>')
        for k in range(3):   # shock rings
            g.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="none" stroke="{RED}" stroke-width="1.5" opacity="0">'
                     f'<animate attributeName="r" values="4;4;{r+6};{r+6}" '
                     f'keyTimes="0;{0.29+k*0.04:.2f};{0.5+k*0.06:.2f};1" dur="{SW}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0;0.7;0;0" '
                     f'keyTimes="0;{0.29+k*0.04:.2f};{0.5+k*0.06:.2f};1" dur="{SW}s" repeatCount="indefinite"/></circle>')
    return "".join(g)


def tally(s, cx, y, governed, size):
    """The count under an arena. The ungoverned one flashes when the swarm meets."""
    col = GREEN if governed else RED
    out = [num(cx - 6, y, "0" if governed else "717", size, col, 0.8, bg=BG, anchor="end"),
           t(cx + 5, y - 2, "collisions", s.det, DIM)]
    if not governed:
        w_ = 3 * size * ADV
        out.append(f'<rect x="{cx-6-w_-6:.1f}" y="{y-size:.1f}" width="{w_+12:.1f}" height="{size*1.3:.1f}" rx="5" '
                   f'fill="{RED}" opacity="0"><animate attributeName="opacity" values="0;0;0.3;0;0" '
                   f'keyTimes="0;0.29;0.33;0.5;1" dur="{SW}s" repeatCount="indefinite"/></rect>')
    return "".join(out)


GOV = [("collisions: 717 → 0", "collisions: 717 → 0"),
       ("all 60 drones reach their goal", "all 60 reach their goal"),
       ("decentralised, no central planner", "no central planner")]


def governor(s, x, y, w):
    hh = 118 + len(GOV) * 22
    g = [f'<g>{fade(0.6)}', card(s, x, y, w, hh, AMBER, 0.35, hl=(SW * 0.86, SW)),
         t(x + 16, y + 25, "THE GOVERNOR", s.det, AMBER, ls=1.6),
         t(x + 16, y + 62, "v ≤ √(a·g)", 26, WHITE, weight=700),
         t(x + 16, y + 85, "a speed limit derived from", s.det, DIM),
         t(x + 16, y + 102, "turning physics", s.det, DIM), '</g>']
    for i, pair in enumerate(GOV):
        ln = pair[1] if s.mode == "n" else pair[0]
        ly = y + 132 + i * 22
        g.append(f'<g>{fade(1.0 + i * 0.2, 0.4, 5)}'
                 f'<circle cx="{x+20}" cy="{ly-4}" r="3.4" fill="{GREEN}">{pulse(0.3, 1, 2.4, i * 0.4)}</circle>'
                 f'{t(x + 32, ly, ln, s.det, TEXT)}</g>')
    return "".join(g), hh


def swarm(s):
    alt = ("Lumo, decentralised collision avoidance for drone swarms. In a 60-drone worst-case crossing, "
           "a speed governor derived from turning physics reduced collisions from 717 to zero, "
           "with every drone still reaching its goal.")
    names = ("UNGOVERNED", "SPEED GOVERNOR")
    if s.mode == "n":
        r, cx = 80, s.W // 2
        body = [title(s, 26, "LUMO · DRONE SWARM"),
                t(s.pad, 46, "60 drones swap sides through one", s.det, DIM),
                t(s.pad, 63, "crossing point: the worst case", s.det, DIM)]
        y = 74
        for gov in (False, True):
            body.append(t(cx, y + 20, names[gov], s.det, TEXT if gov else MUTE, anchor="middle", ls=1.6))
            body.append(arena(cx, y + 34 + r + 9, r, gov))
            body.append(tally(s, cx, y + 34 + 2 * r + 18 + 30, gov, 26))
            y += 2 * r + 18 + 84
        svg, gh = governor(s, s.pad, y + 8, s.inner)
        body.append(svg)
        fy = y + 8 + gh + 26
        body.append(t(s.pad, fy, "arenas are a schematic of the", s.det, DIM))
        body.append(t(s.pad, fy + 17, "crossing, not simulator output", s.det, DIM))
        return finish(s, fy + 17 + 16, alt, "sw", body)

    if s.m:
        r = 84
        body = [title(s, 26, "LUMO · DRONE SWARM COORDINATION"),
                t(s.pad, 48, "60 drones swap sides through one crossing point", s.det, DIM)]
        cy = 76 + 22 + r + 9
        for k, gov in enumerate((False, True)):
            cx = round(s.pad + s.inner * (0.25 + 0.5 * k))
            body.append(t(cx, 84, names[gov], s.det, TEXT if gov else MUTE, anchor="middle", ls=1.6))
            body.append(arena(cx, cy, r, gov))
            body.append(tally(s, cx, cy + r + 44, gov, 28))
        y = cy + r + 44 + 24
        svg, gh = governor(s, s.pad, y, s.inner)
        body.append(svg)
        fy = y + gh + 26
        body.append(t(s.pad, fy, "arenas are a schematic, not simulator output", s.det, DIM))
        return finish(s, fy + 16, alt, "sw", body)

    r = 84
    h = 372
    p = head(s, h, alt, "sw")
    p.append(title(s, 28, "LUMO · DECENTRALISED DRONE SWARM COORDINATION"))
    p.append(t(s.pad, 50, "60 drones swap sides through a single crossing point: the worst case", s.det, DIM))
    cy = 178
    for k, gov in enumerate((False, True)):
        cx = s.pad + 104 + k * 232
        p.append(t(cx, 78, names[gov], s.det, TEXT if gov else MUTE, anchor="middle", ls=1.6))
        p.append(arena(cx, cy, r, gov))
        p.append(tally(s, cx, cy + r + 44, gov, 28))
    p.append(f'<path d="M{s.pad+204} {cy} h30" stroke="{AMBER}" stroke-opacity="0.5" stroke-width="1.6"/>'
             f'<path d="M{s.pad+233} {cy-4} l6 4 -6 4z" fill="{AMBER}" fill-opacity="0.7"/>')
    svg, gh = governor(s, s.pad + 452, 72, s.inner - 452)
    p.append(svg)
    p.append(t(s.pad, h - 16, "arenas are a schematic of the crossing, not simulator output", s.det, DIM))
    return "\n".join(p + tail(s, h)), h


# ------------------------------------------------------------------------ reach

REACH = [("Vault-OS", "the vault itself", AMBER, ["Windows · shipping", "bare-metal appliance"]),
         ("Vault clients", "Flutter · Electron", AMBER, ["Android", "iOS", "Windows", "macOS", "Linux"]),
         ("VEYMEER", "CUDA · WebGPU", ICE, ["NVIDIA", "AMD", "Intel", "Apple"]),
         ("STRADA", "IDE · Tauri", ICE, ["desktop"]),
         ("BME Nexus", "13 languages", "#5FB84B", ["web", "Android", "iOS", "desktop"])]
REACH_NOTE = "five operating systems · four GPU vendors · the web"


def reach(s):
    alt = ("Where the work runs: Vault-OS on Windows and as a bare-metal appliance; Vault clients on "
           "Android, iOS, Windows, macOS and Linux; VEYMEER on NVIDIA, AMD, Intel and Apple GPUs; "
           "STRADA on desktop; BME Nexus on web, Android, iOS and desktop.")
    if s.n:
        body, y = [title(s, 26, "WHERE IT RUNS")], 52
        for i, (name, sub, col, labs) in enumerate(REACH):
            svg, ch = chips(s, s.pad, y + 12, s.inner, labs, col, delay=0.4 + i * 0.15)
            body.append(f'<g>{fade(0.2 + i * 0.15)}{t(s.pad, y, name, s.title, TEXT)}'
                        f'{t(s.W-s.pad, y, sub, s.det, DIM, anchor="end")}</g>{svg}')
            y += 34 + ch + 16
        body.append(rule(s, y - 14))
        svg, fh = footnote(s, y + 6, wrap(REACH_NOTE, chars(s.inner - 18, s.det)))
        body.append(svg)
        return finish(s, y + 6 + fh, alt, "rc", body)

    rh = 44
    h = 48 + len(REACH) * rh + 46
    p = head(s, h, alt, "rc")
    p.append(title(s, 28, "WHERE IT RUNS"))
    for i, (name, sub, col, labs) in enumerate(REACH):
        y = 48 + i * rh
        if i:
            p.append(f'<line x1="{s.pad}" y1="{y}" x2="{s.W-s.pad}" y2="{y}" stroke="{GRID}" stroke-opacity="0.08"/>')
        p.append(f'<g>{fade(0.2 + i * 0.15)}{t(s.pad, y + 27, name, s.title, TEXT, weight=700)}'
                 f'{t(s.pad + 160, y + 27, sub, s.det, DIM)}</g>'
                 f'{chips(s, s.pad + 318, y + 10, s.inner - 318, labs, col, delay=0.4 + i * 0.15)[0]}')
    fy = h - 16
    p.append(rule(s, fy - 20))
    p.append(footnote(s, fy, [REACH_NOTE])[0])
    return "\n".join(p + tail(s, h)), h


# ---------------------------------------------------------------------- buttons
# Link buttons are drawn here rather than fetched from a badge service, for the
# same reason the stats are: nothing on this page depends on someone else's uptime.

BUTTONS = [("irongap", "IRONGAP", "iron-gap.com"), ("linkedin", "LINKEDIN", "taha-halakooei"),
           ("email", "EMAIL", "taha@iron-gap.com"), ("portfolio", "PORTFOLIO", "metronix.ir")]


def button(label, value):
    lw, vw = tw(label, 12.5, 1.2), tw(value, 13)
    w = round(14 + lw + 10 + vw + 12)
    h = 36
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{E(label.title())}: {E(value)}">'
            f'<defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{AMBER}" stop-opacity="0.22"/>'
            f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="c"><rect width="{w}" height="{h}" rx="8"/></clipPath></defs>'
            f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{BG}"/>'
            f'<rect width="4" height="{h}" fill="{AMBER}">{pulse(0.5, 1, 3.0)}</rect>'
            f'{t(14, 23, label, 12.5, AMBER, ls=1.2, weight=700)}'
            f'{t(14 + lw + 10, 23, value, 13, TEXT)}'
            f'<rect x="{-60}" y="0" width="60" height="{h}" fill="url(#b)"><animate attributeName="x" '
            f'values="-60;{w};{w}" keyTimes="0;0.45;1" dur="5s" repeatCount="indefinite"/></rect>'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="8" fill="none" stroke="{AMBER}" '
            f'stroke-opacity="0.4"/></g></svg>')


BUILDERS = {"header": header, "whoami": whoami, "vault": vault, "veymeer": veymeer,
            "engine": engine, "timeline": timeline, "depth": depth, "portfolio": portfolio,
            "swarm": swarm, "method": method, "bme": bme, "reach": reach}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        for suffix, mode in VARIANTS:
            s = S(mode)
            svg, h = fn(s)
            path = f"{OUT}/{name}{suffix}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"{path:34} {s.W}x{h}")
    for slug, label, value in BUTTONS:
        path = f"{OUT}/btn-{slug}.svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(button(label, value))
        print(path)
