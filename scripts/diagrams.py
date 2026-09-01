#!/usr/bin/env python3
"""Build the narrative diagrams in a wide and a narrow variant.

An SVG rendered as <img> scales as a picture: the text does not reflow, so a
layout that is legible at 820px is unreadable at 293px (GitHub's README column
on a phone). Each diagram is therefore emitted twice and selected in markdown
with <picture><source media="(max-width: 600px)">.

Type scale is the constraint that drives everything: nothing renders below 12px
after the browser's scale factor, at either width.
"""
import os

OUT = "assets"
BG, GRID, DIM, TEXT = "#07070A", "#FFC93C", "#5F6672", "#E4E6EB"
AMBER, GREEN, RED, MUTE = "#FFC93C", "#3FB950", "#F85149", "#8B929E"
PANEL, LINE = "#0E1116", "#8A7A4A"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"


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
    return max(6, int(width_px / (size * 0.605)))


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


def tail(s, h, motion=True):
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
               f'stroke="{GRID}" stroke-opacity="0.16"/></g></svg>')
    return out


def sect(s, y, t):
    return (f'<text x="{s.pad}" y="{y}" font-family="{MONO}" font-size="{s.label}" '
            f'fill="{AMBER}" letter-spacing="2.2">{E(t)}</text>')


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
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}"'
            f' fill="{fill}"{a}{l}{w}>{E(txt)}</text>')


# ----------------------------------------------------------------------- header

def header(s):
    if s.n:
        h = 210
        p = head(s, h, "IronGap // Vault-OS", "hd")
        p.append(f'<rect x="{s.pad-10}" y="26" width="3" height="{h-58}" fill="{AMBER}">'
                 f'<animate attributeName="opacity" values="0.6;1;0.6" dur="3.4s" repeatCount="indefinite"/></rect>')
        p.append(t(s.pad, 58, "IRONGAP", 30, "#F2F2F5", ls=3, weight=700))
        p.append(t(s.pad, 90, "// VAULT-OS", 26, AMBER, ls=2, weight=700))
        p.append(t(s.pad, 116, "Taha Halakooei", s.body, MUTE))
        p.append(t(s.pad, 134, "Founder & Chief Architect", s.det, DIM))
        p.append(sweep("hd", s.W, h, band=54, dur=5.5))
        rows = [("TPM 2.0", "TETHERED", GREEN), ("ENCLAVE", "SEALED", GREEN),
                ("EGRESS", "0 PATHS", AMBER)]
        for i, (k, v, c) in enumerate(rows):
            y = 162 + i * 20
            p.append(f'<g opacity="0">{fade(0.4 + i * 0.18)}'
                     f'<circle cx="{s.pad+4}" cy="{y-4}" r="3.2" fill="{c}">{pulse(0.25, 1, 2.2, i*0.4)}</circle>'
                     f'{t(s.pad+16, y, k, s.det, DIM)}{t(s.W-s.pad, y, v, s.det, c, anchor="end")}</g>')
        return "\n".join(p + tail(s, h)), h

    h = 200
    p = head(s, h, "IronGap // Vault-OS — the air-gapped AI appliance", "hd")
    p.append(sweep("hd", s.W, h, band=64, dur=6.0))
    p.append(f'<rect x="{s.pad-12}" y="26" width="4" height="{h-52}" fill="{AMBER}" filter="url(#glhd)">'
             f'{pulse(0.5, 1, 3.4)}</rect>')
    p.append(t(s.pad, 72, "IRONGAP", 42, "#F2F2F5", ls=5, weight=700))
    p.append(t(s.pad + 292, 72, "// VAULT-OS", 42, AMBER, ls=5, weight=700))
    p.append(t(s.pad, 102, "Taha Halakooei  ·  Founder & Chief Architect  ·  Istanbul", s.body, MUTE))
    tag = "The Air-Gapped AI Appliance for Zero-Trust Environments"
    tw = len(tag) * 16 * 0.605
    p.append(f'<defs>{typeclip("hd", s.pad, 118, tw, 22, dur=2.0, begin=0.4)}</defs>')
    p.append(f'<g clip-path="url(#tchd)">{t(s.pad, 132, tag, 16, TEXT)}</g>')
    p.append(caret(s.pad + tw + 3, 118, 17, AMBER, begin=2.4))
    cells = [("TPM 2.0", "TETHERED", GREEN), ("ENCLAVE", "SEALED", GREEN),
             ("LEDGER", "UNBROKEN", GREEN), ("EGRESS", "0 PATHS", AMBER)]
    for i, (k, v, c) in enumerate(cells):
        x = s.pad + i * 195
        p.append(f'<g opacity="0">{fade(2.6 + i * 0.18)}'
                 f'<circle cx="{x+4}" cy="{168}" r="3.4" fill="{c}">{pulse(0.2, 1, 2.2, i*0.35)}</circle>'
                 f'{t(x+16, 172, k, s.det, DIM)}{t(x+92, 172, v, s.det, c)}</g>')
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- whoami

