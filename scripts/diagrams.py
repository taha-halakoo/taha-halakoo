#!/usr/bin/env python3
"""Build every hand-authored panel on the profile, in a wide and a narrow variant.

The content comes from the CV: two companies (IronGap in amber, VEYMEER in ice),
the measured VEYMEER figures, the Vault-OS architecture, the trajectory and the
project map. gen_stats.py draws the panels that come from live GitHub data and
borrows the primitives defined here.

An SVG rendered as <img> scales as a picture: the text does not reflow, so a
layout that is legible at 820px is unreadable at 293px (GitHub's README column
on a phone). Each diagram is therefore emitted twice and selected in markdown
with <picture><source media="(max-width: 600px)">.

Type scale is the constraint that drives everything: nothing renders below 12px
after the browser's scale factor, at either width.
"""
import datetime
import os

OUT = "assets"
BG, GRID, DIM, TEXT = "#07070A", "#FFC93C", "#5F6672", "#E4E6EB"
AMBER, GREEN, RED, MUTE = "#FFC93C", "#3FB950", "#F85149", "#8B929E"
PANEL, LINE = "#0E1116", "#8A7A4A"
ICE = "#4CC2FF"   # VEYMEER. Amber is IronGap; the pair separates under every CVD simulation.
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
ADV = 0.605       # monospace advance per em; every width estimate below rests on it


class S:
    """Per-variant geometry and type scale."""
    def __init__(self, narrow):
        self.n = narrow
        # 300 wide renders at ~0.98 in a phone's 293px README column, so a 13px
        # glyph stays 13px. At 340 the same glyph landed at 10.3px.
        self.W = 300 if narrow else 820
        self.pad = 14 if narrow else 28
        self.label = 13 if narrow else 13.5
        self.title = 15.5 if narrow else 17
        self.body = 13.5 if narrow else 13.5
        self.det = 13 if narrow else 12.5
        self.num = 28 if narrow else 38
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


_UID = ["x"]  # uid of the diagram currently being built, so tail() can match its defs


def head(s, h, alt, uid, extra_defs=""):
    _UID[0] = uid
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.W} {h}" width="{s.W}" '
        f'height="{h}" role="img" aria-label="{E(alt)}">',
        f'<defs><pattern id="g{uid}" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<path d="M26 0H0V26" fill="none" stroke="{GRID}" stroke-opacity="0.045"/></pattern>'
        f'{sweepdef(uid)}{hsweepdef(uid)}'
        f'<filter id="gl{uid}" x="-70%" y="-70%" width="240%" height="240%">'
        f'<feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/>'
        f'<feMergeNode in="SourceGraphic"/></feMerge></filter>{extra_defs}'
        f'<clipPath id="c{uid}"><rect width="{s.W}" height="{h}" rx="12"/></clipPath></defs>',
        f'<g clip-path="url(#c{uid})"><rect width="{s.W}" height="{h}" fill="{BG}"/>'
        f'<rect width="{s.W}" height="{h}" fill="url(#g{uid})"/>',
    ]


def tail(s, h, motion=True, corners=True):
    """Close the card, laying a slow travelling highlight over everything first.

    Every diagram gets this, so no panel is ever completely static.
    """
    out = []
    if motion:
        uid = _UID[0]
        band = 90 if s.n else 120
        out.append(f'<rect x="0" y="0" width="{band}" height="{h}" fill="url(#swh{uid})" '
                   f'pointer-events="none"><animate attributeName="x" values="{-band};{s.W}" '
                   f'dur="{6.5 if s.n else 7.5}s" repeatCount="indefinite"/></rect>')
    out.append(f'<rect x="0.5" y="0.5" width="{s.W-1}" height="{h-1}" rx="12" fill="none" '
               f'stroke="{GRID}" stroke-opacity="0.16"/>')
    # registration marks in the corners, the one piece of chrome every panel shares
    a, m = (9, 7) if s.n else (12, 9)
    W, H = s.W, h
    if not corners or s.n:   # at 300 wide the marks land on the section label
        out.append('</g></svg>')
        return out
    out.append(f'<path d="M{m} {m+a}V{m}h{a}M{W-m-a} {m}h{a}v{a}M{W-m} {H-m-a}v{a}h{-a}M{m+a} {H-m}h{-a}v{-a}" '
               f'fill="none" stroke="{GRID}" stroke-opacity="0.5" stroke-width="1.2"/></g></svg>')
    return out


def sect(s, y, t, colour=None):
    return (f'<text x="{s.pad}" y="{y}" font-family="{MONO}" font-size="{s.label}" '
            f'fill="{colour or AMBER}" letter-spacing="2.2">{E(t)}</text>')


def fade(delay, dur=0.45):
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" '
            f'dur="{dur}s" fill="freeze"/>')


# ------------------------------------------------------------------ animation
# Content fades in once and stays (fill="freeze"). Everything below is motion
# layered over it, looping forever, and never hides what it passes across.

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
    return (f'<circle r="{r}" fill="{c}">'
            f'<animateMotion path="{path_d}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.12;0.85;1" '
            f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>')


def burst(cx, cy, r1=20, dur=2.6, begin=0.0, colour=None):
    """An expanding ring, like something landing."""
    c = colour or AMBER
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="none" stroke="{c}" stroke-width="2">'
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
    return (f'<clipPath id="tc{uid}"><rect x="{x}" y="{y}" width="0" height="{h}">'
            f'<animate attributeName="width" from="0" to="{w}" dur="{dur}s" '
            f'begin="{begin}s" fill="freeze"/></rect></clipPath>')


def caret(x, y, h=15, colour=None, begin=0.0):
    c = colour or GREEN
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="9" height="{h}" fill="{c}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="0.1s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" '
            f'begin="{begin+0.2}s" repeatCount="indefinite"/></rect>')


def card(s, x, y, w, h, stroke=GRID, op=0.28, fill=PANEL):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="7" '
            f'fill="{fill}" stroke="{stroke}" stroke-opacity="{op}"/>')


def t(x, y, txt, size, fill=TEXT, anchor="start", ls=None, weight=None):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    w = f' font-weight="{weight}"' if weight else ""
    sp = ' xml:space="preserve"' if "  " in txt else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}"'
            f' fill="{fill}"{a}{l}{w}{sp}>{E(txt)}</text>')


def name_text(x, y, txt, size, length):
    """The one run set in a proportional face. textLength pins its width, so the
    layout does not depend on which system font the viewer ends up with."""
    return (f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="{size}" font-weight="800" '
            f'fill="#F4F4F6" textLength="{length}" lengthAdjust="spacingAndGlyphs">{E(txt)}</text>')


def chips(s, x, y, maxw, labels, colour, hot=None):
    """Flow labels as pills, wrapping at maxw. Returns (svg, height used)."""
    size, ch, gap, padx = s.det, 24, 6, 9
    cx, cy, out = x, y, []
    for lab in labels:
        w = tw(lab, size) + 2 * padx
        if cx > x and cx + w > x + maxw + 0.5:
            cx, cy = x, cy + ch + gap
        c = (hot or {}).get(lab)
        out.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{w:.1f}" height="{ch}" rx="12" '
                   f'fill="{c or colour}" fill-opacity="{0.16 if c else 0.07}" '
                   f'stroke="{c or colour}" stroke-opacity="{0.9 if c else 0.38}"/>')
        out.append(t(cx + padx, cy + 16.5, lab, size, "#F2F2F5" if c else TEXT))
        cx += w + gap
    return "".join(out), cy + ch - y


# ----------------------------------------------------------------------- header

def emblem(cx, cy):
    """Vault core in amber with inference tokens orbiting it in ice."""
    g = [f'<circle cx="{cx}" cy="{cy}" r="74" fill="none" stroke="{AMBER}" stroke-opacity="0.35" '
         f'stroke-width="5" stroke-dasharray="1 8.69"/>',
         f'<circle cx="{cx}" cy="{cy}" r="62" fill="none" stroke="{AMBER}" stroke-opacity="0.55" '
         f'stroke-width="1.3" stroke-dasharray="26 10 4 10">'
         f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" '
         f'to="360 {cx} {cy}" dur="38s" repeatCount="indefinite"/></circle>',
         f'<circle cx="{cx}" cy="{cy}" r="46" fill="none" stroke="{ICE}" stroke-opacity="0.45" '
         f'stroke-width="1.3" stroke-dasharray="3 5">'
         f'<animateTransform attributeName="transform" type="rotate" from="360 {cx} {cy}" '
         f'to="0 {cx} {cy}" dur="26s" repeatCount="indefinite"/></circle>']
    for k, a in enumerate((0, 120, 240)):
        g.append(f'<circle cx="{cx+46}" cy="{cy}" r="{3.2 - k * 0.5:.1f}" fill="{ICE}">'
                 f'<animateTransform attributeName="transform" type="rotate" from="{a} {cx} {cy}" '
                 f'to="{a+360} {cx} {cy}" dur="3.4s" repeatCount="indefinite"/></circle>')
    g.append(f'<circle cx="{cx+62}" cy="{cy}" r="3" fill="{AMBER}">'
             f'<animateTransform attributeName="transform" type="rotate" from="200 {cx} {cy}" '
             f'to="-160 {cx} {cy}" dur="11s" repeatCount="indefinite"/></circle>')
    g.append(f'<rect x="{cx-19}" y="{cy-19}" width="38" height="38" rx="3" fill="{PANEL}" '
             f'stroke="{AMBER}" stroke-width="2" transform="rotate(45 {cx} {cy})"/>')
    g.append(f'<rect x="{cx-7}" y="{cy-7}" width="14" height="14" rx="1.5" fill="{AMBER}">'
             f'{pulse(0.35, 1, 2.6)}</rect>')
    g.append(burst(cx, cy, 44, 4.2, 0.6, AMBER))
    return "".join(g)