WHO = [
    ("whoami", ["Taha Halakooei — founder & chief architect,", "IronGap Technologies"],
     ["Taha Halakooei", "founder & chief architect, IronGap"]),
    ("cat ~/.focus", ["air-gapped AI infrastructure · sovereign compute", "· zero-trust systems"],
     ["air-gapped AI infrastructure", "sovereign compute · zero-trust"]),
    ("ls ~/building", ["vault-os/   vault-ecosystem/   traces/", "studyhub/   bme-nexus/"],
     ["vault-os/  vault-ecosystem/", "traces/  studyhub/  bme-nexus/"]),
    ("uptime", ["industrial systems since 2024 · founded Jan 2026", "· Vault-OS v1.0.9.1 shipping"],
     ["industrial systems since 2024", "founded Jan 2026 · v1.0.9.1"]),
    ("echo $PRINCIPLE", ["isolation you can verify beats assurance", "you have to trust"],
     ["isolation you can verify beats", "assurance you have to trust"]),
]


def whoami(s):
    lh = 19 if s.n else 21
    blk = 26 + lh * 2 if s.n else 28 + lh * 2
    h = 52 + len(WHO) * blk + 34
    p = head(s, h, "Terminal introduction", "wh")
    p.append(f'<rect width="{s.W}" height="36" fill="{PANEL}"/>')
    for i, c in enumerate([RED, AMBER, GREEN]):
        p.append(f'<circle cx="{20+i*17}" cy="18" r="4.6" fill="{c}" fill-opacity="0.8"/>')
    p.append(t(78, 22, "taha@irongap — zsh", s.det, DIM))
    p.append(f'<line x1="0" y1="36" x2="{s.W}" y2="36" stroke="{GRID}" stroke-opacity="0.16"/>')
    clips = []
    y = 62
    for i, (cmd, wide, narrow) in enumerate(WHO):
        lines = narrow if s.n else wide
        g = [f'<g opacity="0">{fade(0.25 + i * 0.5)}']
        g.append(t(s.pad, y, "›", s.body, GREEN))
        g.append(f'<g clip-path="url(#tcw{i})">{t(s.pad + 16, y, cmd, s.body, TEXT)}</g>')
        for j, ln in enumerate(lines):
            col = AMBER if i in (2, 4) else MUTE
            g.append(t(s.pad, y + lh * (j + 1), ln, s.body, col))
        g.append('</g>')
        cw_ = len(cmd) * s.body * 0.605
        clips.append(typeclip(f"w{i}", s.pad + 16, y - 14, cw_, 18, dur=0.45,
                              begin=0.25 + i * 0.5))
        p.append("".join(g))
        y += blk
    p.insert(1, f'<defs>{"".join(clips)}</defs>')
    p.append(f'<text x="{s.pad}" y="{y}" font-family="{MONO}" font-size="{s.body}" '
             f'fill="{GREEN}" opacity="0">{fade(2.9, 0.2)}›</text>')
    p.append(f'<rect x="{s.pad+16}" y="{y-12}" width="9" height="15" fill="{GREEN}" opacity="0">'
             f'{fade(2.9, 0.2)}<animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" '
             f'begin="3.1s" repeatCount="indefinite"/></rect>')
    return "\n".join(p + tail(s, h)), h


# --------------------------------------------------------------------- timeline

TL = [("2013 — 2025", "SAMPAD", "exceptional talents programme", GREEN),
      ("JUN 2024", "GOLESTAN AXON", "systems & IT · iodine plant uptime", "#5FB84B"),
      ("SEP 2025", "YILDIZ TECHNICAL", "biomedical engineering, 100% English", "#8FB63C"),
      ("JAN 2026", "IRONGAP FOUNDED", "Vault-OS architecture from bare metal", "#D9C22E"),
      ("NOW", "v1.0.9.1", "shipping on Windows", AMBER)]


def timeline(s):
    if s.n:
        x = s.pad + 6
        budget = chars(s.W - s.pad - (x + 20), s.det)
        laid = [(d, n, wrap(desc, budget), c) for d, n, desc, c in TL]
        dmax = max(len(e[2]) for e in laid)
        rh = 44 + dmax * 17
        h = 44 + len(laid) * rh + 12
        p = head(s, h, "Trajectory", "tl")
        p.append(sect(s, 26, "TRAJECTORY"))
        p.append(f'<line x1="{x}" y1="52" x2="{x}" y2="{h-26}" stroke="{GRID}" stroke-opacity="0.2"/>')
        for i, (date, name, dl, col) in enumerate(laid):
            y = 62 + i * rh
            g = [f'<g opacity="0">{fade(0.2 + i * 0.22)}',
                 f'<circle cx="{x}" cy="{y}" r="6" fill="{BG}" stroke="{col}" stroke-width="2">'
                 f'{pulse(0.4, 1, 2.6, i*0.3) if i == len(TL)-1 else ""}</circle>',
                 t(x + 20, y - 4, date, s.det, DIM, ls=1.2),
                 t(x + 20, y + 16, name, s.title, TEXT)]
            for j, ln in enumerate(dl):
                g.append(t(x + 20, y + 35 + j * 17, ln, s.det, DIM))
            g.append('</g>')
            p.append("".join(g))
        return "\n".join(p + tail(s, h)), h

    slot = s.inner / len(TL)
    xs = [s.pad + slot * (i + 0.5) for i in range(len(TL))]
    budget = chars(slot - 12, s.det)
    laid = [(d, n, wrap(desc, budget), c) for d, n, desc, c in TL]
    dmax = max(len(x[2]) for x in laid)
    h = 150 + dmax * 17 + 16
    p = head(s, h, "Trajectory from Sampad to IronGap", "tl")
    p.append(sect(s, 28, "TRAJECTORY"))
    p.append(f'<defs><linearGradient id="tg" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{GREEN}"/><stop offset="1" stop-color="{AMBER}"/></linearGradient></defs>')
    span = xs[-1] - xs[0]
    p.append(f'<line x1="{xs[0]:.1f}" y1="94" x2="{xs[-1]:.1f}" y2="94" stroke="url(#tg)" stroke-width="2.5" '
             f'stroke-dasharray="{span:.0f}" stroke-dashoffset="{span:.0f}">'
             f'<animate attributeName="stroke-dashoffset" from="{span:.0f}" to="0" dur="2.2s" fill="freeze"/></line>')
    for i, (date, name, dl, col) in enumerate(laid):
        x = xs[i]
        g = [f'<g opacity="0">{fade(0.2 + i * 0.3)}',
             t(x, 76, date, s.det, DIM if i < 4 else AMBER, anchor="middle", ls=1.2),
             f'<circle cx="{x:.1f}" cy="94" r="{7 if i==4 else 6}" fill="{col if i==4 else BG}" '
             f'stroke="{col}" stroke-width="2"/>',
             t(x, 126, name, s.body, TEXT, anchor="middle")]
        for j, ln in enumerate(dl):
            g.append(t(x, 148 + j * 17, ln, s.det, DIM, anchor="middle"))
        g.append('</g>')
        p.append("".join(g))
    return "\n".join(p + tail(s, h)), h


# ------------------------------------------------------------------------ depth