def lockup(s, x, y, w, h, brand, delay):
    """One company cell: wordmark, what it is, one live line."""
    col = AMBER if brand == "irongap" else ICE
    g = [f'<g opacity="0">{fade(delay)}', card(s, x, y, w, h, col, 0.4),
         f'<rect x="{x:.1f}" y="{y:.1f}" width="4" height="{h}" rx="2" fill="{col}">'
         f'{pulse(0.45, 1, 3.0, delay)}</rect>']
    tx = x + 18
    if brand == "irongap":
        g.append(t(tx, y + 27, "IRONGAP", 17, AMBER, weight=700, ls=0.6))
        if not s.n:
            g.append(t(tx + tw("IRONGAP", 17, 0.6), y + 27, "_TECHNOLOGIES", 17, MUTE, weight=700, ls=0.6))
        what = "air-gapped AI, zero-trust" if s.n else "air-gapped AI for zero-trust environments"
        live = ("VAULT-OS", "SHIPPING" if s.n else "SHIPPING · WINDOWS")
    else:
        g.append(t(tx, y + 27, "VEYMEER", 17, "#F2F2F5", weight=700, ls=6.5))
        what = "from-scratch LLM inference" if s.n else "from-scratch LLM inference engine"
        live = ("400–500 TOK/S", "RTX 3050" if s.n else "RTX 3050 LAPTOP GPU")
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
    if s.n:
        ch = 92
        h = 140 + 2 * (ch + 10) + 6
        p = head(s, h, alt, "hd")
        p.append(sweep("hd", s.W, h, band=54, dur=5.5))
        p.append(sect(s, 30, "FOUNDER & CHIEF ARCHITECT"))
        p.append(name_text(s.pad, 74, "Taha Halakooei", 36, 265))
        p.append(t(s.pad, 100, "secure systems · AI infrastructure", s.det, MUTE))
        p.append(t(s.pad, 118, "full-stack engineering · Istanbul", s.det, MUTE))
        p.append(lockup(s, s.pad, 136, s.inner, ch, "irongap", 0.4))
        p.append(lockup(s, s.pad, 136 + ch + 10, s.inner, ch, "veymeer", 0.6))
        return "\n".join(p + tail(s, h)), h

    h = 310
    p = head(s, h, alt, "hd")
    p.append(sweep("hd", s.W, h, band=64, dur=6.0))
    p.append(sect(s, 42, "FOUNDER & CHIEF ARCHITECT  ·  ISTANBUL, TÜRKİYE"))
    p.append(name_text(s.pad, 106, "Taha Halakooei", 62, 456))
    tag = "secure systems · AI infrastructure · full-stack engineering"
    w_ = tw(tag, 15)
    p.append(f'<defs>{typeclip("hd", s.pad, 124, w_, 22, dur=2.0, begin=0.4)}</defs>')
    p.append(f'<g clip-path="url(#tchd)">{t(s.pad, 139, tag, 15, TEXT)}</g>')
    p.append(caret(s.pad + w_ + 4, 126, 16, AMBER, begin=2.4))
    p.append(f'<g opacity="0">{fade(2.5)}'
             f'{t(s.pad, 163, "from TPM-bound boot chains and hand-written CUDA kernels", s.det, DIM)}'
             f'{t(s.pad, 180, "to cross-platform Flutter and React applications", s.det, DIM)}</g>')
    p.append(f'<g opacity="0">{fade(0.3, 0.9)}<g transform="translate(-65.6 -8.4) scale(1.1)">{emblem(696, 104)}</g></g>')
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
    lh = 19 if s.n else 21
    step = 0.45
    rows = [(cmd, narrow if s.n else wide, col) for cmd, wide, narrow, col in WHO]
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
        g = [f'<g opacity="0">{fade(0.25 + i * step)}']
        g.append(t(s.pad, y, "›", s.body, GREEN))
        g.append(f'<g clip-path="url(#tcw{i})">{t(s.pad + 16, y, cmd, s.body, TEXT)}</g>')
        for j, ln in enumerate(lines):
            g.append(t(s.pad, y + lh * (j + 1), ln, s.body, col))
        g.append('</g>')
        clips.append(typeclip(f"w{i}", s.pad + 16, y - 14, tw(cmd, s.body), 18, dur=0.4,
                              begin=0.25 + i * step))
        p.append("".join(g))
        y += lh * (len(lines) + 1) + 9
    p.insert(1, f'<defs>{"".join(clips)}</defs>')
    end = 0.25 + len(rows) * step + 0.2
    p.append(f'<text x="{s.pad}" y="{y}" font-family="{MONO}" font-size="{s.body}" '
             f'fill="{GREEN}" opacity="0">{fade(end, 0.2)}›</text>')
    p.append(f'<rect x="{s.pad+16}" y="{y-12}" width="9" height="15" fill="{GREEN}" opacity="0">'
             f'{fade(end, 0.2)}<animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" '
             f'begin="{end+0.2:.2f}s" repeatCount="indefinite"/></rect>')
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
    p.append(sect(s, 26 if s.n else 28, "TRAJECTORY"))
    yl = 46 if s.n else 58
    for yr in range(T0.year, now.year + 1):
        x = X(D(yr, 1, 1))
        if x1 - x < 34:
            continue
        p.append(f'<line x1="{x:.1f}" y1="{yl+6}" x2="{x:.1f}" y2="{h-(30 if s.n else 36)}" '
                 f'stroke="{GRID}" stroke-opacity="0.09"/>')
        p.append(t(x + (0 if s.n else 5), yl, str(yr), s.det, DIM))
    p.append(t(x1, yl, "NOW", s.det, TEXT, anchor="end", ls=1.2))
    p.append(f'<line x1="{x1:.1f}" y1="{yl+6}" x2="{x1:.1f}" y2="{h-(30 if s.n else 36)}" '
             f'stroke="{TEXT}" stroke-opacity="0.35" stroke-dasharray="2 4"/>')
    for i, (name, role, start, end, lab, col) in enumerate(TRACKS):
        y = top + i * rh
        xs, xe = X(start or T0), X(end or now)
        by = y + (46 if s.n else 12)
        g = [f'<g opacity="0">{fade(0.2 + i * 0.22)}']
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
        p.append(f'<rect x="{xs:.1f}" y="{by}" width="0" height="14" rx="3" fill="{fill}">'
                 f'<animate attributeName="width" from="0" to="{xe-xs:.1f}" dur="0.9s" '
                 f'begin="{0.3+i*0.22:.2f}s" fill="freeze"/></rect>')
        if end is None:
            p.append(f'<g opacity="0">{fade(1.2 + i * 0.22)}'
                     f'<circle cx="{x1:.1f}" cy="{by+7}" r="4.5" fill="{col}" stroke="{BG}" stroke-width="2">'
                     f'{pulse(0.4, 1, 2.4, i * 0.3)}</circle>'
                     f'{burst(x1, by + 7, 13, 3.0, 1.4 + i * 0.5, col)}</g>')
    fy = h - 14
    p.append(f'<circle cx="{s.pad+5}" cy="{fy-4}" r="3.6" fill="{GREEN}">{pulse(0.3, 1, 2.2)}</circle>')
    p.append(t(s.pad + 18, fy, f"{live} tracks running concurrently" if not s.n
               else f"{live} tracks running at once", s.det, MUTE))
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
    p.append(sect(s, 28, "THE STACK I WORK ACROSS"))
    for i, (name, dl, tl_, col) in enumerate(laid):
        y = 46 + i * (rh + 8)
        g = [f'<g opacity="0">{fade(0.2 + (len(laid)-i) * 0.12)}',
             card(s, s.pad, y, s.inner, rh, col, 0.32),
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
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- method

STEPS = [("1 · REPRODUCE", "make it happen on demand", "kill power at 18 of 22GB", GRID),
         ("2 · ISOLATE", "cut until only the failure is left", "unpack, or the resume index?", GRID),
         ("3 · FALSIFY", "try hard to prove the diagnosis wrong", "what else explains this?", AMBER),
         ("4 · FIX", "smallest change that holds", "not the most clever one", GRID),
         ("5 · VERIFY", "add the check that would have caught it", "shutdown now verifies", GREEN)]


def method(s):
    if s.n:
        budget = chars(s.inner - 28, s.det)
        laid = [(n, wrap(d, budget), wrap(e, budget), c) for n, d, e, c in STEPS]
        dmax = max(len(d) for _, d, _, _ in laid)
        emax = max(len(e) for _, _, e, _ in laid)
        rh = 26 + dmax * 17 + 6 + emax * 17
        h = 46 + len(laid) * (rh + 12) + 12
        p = head(s, h, "How I work a failure", "mt")
        p.append(sect(s, 28, "HOW I WORK A FAILURE"))
        for i, (name, dl, el, col) in enumerate(laid):
            y = 46 + i * (rh + 12)
            hl = AMBER if col == AMBER else (GREEN if col == GREEN else TEXT)
            g = [f'<g opacity="0">{fade(0.2 + i * 0.2)}', card(s, s.pad, y, s.inner, rh, col, 0.34),
                 t(s.pad + 14, y + 21, name, s.title, hl)]
            for j, ln in enumerate(dl):
                g.append(t(s.pad + 14, y + 40 + j * 17, ln, s.det, DIM))
            for j, ln in enumerate(el):
                g.append(t(s.pad + 14, y + 40 + dmax * 17 + 6 + j * 17, ln, s.det, LINE))
            g.append('</g>')
            p.append("".join(g))
            if i < len(laid) - 1:
                p.append(f'<path d="M{s.pad+20} {y+rh} v12" stroke="{AMBER}" stroke-opacity="0.4" stroke-width="1.5"/>')
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
    p.append(sect(s, 28, "HOW I WORK A FAILURE"))
    for i, (name, dl, el, col) in enumerate(laid):
        x = s.pad + i * (bw + 12)
        hl = AMBER if col == AMBER else (GREEN if col == GREEN else TEXT)
        g = [f'<g opacity="0">{fade(0.2 + i * 0.22)}', card(s, x, top, bw, bh, col, 0.34),
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
    p.append(travel(f"M{s.pad+bw/2:.0f} {top} H{s.pad+4*(bw+12)+bw/2:.0f}", 6.5, 1.4, 4.0, AMBER))
    p.append(burst(s.pad + 2 * (bw + 12) + bw / 2, top, 18, 3.2, 2.6, AMBER))
    p.append(travel(f"M{s.pad+bw*2+24+bw/2:.0f} {top+bh:.0f} V{top+bh+20:.0f} "
                    f"H{s.pad+bw/2:.0f} V{top+bh:.0f}", 4.0, 3.4, 3.4, AMBER))
    ry = top + bh + 20
    p.append(f'<path d="M{s.pad+bw*2+24+bw/2} {top+bh} v20 H{s.pad+bw/2} v-20" fill="none" '
             f'stroke="{AMBER}" stroke-opacity="0.35" stroke-width="1.4" stroke-dasharray="5 4"/>')
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
    if s.n:
        ph = 58
        h = 52 + len(PAIRS) * (ph * 2 + 26) + 12
        p = head(s, h, "How biomedical engineering maps onto secure systems work", "bm")
        p.append(sect(s, 26, "THE DEGREE IS NOT A DETOUR"))
        y = 46
        for i, (left, right) in enumerate(PAIRS):
            p.append(f'<g opacity="0">{fade(0.2 + i * 0.22)}'
                     f'{card(s, s.pad, y, s.inner, ph, GREEN, 0.3)}'
                     f'{t(s.pad+12, y+23, left[0], s.det, TEXT)}'
                     f'{t(s.pad+12, y+41, left[1], s.det, TEXT)}'
                     f'<path d="M{s.W/2} {y+ph+3} v13" stroke="{AMBER}" stroke-opacity="0.5" stroke-width="1.5"/>'
                     f'{card(s, s.pad, y+ph+20, s.inner, ph, AMBER, 0.3)}'
                     f'{t(s.pad+12, y+ph+43, right[0], s.det, TEXT)}'
                     f'{t(s.pad+12, y+ph+61, right[1], s.det, TEXT)}</g>')
            p.append(travel(f"M{s.W/2:.0f} {y+ph+3} v13", 2.4, i * 0.55, 3.2, AMBER))
            y += ph * 2 + 26
        return "\n".join(p + tail(s, h)), h

    ph, gap = 56, 14
    h = 76 + len(PAIRS) * (ph + gap) + 8
    p = head(s, h, "How biomedical engineering training maps onto secure systems work", "bm")
    p.append(sect(s, 28, "WHY THE BIOMEDICAL DEGREE IS NOT A DETOUR"))
    cw = (s.inner - 90) / 2
    p.append(t(s.pad, 56, "WHAT THE DEGREE TEACHES", s.det, GREEN, ls=1.6))
    p.append(t(s.pad + cw + 90, 56, "WHAT IT BECAME IN MY WORK", s.det, AMBER, ls=1.6))
    for i, (left, right) in enumerate(PAIRS):
        y = 68 + i * (ph + gap)
        rx = s.pad + cw + 90
        p.append(f'<g opacity="0">{fade(0.2 + i * 0.22)}'
                 f'{card(s, s.pad, y, cw, ph, GREEN, 0.3)}'
                 f'{t(s.pad+13, y+23, left[0], s.body, TEXT)}{t(s.pad+13, y+42, left[1], s.body, TEXT)}'
                 f'<path d="M{s.pad+cw+10} {y+ph/2} h68" stroke="{AMBER}" stroke-opacity="0.4" stroke-width="1.5"/>'
                 f'<path d="M{s.pad+cw+72} {y+ph/2-4} l6 4 -6 4z" fill="{AMBER}" fill-opacity="0.6"/>'
                 f'{card(s, rx, y, cw, ph, AMBER, 0.3)}'
                 f'{t(rx+13, y+23, right[0], s.body, TEXT)}{t(rx+13, y+42, right[1], s.body, TEXT)}</g>')
        p.append(f'<circle r="3.2" fill="{AMBER}"><animate attributeName="cx" values="{s.pad+cw+10};{s.pad+cw+72}" '
                 f'dur="2.4s" begin="{i*0.6}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="cy" values="{y+ph/2};{y+ph/2}" dur="2.4s" begin="{i*0.6}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" dur="2.4s" begin="{i*0.6}s" repeatCount="indefinite"/></circle>')
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
    if s.n:
        budget = chars(s.inner - 24, s.det)
        h = 44
        for _, _, items in DOMAINS:
            h += 40 + sum(30 + len(wrap(d, budget)) * 17 + 8 for _, d, _ in items)
        h += 2
        p = head(s, h, alt, "pf")
        p.append(sect(s, 26, "WHAT I HAVE BUILT"))
        y = 48
        k = 0
        for name, col, items in DOMAINS:
            p.append(t(s.pad, y, name, s.det, col, ls=1.5))
            p.append(f'<line x1="{s.pad}" y1="{y+7}" x2="{s.W-s.pad}" y2="{y+7}" stroke="{col}" stroke-opacity="0.3"/>')
            y += 20
            for nm, desc, tech in items:
                dl = wrap(desc, budget)
                ch = 30 + len(dl) * 17
                g = [f'<g opacity="0">{fade(0.15 + k * 0.07)}', card(s, s.pad, y, s.inner, ch, col, 0.26),
                     t(s.pad + 12, y + 21, nm, s.title, TEXT)]
                for j, ln in enumerate(dl):
                    g.append(t(s.pad + 12, y + 39 + j * 17, ln, s.det, DIM))
                g.append('</g>')
                p.append("".join(g))
                y += ch + 8
                k += 1
            y += 20
        return "\n".join(p + tail(s, h)), h

    cw = (s.inner - 3 * 12) / 4
    budget = chars(cw - 24, s.det)
    laid = [(nm, wrap(d, budget), wrap(tc, budget), col)
            for _, col, items in DOMAINS for nm, d, tc in items]
    dmax = max(len(d) for _, d, _, _ in laid)
    tmax = max(len(tc) for _, _, tc, _ in laid)
    ch = 26 + dmax * 15 + 8 + tmax * 15 + 4
    rows = max(len(i) for _, _, i in DOMAINS)
    h = 78 + rows * (ch + 8) + 14
    p = head(s, h, alt, "pf")
    p.append(sect(s, 28, "WHAT I HAVE BUILT"))
    k = 0
    for c, (name, col, items) in enumerate(DOMAINS):
        x = s.pad + c * (cw + 12)
        p.append(t(x, 58, name, s.det, col, ls=1.3))
        p.append(f'<line x1="{x}" y1="66" x2="{x+cw}" y2="66" stroke="{col}" stroke-opacity="0.3"/>')
        for r, (nm, desc, tech) in enumerate(items):
            y = 80 + r * (ch + 8)
            dl, tl_ = wrap(desc, budget), wrap(tech, budget)
            g = [f'<g opacity="0">{fade(0.15 + k * 0.07)}', card(s, x, y, cw, ch, col, 0.26),
                 t(x + 12, y + 21, nm, s.body, TEXT, weight=700)]
            for j, ln in enumerate(dl):
                g.append(t(x + 12, y + 39 + j * 15, ln, s.det, DIM))
            for j, ln in enumerate(tl_):
                g.append(t(x + 12, y + 39 + dmax * 15 + 8 + j * 15, ln, s.det, LINE))
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


def vault(s):
    alt = ("Vault-OS architecture inside the air gap: clients on the local network, the Vault-OS core, "
           "a pluggable inference layer, a TPM-bound encrypted enclave holding PostgreSQL and pgvector, "
           "the fail-deadly trust root, and a Rust appliance operating system underneath.")
    hot = {"VEYMEER": ICE}
    if s.n:
        x, w = s.pad, s.inner
        laid = []
        for name, cap, col, labs in VAULT:
            _, chh = chips(s, 0, 0, w - 24, labs, col, hot)
            laid.append((name, cap, col, labs, 52 + chh + 12))
        h = 46 + sum(l[4] + 10 for l in laid) + 34
        p = head(s, h, alt, "vt")
        p.append(sect(s, 26, "VAULT-OS · AIR-GAPPED"))
        y = 44
        for i, (name, cap, col, labs, lh) in enumerate(laid):
            svg, _ = chips(s, x + 12, y + 52, w - 24, labs, col, hot)
            p.append(f'<g opacity="0">{fade(0.2 + i * 0.16)}{card(s, x, y, w, lh, col, 0.3)}'
                     f'<rect x="{x}" y="{y}" width="4" height="{lh}" rx="2" fill="{col}">'
                     f'{pulse(0.45, 1, 3.0, i * 0.35)}</rect>'
                     f'{t(x+12, y+22, name, s.title, TEXT)}{t(x+12, y+40, cap, s.det, DIM)}{svg}</g>')
            y += lh + 10
        p.append(f'<circle cx="{s.pad+5}" cy="{y+12}" r="3.6" fill="{GREEN}">{pulse(0.3, 1, 2.2)}</circle>')
        p.append(t(s.pad + 18, y + 16, "offline by design · no Docker", s.det, MUTE))
        return "\n".join(p + tail(s, h)), h

    x, w = s.pad + 14, s.inner - 28
    cx0 = x + 196
    laid = []
    for name, cap, col, labs in VAULT:
        _, chh = chips(s, 0, 0, w - 196 - 12, labs, col, hot)
        laid.append((name, cap, col, labs, max(52, chh + 24)))
    top = 66
    body = sum(l[4] + 12 for l in laid) - 12
    h = top + body + 14 + 44
    p = head(s, h, alt, "vt")
    p.append(sect(s, 28, "VAULT-OS · THE AIR-GAPPED AI KNOWLEDGE VAULT"))
    # the perimeter: everything the product needs is drawn inside it
    p.append(f'<rect x="{s.pad}" y="52" width="{s.inner}" height="{body+28}" rx="10" fill="none" '
             f'stroke="{AMBER}" stroke-opacity="0.5" stroke-width="1.4" stroke-dasharray="7 6">'
             f'<animate attributeName="stroke-dashoffset" from="0" to="-52" dur="6s" repeatCount="indefinite"/></rect>')
    tag = "AIR-GAPPED PERIMETER"
    tgw = tw(tag, s.det, 1.4)
    p.append(f'<rect x="{s.W-s.pad-24-tgw-8:.1f}" y="44" width="{tgw+16:.1f}" height="16" fill="{BG}"/>')
    p.append(t(s.W - s.pad - 24, 57, tag, s.det, AMBER, anchor="end", ls=1.4))
    y = top
    for i, (name, cap, col, labs, lh) in enumerate(laid):
        svg, chh = chips(s, cx0, y + (lh - (lh - 24 if lh > 52 else 24)) / 2, w - 196 - 12, labs, col, hot)
        p.append(f'<g opacity="0">{fade(0.2 + i * 0.16)}{card(s, x, y, w, lh, col, 0.3)}'
                 f'<rect x="{x}" y="{y}" width="4" height="{lh}" rx="2" fill="{col}">'
                 f'{pulse(0.45, 1, 3.0, i * 0.35)}</rect>'
                 f'{t(x+16, y+23, name, s.body, TEXT, weight=700)}{t(x+16, y+40, cap, s.det, DIM)}{svg}</g>')
        if i < len(laid) - 1:
            p.append(f'<path d="M{x+2} {y+lh} v12" stroke="{col}" stroke-opacity="0.6" stroke-width="2"/>')
        y += lh + 12
    p.append(travel(f"M{x+2} {top} V{top+body}", 5.5, 1.6, 3.2, "#F2F2F5"))
    fy = h - 16
    p.append(f'<circle cx="{s.pad+5}" cy="{fy-4}" r="3.6" fill="{GREEN}">{pulse(0.3, 1, 2.2)}</circle>')
    p.append(t(s.pad + 18, fy, "offline by design · runs fully native, without Docker · shipping on Windows",
               s.det, MUTE))
    return "\n".join(p + tail(s, h)), h


# ---------------------------------------------------------------------- veymeer
# Every figure below is one the engine was measured at. Nothing is derived
# except 38×, which is 1.9 / 0.05.

TILES_V = [("400–500", "TOK/S · CODE EDIT", "TOK/S"), ("12–15×", "VS STD DECODING", "FASTER"),
           ("0.05 s", "TO FIRST TOKEN", "FIRST TOKEN"), ("0", "TOKENS DIFFERENT", "OUTPUT DIFF")]
RACE = 13.5      # midpoint of the measured 12–15× range
CYC = 9.0        # seconds per loop
GREY = "#5F6672"


def stat(s, x, y, w, h, val, label, colour, delay, size):
    return (f'<g opacity="0">{fade(delay, 0.5)}{card(s, x, y, w, h, GRID, 0.16)}'
            f'<rect x="{x+14:.1f}" y="{y+12:.1f}" width="22" height="3" rx="1.5" fill="{colour}"/>'
            f'{t(x+14, y+h-29, val, size, "#F2F2F5", weight=700)}'
            f'{t(x+14, y+h-10, label, s.det, DIM, ls=0 if s.n else 1.3)}</g>')


def lane(x, y, w, colour, ratio, uid):
    """A track that fills with tokens; `ratio` is how many times faster than 1×."""
    full = 0.9 / ratio
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="16" rx="3" fill="{PANEL}" '
            f'stroke="{GRID}" stroke-opacity="0.12"/>'
            f'<clipPath id="ln{uid}"><rect x="{x:.1f}" y="{y}" width="0" height="16">'
            f'<animate attributeName="width" values="0;{w:.1f};{w:.1f}" keyTimes="0;{full:.4f};1" '
            f'dur="{CYC}s" repeatCount="indefinite"/></rect></clipPath>'
            f'<line x1="{x+3:.1f}" y1="{y+8}" x2="{x+w-3:.1f}" y2="{y+8}" stroke="{colour}" '
            f'stroke-width="8" stroke-dasharray="7 3" clip-path="url(#ln{uid})"/>')


def bar(x, y, w, colour, delay):
    return (f'<rect x="{x:.1f}" y="{y}" width="0" height="14" rx="3" fill="{colour}">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" dur="0.8s" begin="{delay}s" '
            f'fill="freeze"/></rect>')


def veymeer(s):
    alt = ("VEYMEER measured on an RTX 3050 laptop GPU running Qwen2.5-7B: 400 to 500 tokens per second "
           "on code editing, 12 to 15 times faster than standard decoding, time to first token cut from "
           "1.9 seconds to 0.05 seconds by prompt caching, and output identical to standard decoding.")
    if s.n:
        tw_, th = (s.inner - 10) / 2, 76
        h = 663
        p = head(s, h, alt, "vm")
        p.append(sect(s, 26, "VEYMEER · MEASURED", ICE))
        p.append(t(s.pad, 46, "Qwen2.5-7B · RTX 3050 laptop GPU", s.det, DIM))
        p.append(t(s.pad, 63, "lossless speculative decoding", s.det, DIM))
        for i, (v, _, lab) in enumerate(TILES_V):
            p.append(stat(s, s.pad + (i % 2) * (tw_ + 10), 76 + (i // 2) * (th + 10), tw_, th,
                          v, lab, ICE, 0.1 * i, 25))
        y = 76 + 2 * (th + 10) + 24
        p.append(t(s.pad, y, "DECODE SPEED · TO SCALE", s.det, DIM, ls=1.4))
        for k, (lab, val, col, ratio) in enumerate([("standard decoding", "1×", GREY, 1),
                                                    ("VEYMEER", "12–15×", ICE, RACE)]):
            ly = y + 26 + k * 50
            p.append(t(s.pad, ly, lab, s.det, MUTE if k == 0 else TEXT))
            p.append(t(s.W - s.pad, ly, val, s.det, TEXT, anchor="end"))
            p.append(lane(s.pad, ly + 9, s.inner, col, ratio, f"n{k}"))
        y += 26 + 2 * 50 + 4
        for j, ln in enumerate(["same model, same GPU, same output", "bars fill at 1× and 13.5×, the",
                                "midpoint of the measured range"]):
            p.append(t(s.pad, y + j * 17, ln, s.det, DIM))
        y += 3 * 17 + 20
        p.append(t(s.pad, y, "TIME TO FIRST TOKEN", s.det, DIM, ls=1.4))
        for k, (lab, val, col, frac) in enumerate([("no cache", "1.9 s", GREY, 1.0),
                                                   ("prompt cache", "0.05 s · 38× sooner", ICE, 0.05 / 1.9)]):
            ly = y + 26 + k * 46
            p.append(t(s.pad, ly, lab, s.det, MUTE if k == 0 else TEXT))
            p.append(t(s.W - s.pad, ly, val, s.det, TEXT, anchor="end"))
            p.append(bar(s.pad, ly + 9, s.inner * frac, col, 0.6 + k * 0.2))
        y += 26 + 2 * 46 + 12
        p.append(f'<line x1="{s.pad}" y1="{y-14}" x2="{s.W-s.pad}" y2="{y-14}" stroke="{GRID}" stroke-opacity="0.12"/>')
        p.append(f'<circle cx="{s.pad+5}" cy="{y+4}" r="3.6" fill="{GREEN}">{pulse(0.3, 1, 2.2)}</circle>')
        for j, ln in enumerate(["beats llama.cpp on a public", "26-prompt benchmark, with output",
                                "identical to standard decoding"]):
            p.append(t(s.pad + 18, y + 8 + j * 17, ln, s.det, MUTE))
        assert y + 8 + 2 * 17 + 18 == h
        return "\n".join(p + tail(s, h)), h

    tw_, th = (s.inner - 3 * 12) / 4, 84
    h = 404
    p = head(s, h, alt, "vm")
    p.append(sect(s, 28, "VEYMEER · MEASURED", ICE))
    p.append(t(s.W - s.pad, 28, "Qwen2.5-7B · RTX 3050 laptop GPU · lossless speculative decoding",
               s.det, DIM, anchor="end"))
    for i, (v, lab, _) in enumerate(TILES_V):
        p.append(stat(s, s.pad + i * (tw_ + 12), 46, tw_, th, v, lab, ICE, 0.12 * i, 34))
    lx, tx = s.pad + 196, s.pad + 212
    p.append(t(s.pad, 166, "DECODE SPEED · ANIMATION TO SCALE", s.det, DIM, ls=1.6))
    for k, (lab, val, col, ratio) in enumerate([("standard decoding", "1×", GREY, 1),
                                                ("VEYMEER", "12–15×", ICE, RACE)]):
        y = 180 + k * 30
        p.append(t(s.pad, y + 13, lab, s.det, MUTE if k == 0 else TEXT))
        p.append(t(lx, y + 13, val, s.det, TEXT, anchor="end"))
        p.append(lane(tx, y, s.W - s.pad - tx, col, ratio, f"w{k}"))
    done = CYC * 0.9 / RACE
    p.append(f'<circle cx="{s.W-s.pad-6}" cy="218" r="3" fill="none" stroke="{ICE}" stroke-width="2" opacity="0">'
             f'<animate attributeName="r" values="3;3;20;20" keyTimes="0;{done/CYC:.4f};{done/CYC+0.12:.4f};1" '
             f'dur="{CYC}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;0.9;0;0" keyTimes="0;{done/CYC:.4f};{done/CYC+0.12:.4f};1" '
             f'dur="{CYC}s" repeatCount="indefinite"/></circle>')
    p.append(t(s.pad, 254, "same model · same GPU · same output — bars fill at 1× and 13.5×, the midpoint",
               s.det, DIM))
    p.append(t(s.pad, 292, "TIME TO FIRST TOKEN · PROMPT CACHING", s.det, DIM, ls=1.6))
    scale = 420
    for k, (lab, val, col, frac) in enumerate([("no cache", "1.9 s", GREY, 1.0),
                                               ("prompt cache", "0.05 s · 38× sooner", ICE, 0.05 / 1.9)]):
        y = 304 + k * 26
        p.append(t(s.pad, y + 12, lab, s.det, MUTE if k == 0 else TEXT))
        p.append(bar(tx, y, scale * frac, col, 0.6 + k * 0.2))
        p.append(f'<g opacity="0">{fade(1.2 + k * 0.2)}{t(tx + scale * frac + 9, y + 12, val, s.det, TEXT)}</g>')
    p.append(f'<line x1="{s.pad}" y1="364" x2="{s.W-s.pad}" y2="364" stroke="{GRID}" stroke-opacity="0.12"/>')
    p.append(f'<circle cx="{s.pad+5}" cy="382" r="3.6" fill="{GREEN}">{pulse(0.3, 1, 2.2)}</circle>')
    p.append(t(s.pad + 18, 386, "beats llama.cpp on a public 26-prompt benchmark, with output identical to "
               "standard decoding", s.det, MUTE))
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- engine

STAGES = [("GGUF", "model loader"), ("BPE", "tokenizer"),
          ("KERNELS", "runtime-built CUDA via NVRTC"), ("KV CACHE", "attention state"),
          ("SCHEDULER", "decode scheduling"), ("API", "OpenAI compatible")]
BACKENDS = [("CUDA", "NVIDIA"), ("WebGPU", "AMD · Intel · Apple")]
CAPS = ["lossless speculative decoding", "prompt caching", "weight streaming beyond VRAM",
        "structured output", "tool calling", "multi-machine sharding over mTLS"]
STRADA = ["Tauri", "VS Code extensions", "integrated debugging", "autonomous coding agent"]


def engine(s):
    alt = ("VEYMEER engine, built from first principles in Rust, CUDA and Python: GGUF loader, BPE "
           "tokenizer, CUDA kernels compiled at runtime via NVRTC, KV cache, scheduler and an "
           "OpenAI-compatible API, with CUDA and WebGPU backends. STRADA, a desktop IDE, is built on it.")
    if s.n:
        bh = 50
        _, caph = chips(s, 0, 0, s.inner, CAPS, ICE)
        _, sth = chips(s, 0, 0, s.inner - 24, STRADA, ICE)
        y = 76
        h = y + len(STAGES) * (bh + 8) + 30 + 2 * 52 + 30 + caph + 22 + 54 + sth + 12 + 16
        p = head(s, h, alt, "en")
        p.append(sect(s, 26, "VEYMEER · THE ENGINE", ICE))
        p.append(t(s.pad, 46, "from first principles, in Rust,", s.det, DIM))
        p.append(t(s.pad, 63, "CUDA and Python", s.det, DIM))
        for i, (nm, d) in enumerate(STAGES):
            p.append(f'<g opacity="0">{fade(0.2 + i * 0.14)}{card(s, s.pad, y, s.inner, bh, ICE, 0.3)}'
                     f'{t(s.pad+14, y+21, nm, s.title, TEXT)}{t(s.pad+14, y+39, d, s.det, DIM)}</g>')
            if i < len(STAGES) - 1:
                p.append(f'<path d="M{s.pad+20} {y+bh} v8" stroke="{ICE}" stroke-opacity="0.5" stroke-width="1.5"/>')
            y += bh + 8
        y += 16
        p.append(t(s.pad, y, "BACKENDS", s.det, DIM, ls=1.4))
        y += 10
        for i, (nm, v) in enumerate(BACKENDS):
            p.append(f'{card(s, s.pad, y, s.inner, 44, ICE, 0.3)}{t(s.pad+14, y+27, nm, s.title, TEXT)}'
                     f'{t(s.W-s.pad-14, y+27, v, s.det, DIM, anchor="end")}')
            y += 52
        y += 16
        p.append(t(s.pad, y, "ON TOP OF THE LOOP", s.det, DIM, ls=1.4))
        svg, _ = chips(s, s.pad, y + 10, s.inner, CAPS, ICE)
        p.append(svg)
        y += 10 + caph + 14
        p.append(card(s, s.pad, y, s.inner, 54 + sth + 12, ICE, 0.45))
        p.append(f'<rect x="{s.pad}" y="{y}" width="4" height="{54+sth+12}" rx="2" fill="{ICE}">{pulse(0.45, 1, 3.0)}</rect>')
        p.append(t(s.pad + 14, y + 23, "STRADA", s.title, "#F2F2F5", weight=700, ls=2))
        p.append(t(s.pad + 14, y + 41, "desktop IDE on the engine", s.det, DIM))
        svg, _ = chips(s, s.pad + 12, y + 54, s.inner - 24, STRADA, ICE)
        p.append(svg)
        return "\n".join(p + tail(s, h)), h

    bw = (s.inner - 5 * 14) / 6
    budget = chars(bw - 22, s.det)
    laid = [(n, wrap(d, budget)) for n, d in STAGES]
    bh = 32 + max(len(d) for _, d in laid) * 16 + 10
    top = 48
    _, caph = chips(s, 0, 0, s.inner, CAPS, ICE)
    by = top + bh + 34
    cy_ = by + 44 + 34
    sy = cy_ + caph + 18
    h = sy + 82 + 16
    p = head(s, h, alt, "en")
    p.append(sect(s, 28, "VEYMEER · THE ENGINE, FROM FIRST PRINCIPLES", ICE))
    p.append(t(s.W - s.pad, 28, "Rust · CUDA · Python", s.det, DIM, anchor="end"))
    for i, (nm, dl) in enumerate(laid):
        x = s.pad + i * (bw + 14)
        g = [f'<g opacity="0">{fade(0.2 + i * 0.18)}', card(s, x, top, bw, bh, ICE, 0.32),
             t(x + 11, top + 23, nm, s.body, TEXT, weight=700)]
        for j, ln in enumerate(dl):
            g.append(t(x + 11, top + 43 + j * 16, ln, s.det, DIM))
        g.append('</g>')
        p.append("".join(g))
        if i < len(laid) - 1:
            p.append(f'<path d="M{x+bw+2:.1f} {top+bh/2} h7" stroke="{ICE}" stroke-opacity="0.6" stroke-width="1.6"/>'
                     f'<path d="M{x+bw+8:.1f} {top+bh/2-4} l5 4 -5 4z" fill="{ICE}" fill-opacity="0.7"/>')
    for k in range(3):
        p.append(travel(f"M{s.pad+6} {top+bh} H{s.W-s.pad-6}", 3.6, 1.2 + k * 1.2, 3.0, ICE))
    p.append(t(s.pad, by - 10, "BACKENDS", s.det, DIM, ls=1.6))
    hw = (s.inner - 14) / 2
    for i, (nm, v) in enumerate(BACKENDS):
        x = s.pad + i * (hw + 14)
        p.append(f'<g opacity="0">{fade(1.3 + i * 0.18)}{card(s, x, by, hw, 44, ICE, 0.3)}'
                 f'{t(x+14, by+27, nm, s.title, TEXT, weight=700)}'
                 f'{t(x+hw-14, by+27, v, s.det, MUTE, anchor="end")}</g>')
    p.append(t(s.pad, cy_ - 10, "ON TOP OF THE LOOP", s.det, DIM, ls=1.6))
    svg, _ = chips(s, s.pad, cy_, s.inner, CAPS, ICE)
    p.append(f'<g opacity="0">{fade(1.7)}{svg}</g>')
    p.append(f'<g opacity="0">{fade(2.0)}{card(s, s.pad, sy, s.inner, 82, ICE, 0.5)}'
             f'<rect x="{s.pad}" y="{sy}" width="4" height="82" rx="2" fill="{ICE}">{pulse(0.45, 1, 3.0)}</rect>'
             f'{t(s.pad+16, sy+27, "STRADA", s.title, "#F2F2F5", weight=700, ls=3)}'
             f'{t(s.pad+150, sy+27, "a desktop IDE built on the engine", s.det, DIM)}'
             f'{chips(s, s.pad+16, sy+44, s.inner-32, STRADA, ICE)[0]}</g>')
    return "\n".join(p + tail(s, h)), h


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
        mot = (f'<animateMotion path="M{r} 0A{r} {b} 0 0 1 {-r} 0" dur="{SW}s" repeatCount="indefinite" '
               f'calcMode="spline" keyPoints="0;0.5;1;1" keyTimes="0;0.43;0.86;1" '
               f'keySplines="0.2 0.5 0.6 1;0.4 0 0.8 0.5;0 0 1 1"/>')
    else:
        mot = (f'<animateMotion path="M{r} 0H{-r}" dur="{SW}s" repeatCount="indefinite" '
               f'calcMode="linear" keyPoints="0;1;1" keyTimes="0;0.6;1"/>'
               f'<animate attributeName="opacity" values="1;1;0.22;0.22" keyTimes="0;0.29;0.33;1" '
               f'dur="{SW}s" repeatCount="indefinite"/>')
    for i in range(N_DRONES):
        g.append(f'<g transform="rotate({i * 360 / N_DRONES:g})"><circle r="1.7" fill="{col}">{mot}</circle></g>')
    g.append('</g>')
    if not governed:
        g.append(f'<circle cx="{cx}" cy="{cy}" r="0" fill="{RED}" opacity="0">'
                 f'<animate attributeName="r" values="0;0;{r*0.5:.0f};{r*0.5:.0f}" keyTimes="0;0.27;0.4;1" '
                 f'dur="{SW}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0.75;0;0" keyTimes="0;0.29;0.42;1" '
                 f'dur="{SW}s" repeatCount="indefinite"/></circle>')
    return "".join(g)


GOV = [("collisions: 717 → 0", "collisions: 717 → 0"),
       ("all 60 drones reach their goal", "all 60 reach their goal"),
       ("decentralised, no central planner", "no central planner")]


def governor(s, x, y, w):
    hh = 118 + len(GOV) * 22
    g = [card(s, x, y, w, hh, AMBER, 0.35),
         t(x + 16, y + 25, "THE GOVERNOR", s.det, AMBER, ls=1.6),
         t(x + 16, y + 62, "v ≤ √(a·g)", 26, "#F2F2F5", weight=700),
         t(x + 16, y + 85, "a speed limit derived from", s.det, DIM),
         t(x + 16, y + 102, "turning physics", s.det, DIM)]
    for i, pair in enumerate(GOV):
        ln = pair[1] if s.n else pair[0]
        ly = y + 132 + i * 22
        g.append(f'<circle cx="{x+20}" cy="{ly-4}" r="3.4" fill="{GREEN}">{pulse(0.3, 1, 2.4, i * 0.4)}</circle>')
        g.append(t(x + 32, ly, ln, s.det, TEXT))
    return "".join(g), hh


def swarm(s):
    alt = ("Lumo, decentralised collision avoidance for drone swarms. In a 60-drone worst-case crossing, "
           "a speed governor derived from turning physics reduced collisions from 717 to zero, "
           "with every drone still reaching its goal.")
    r = 80 if s.n else 84
    if s.n:
        cx = s.W // 2
        blk = 2 * r + 18 + 84
        _, gh = governor(s, 0, 0, s.inner)
        h = 74 + 2 * blk + gh + 16 + 48
        p = head(s, h, alt, "sw")
        p.append(sect(s, 26, "LUMO · DRONE SWARM"))
        p.append(t(s.pad, 46, "60 drones swap sides through one", s.det, DIM))
        p.append(t(s.pad, 63, "crossing point: the worst case", s.det, DIM))
        y = 74
        for gov in (False, True):
            p.append(t(cx, y + 20, "SPEED GOVERNOR" if gov else "UNGOVERNED", s.det,
                       TEXT if gov else MUTE, anchor="middle", ls=1.6))
            p.append(arena(cx, y + 34 + r + 9, r, gov))
            p.append(t(cx - 6, y + 34 + 2 * r + 18 + 30, "0" if gov else "717", 26,
                       GREEN if gov else RED, anchor="end", weight=700))
            p.append(t(cx + 4, y + 34 + 2 * r + 18 + 28, "collisions", s.det, DIM))
            y += blk
        svg, _ = governor(s, s.pad, y + 8, s.inner)
        p.append(svg)
        fy = y + 8 + gh + 26
        p.append(t(s.pad, fy, "arenas are a schematic of the", s.det, DIM))
        p.append(t(s.pad, fy + 17, "crossing, not simulator output", s.det, DIM))
        return "\n".join(p + tail(s, h)), h

    h = 372
    p = head(s, h, alt, "sw")
    p.append(sect(s, 28, "LUMO · DECENTRALISED DRONE SWARM COORDINATION"))
    p.append(t(s.pad, 50, "60 drones swap sides through a single crossing point: the worst case", s.det, DIM))
    cy = 178
    for k, gov in enumerate((False, True)):
        cx = s.pad + 104 + k * 232
        p.append(t(cx, 78, "SPEED GOVERNOR" if gov else "UNGOVERNED", s.det,
                   TEXT if gov else MUTE, anchor="middle", ls=1.6))
        p.append(arena(cx, cy, r, gov))
        p.append(t(cx - 6, cy + r + 44, "0" if gov else "717", 28, GREEN if gov else RED,
                   anchor="end", weight=700))
        p.append(t(cx + 5, cy + r + 42, "collisions", s.det, DIM))
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
        laid = [(n, sub, col, labs, chips(s, 0, 0, s.inner, labs, col)[1]) for n, sub, col, labs in REACH]
        h = 46 + sum(34 + ch + 16 for *_, ch in laid) + 44
        p = head(s, h, alt, "rc")
        p.append(sect(s, 26, "WHERE IT RUNS"))
        y = 52
        for i, (name, sub, col, labs, ch) in enumerate(laid):
            p.append(f'<g opacity="0">{fade(0.2 + i * 0.15)}{t(s.pad, y, name, s.title, TEXT)}'
                     f'{t(s.W-s.pad, y, sub, s.det, DIM, anchor="end")}'
                     f'{chips(s, s.pad, y + 12, s.inner, labs, col)[0]}</g>')
            y += 34 + ch + 16
        p.append(f'<line x1="{s.pad}" y1="{y-14}" x2="{s.W-s.pad}" y2="{y-14}" stroke="{GRID}" stroke-opacity="0.12"/>')
        p.append(t(s.pad, y + 6, "five operating systems", s.det, MUTE))
        p.append(t(s.pad, y + 23, "four GPU vendors · the web", s.det, MUTE))
        return "\n".join(p + tail(s, h)), h

    rh = 44
    h = 48 + len(REACH) * rh + 46
    p = head(s, h, alt, "rc")
    p.append(sect(s, 28, "WHERE IT RUNS"))
    for i, (name, sub, col, labs) in enumerate(REACH):
        y = 48 + i * rh
        if i:
            p.append(f'<line x1="{s.pad}" y1="{y}" x2="{s.W-s.pad}" y2="{y}" stroke="{GRID}" stroke-opacity="0.08"/>')
        p.append(f'<g opacity="0">{fade(0.2 + i * 0.15)}{t(s.pad, y + 27, name, s.title, TEXT, weight=700)}'
                 f'{t(s.pad + 160, y + 27, sub, s.det, DIM)}'
                 f'{chips(s, s.pad + 318, y + 10, s.inner - 318, labs, col)[0]}</g>')
    fy = h - 16
    p.append(f'<line x1="{s.pad}" y1="{fy-20}" x2="{s.W-s.pad}" y2="{fy-20}" stroke="{GRID}" stroke-opacity="0.12"/>')
    p.append(f'<circle cx="{s.pad+5}" cy="{fy-4}" r="3.6" fill="{GREEN}">{pulse(0.3, 1, 2.2)}</circle>')
    p.append(t(s.pad + 18, fy, REACH_NOTE, s.det, MUTE))
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
            f'<rect width="4" height="{h}" fill="{AMBER}"/>'
            f'{t(14, 23, label, 12.5, AMBER, ls=1.2, weight=700)}'
            f'{t(14 + lw + 10, 23, value, 13, TEXT)}'
            f'<rect x="0" y="0" width="60" height="{h}" fill="url(#b)"><animate attributeName="x" '
            f'values="-60;{w}" dur="4.5s" repeatCount="indefinite"/></rect>'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="8" fill="none" stroke="{AMBER}" '
            f'stroke-opacity="0.4"/></g></svg>')


BUILDERS = {"header": header, "whoami": whoami, "vault": vault, "veymeer": veymeer,
            "engine": engine, "timeline": timeline, "depth": depth, "portfolio": portfolio,
            "swarm": swarm, "method": method, "bme": bme, "reach": reach}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        for suffix, narrow in (("", False), ("-narrow", True)):
            svg, h = fn(S(narrow))
            path = f"{OUT}/{name}{suffix}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"{path:34} {S(narrow).W}x{h}")
    for slug, label, value in BUTTONS:
        path = f"{OUT}/btn-{slug}.svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(button(label, value))
        print(path)