LAYERS = [("Interface", "cross-platform clients, offline-first state", "Flutter · React · TypeScript", GREEN),
          ("Orchestration", "DAG runtime, sandboxed agents, critic pass", "ReAct · MCP · Node.js", "#5FB84B"),
          ("Inference", "engine abstraction, multi-node GPU clustering", "vLLM · TensorRT-LLM", "#8FB63C"),
          ("Data", "vector search, spatial constraints, graphs", "PostgreSQL · pgvector · PostGIS", "#C0BE34"),
          ("Bare metal", "no container runtime, native services", "Windows · Linux · Shell", "#E0C630"),
          ("Silicon", "TPM attestation, PCR-bound licensing", "TPM 2.0 · HSM · NIST SP 800-88", AMBER)]


def depth(s):
    if s.n:
        budget = chars(s.inner - 28, s.det)
        laid = [(n, wrap(d, budget), wrap(tc, budget), c) for n, d, tc, c in LAYERS]
        dmax = max(len(d) for _, d, _, _ in laid)
        tmax = max(len(tc) for _, _, tc, _ in laid)
        rh = 26 + dmax * 17 + 4 + tmax * 17
    else:
        # tech sits right-aligned on its own column; description gets the rest
        budget = chars(s.inner - 300, s.det)
        laid = [(n, wrap(d, budget), [tc], c) for n, d, tc, c in LAYERS]
        dmax = max(len(d) for _, d, _, _ in laid)
        rh = 30 + dmax * 17
    h = 46 + len(laid) * (rh + 8) + 16
    p = head(s, h, "The stack I work across, from silicon to interface", "dp")
    p.append(sect(s, 28, "THE STACK I WORK ACROSS"))
    for i, (name, dl, tl_, col) in enumerate(laid):
        y = 46 + i * (rh + 8)
        g = [f'<g opacity="0">{fade(0.2 + (len(laid)-i) * 0.12)}',
             card(s, s.pad, y, s.inner, rh, col, 0.32),
             f'<rect x="{s.pad}" y="{y}" width="4" height="{rh}" rx="2" fill="{col}">'
             f'{pulse(0.45, 1, 3.0, i * 0.35)}</rect>',
             t(s.pad + 15, y + 21, name, s.title, TEXT)]
        for j, ln in enumerate(dl):
            g.append(t(s.pad + 15, y + 40 + j * 17, ln, s.det, DIM))
        if s.n:
            for j, ln in enumerate(tl_):
                g.append(t(s.pad + 15, y + 40 + dmax * 17 + 4 + j * 17, ln, s.det, col))
        else:
            g.append(t(s.W - s.pad - 14, y + rh / 2 + 4, tl_[0], s.det, col, anchor="end"))
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
    bh = 30 + body_h * 16 + 10 + ex_h * 15
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
    cy = top + bh / 2
    p.append(travel(f"M{s.pad+bw/2:.0f} {cy:.0f} H{s.pad+4*(bw+12)+bw/2:.0f}", 6.5, 1.4, 4.5, AMBER))
    p.append(burst(s.pad + 2 * (bw + 12) + bw / 2, cy, 22, 3.2, 2.6, AMBER))
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

DOMAINS = [("SECURITY & INFRA", AMBER,
            [("Vault-OS", "air-gapped AI appliance", "TPM 2.0 · pgvector · vLLM"),
             ("Vault-Ecosystem", "clients, 6 platforms", "Flutter · biometric lock"),
             ("Console MCP", "agent interface", "every write hits the ledger")]),
           ("PLATFORMS", "#5FB84B",
            [("TRACES", "location-locked content", "PostGIS · pgvector · Fastify"),
             ("StudyHub OS", "modular productivity", "React · Supabase RBAC"),
             ("YTU BME Nexus", "department platform", "React · Supabase")]),
           ("APPLIED VISION", "#8FB63C",
            [("Virtual Mouse", "hands-free pointer control", "MediaPipe · One-Euro"),
             ("Polaris R&D", "MATE research group", "Python · algorithms")]),
           ("INDUSTRIAL", MUTE,
            [("Golestan Axon", "systems & IT, 2 years", "iodine plant commissioning"),
             ("Iodina", "extraction plant systems", "where uptime was learned")])]


def portfolio(s):
    if s.n:
        ch = 60
        h = 44
        for _, _, items in DOMAINS:
            h += 30 + len(items) * (ch + 8)
        h += 12
        p = head(s, h, "Map of work across four domains", "pf")
        p.append(sect(s, 26, "WHAT I HAVE BUILT"))
        y = 48
        k = 0
        for name, col, items in DOMAINS:
            p.append(t(s.pad, y, name, s.det, col, ls=1.5))
            p.append(f'<line x1="{s.pad}" y1="{y+7}" x2="{s.W-s.pad}" y2="{y+7}" stroke="{col}" stroke-opacity="0.3"/>')
            y += 20
            for nm, desc, tech in items:
                p.append(f'<g opacity="0">{fade(0.15 + k * 0.1)}'
                         f'{card(s, s.pad, y, s.inner, ch, col, 0.26)}'
                         f'{t(s.pad+12, y+21, nm, s.title, TEXT)}'
                         f'{t(s.pad+12, y+38, desc, s.det, DIM)}'
                         f'{t(s.pad+12, y+54, tech, s.det, LINE)}</g>')
                y += ch + 8
                k += 1
            y += 10
        return "\n".join(p + tail(s, h)), h

    cw = (s.inner - 3 * 12) / 4
    budget = chars(cw - 24, s.det)
    laid = [(nm, wrap(d, budget), wrap(tc, budget), col)
            for _, col, items in DOMAINS for nm, d, tc in items]
    dmax = max(len(d) for _, d, _, _ in laid)
    tmax = max(len(tc) for _, _, tc, _ in laid)
    ch = 26 + dmax * 15 + 6 + tmax * 15
    rows = max(len(i) for _, _, i in DOMAINS)
    h = 78 + rows * (ch + 8) + 14
    p = head(s, h, "Map of work across security, platforms, applied vision and industry", "pf")
    p.append(sect(s, 28, "WHAT I HAVE BUILT"))
    k = 0
    for c, (name, col, items) in enumerate(DOMAINS):
        x = s.pad + c * (cw + 12)
        p.append(t(x, 58, name, s.det, col, ls=1.3))
        p.append(f'<line x1="{x}" y1="66" x2="{x+cw}" y2="66" stroke="{col}" stroke-opacity="0.3"/>')
        for r, (nm, desc, tech) in enumerate(items):
            y = 80 + r * (ch + 8)
            dl, tl_ = wrap(desc, budget), wrap(tech, budget)
            g = [f'<g opacity="0">{fade(0.15 + k * 0.09)}', card(s, x, y, cw, ch, col, 0.26),
                 t(x + 12, y + 21, nm, s.body, TEXT)]
            for j, ln in enumerate(dl):
                g.append(t(x + 12, y + 39 + j * 15, ln, s.det, DIM))
            for j, ln in enumerate(tl_):
                g.append(t(x + 12, y + 39 + dmax * 15 + 8 + j * 15, ln, s.det, LINE))
            g.append('</g>')
            p.append("".join(g))
            k += 1
    return "\n".join(p + tail(s, h)), h


# ------------------------------------------------------------------------ focus

PLATS = ["Windows", "Linux", "macOS", "Android", "iOS"]
PRODUCTS = [("Vault-OS", "the appliance · v1.0.9.1", ["ship", "dev", "dev", "no", "no"]),
            ("Vault-Ecosystem", "companion clients", ["ship", "dev", "dev", "dev", "dev"])]


def mark(x, y, st, uid):
    if st == "ship":
        return f'<circle cx="{x}" cy="{y}" r="6.5" fill="{GREEN}"/>'
    if st == "dev":
        return (f'<circle cx="{x}" cy="{y}" r="6.5" fill="none" stroke="{AMBER}" stroke-width="2" '
                f'stroke-dasharray="3 3"><animateTransform attributeName="transform" type="rotate" '
                f'from="0 {x} {y}" to="360 {x} {y}" dur="9s" repeatCount="indefinite"/></circle>')
    return f'<text x="{x}" y="{y+5}" font-family="{MONO}" font-size="14" fill="#2A2E36" text-anchor="middle">—</text>'


def focus(s):
    if s.n:
        h = 44 + len(PRODUCTS) * (34 + len(PLATS) * 24 + 14) + 46
        p = head(s, h, "Platform shipping status", "fc")
        p.append(sect(s, 26, "SHIPPING STATUS"))
        y = 52
        for pi, (nm, sub, sts) in enumerate(PRODUCTS):
            p.append(t(s.pad, y, nm, s.title, TEXT))
            p.append(t(s.pad, y + 17, sub, s.det, DIM))
            y += 32
            for i, pl in enumerate(PLATS):
                p.append(f'<g opacity="0">{fade(0.2 + (pi * 5 + i) * 0.08)}'
                         f'{mark(s.pad+10, y+i*24, sts[i], f"n{pi}{i}")}'
                         f'{t(s.pad+30, y+i*24+5, pl, s.body, MUTE)}</g>')
            y += len(PLATS) * 24 + 14
        p.append(f'<line x1="{s.pad}" y1="{y-6}" x2="{s.W-s.pad}" y2="{y-6}" stroke="{GRID}" stroke-opacity="0.12"/>')
        p.append(f'<circle cx="{s.pad+6}" cy="{y+14}" r="5.5" fill="{GREEN}"/>')
        p.append(t(s.pad + 20, y + 19, "shipping", s.det, DIM))
        p.append(f'<circle cx="{s.pad+112}" cy="{y+14}" r="5.5" fill="none" stroke="{AMBER}" '
                 f'stroke-width="2" stroke-dasharray="3 3"/>')
        p.append(t(s.pad + 126, y + 19, "in development", s.det, DIM))
        return "\n".join(p + tail(s, h)), h

    h = 230
    p = head(s, h, "Platform shipping status for Vault-OS and Vault-Ecosystem", "fc")
    p.append(sect(s, 28, "SHIPPING STATUS"))
    x0 = s.pad + 250
    step = (s.W - s.pad - x0) / len(PLATS)
    for i, pl in enumerate(PLATS):
        p.append(t(x0 + step * i + step / 2, 62, pl.upper(), s.det, DIM, anchor="middle", ls=1.4))
    p.append(f'<line x1="{s.pad}" y1="72" x2="{s.W-s.pad}" y2="72" stroke="{GRID}" stroke-opacity="0.12"/>')
    for pi, (nm, sub, sts) in enumerate(PRODUCTS):
        y = 104 + pi * 56
        p.append(f'<g opacity="0">{fade(0.2 + pi * 0.25)}'
                 f'{t(s.pad, y, nm, s.title, TEXT)}{t(s.pad, y+18, sub, s.det, DIM)}')
        for i in range(len(PLATS)):
            p.append(mark(x0 + step * i + step / 2, y - 5, sts[i], f"w{pi}{i}"))
        p.append('</g>')
    p.append(f'<line x1="{s.pad}" y1="180" x2="{s.W-s.pad}" y2="180" stroke="{GRID}" stroke-opacity="0.12"/>')
    p.append(f'<circle cx="{s.pad+6}" cy="203" r="5.5" fill="{GREEN}"/>')
    p.append(t(s.pad + 20, 208, "shipping", s.body, DIM))
    p.append(f'<circle cx="{s.pad+150}" cy="203" r="5.5" fill="none" stroke="{AMBER}" stroke-width="2" stroke-dasharray="3 3"/>')
    p.append(t(s.pad + 164, 208, "in development", s.body, DIM))
    p.append(t(s.pad + 330, 209, "—", 14, "#2A2E36"))
    p.append(t(s.pad + 348, 208, "not planned", s.body, DIM))
    return "\n".join(p + tail(s, h)), h


BUILDERS = {"header": header, "whoami": whoami, "timeline": timeline, "depth": depth,
            "method": method, "bme": bme, "portfolio": portfolio, "focus": focus}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        for suffix, narrow in (("", False), ("-narrow", True)):
            svg, h = fn(S(narrow))
            path = f"{OUT}/{name}{suffix}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"{path:34} {S(narrow).W}x{h}")
