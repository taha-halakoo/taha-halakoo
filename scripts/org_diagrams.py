#!/usr/bin/env python3
"""Build the IronGap organisation diagrams, wide and narrow, with looping motion.

Same constraints as the personal profile: an SVG in an <img> scales as a
picture, so each diagram is emitted at 820px and again at 300px and selected
with <picture><source media="(max-width: 600px)">.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (S, head, tail, sect, fade, card, t, chars, wrap, pulse,  # noqa: E402
                      travel, burst, orbit, caret, typeclip, sweep,
                      BG, GRID, DIM, TEXT, AMBER, GREEN, RED, MUTE, PANEL, LINE, MONO)

OUT = os.environ.get("ORG_OUT", "org/profile/assets")


def arrow(x1, y1, x2, y2, colour=None, op=0.5, dash=None):
    c = colour or GREEN
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{c}" stroke-opacity="{op}" '
            f'stroke-width="1.6" fill="none"{d}/>'
            f'<path d="M{x2:.1f} {y2-4:.1f} l6 4 -6 4z" fill="{c}" fill-opacity="{op+0.2:.2f}"/>')


# ----------------------------------------------------------------------- header

def org_header(s):
    if s.n:
        h = 196
        p = head(s, h, "IronGap // Vault-OS — air-gapped AI infrastructure", "oh")
        p.append(f'<rect x="{s.pad-10}" y="24" width="3" height="{h-56}" fill="{AMBER}" '
                 f'filter="url(#gloh)">{pulse(0.5, 1, 3.4)}</rect>')
        p.append(t(s.pad, 56, "IRONGAP", 30, "#F2F2F5", ls=3, weight=700))
        p.append(t(s.pad, 88, "// VAULT-OS", 26, AMBER, ls=2, weight=700))
        p.append(t(s.pad, 114, "Air-gapped AI infrastructure", s.body, MUTE))
        p.append(t(s.pad, 132, "for zero-trust environments", s.body, MUTE))
        for i, (k, v, c) in enumerate([("VERSION", "1.0.9.1", AMBER),
                                       ("EGRESS", "0 PATHS", AMBER),
                                       ("STATUS", "SEALED", GREEN)]):
            y = 158 + i * 19
            p.append(f'<g opacity="0">{fade(0.4 + i * 0.18)}'
                     f'<circle cx="{s.pad+4}" cy="{y-4}" r="3.2" fill="{c}">{pulse(0.25, 1, 2.2, i*0.4)}</circle>'
                     f'{t(s.pad+16, y, k, s.det, DIM)}'
                     f'{t(s.W-s.pad, y, v, s.det, c, anchor="end")}</g>')
        return "\n".join(p + tail(s, h)), h

    h = 192
    p = head(s, h, "IronGap // Vault-OS — air-gapped AI infrastructure", "oh")
    p.append(sweep("oh", s.W, h, band=64, dur=6.0))
    p.append(f'<rect x="{s.pad-12}" y="26" width="4" height="{h-52}" fill="{AMBER}" '
             f'filter="url(#gloh)">{pulse(0.5, 1, 3.4)}</rect>')
    p.append(t(s.pad, 72, "IRONGAP", 42, "#F2F2F5", ls=5, weight=700))
    p.append(t(s.pad + 292, 72, "// VAULT-OS", 42, AMBER, ls=5, weight=700))
    p.append(t(s.pad, 102, "Air-gapped AI infrastructure  ·  zero-trust environments  ·  Istanbul",
               s.body, MUTE))
    tag = "Frontier-class models on hardware you physically control"
    tw = len(tag) * 16 * 0.605
    p.append(f'<defs>{typeclip("oh", s.pad, 118, tw, 22, dur=2.0, begin=0.4)}</defs>')
    p.append(f'<g clip-path="url(#tcoh)">{t(s.pad, 132, tag, 16, TEXT)}</g>')
    p.append(caret(s.pad + tw + 3, 118, 17, AMBER, begin=2.4))
    for i, (k, v, c) in enumerate([("VERSION", "1.0.9.1", AMBER), ("EGRESS", "0 PATHS", AMBER),
                                   ("LEDGER", "UNBROKEN", GREEN), ("STATUS", "SEALED", GREEN)]):
        x = s.pad + i * 195
        p.append(f'<g opacity="0">{fade(2.6 + i * 0.18)}'
                 f'<circle cx="{x+4}" cy="164" r="3.4" fill="{c}">{pulse(0.2, 1, 2.2, i*0.35)}</circle>'
                 f'{t(x+16, 168, k, s.det, DIM)}{t(x+92, 168, v, s.det, c)}</g>')
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- airgap

THREATS = ["cloud inference APIs", "vendor telemetry", "model providers",
           "subprocessors", "exfiltration attempts", "cross-border transfer"]
ENCLAVE = [("TPM 2.0 TETHER", "PCR-bound licence"), ("GPU CLUSTER", "vLLM · TensorRT-LLM"),
           ("pgvector + HNSW", "native, zero-docker"), ("DAG RUNTIME", "33 nodes · agents"),
           ("CRITIC PASS", "adversarial review"), ("BURN SWITCH", "NIST SP 800-88")]


def airgap(s):
    if s.n:
        th = 24
        top = 52
        gap_y = top + len(THREATS) * th + 18
        enc_y = gap_y + 58
        rh = 44
        h = enc_y + len(ENCLAVE) * (rh + 6) + 24
        p = head(s, h, "Air-gap architecture: zero egress paths", "ag")
        p.append(sect(s, 26, "UNTRUSTED NETWORK"))
        for i, x in enumerate(THREATS):
            y = top + i * th
            p.append(f'<circle cx="{s.pad+4}" cy="{y-4}" r="3" fill="{RED}"/>')
            p.append(t(s.pad + 16, y, x, s.det, "#8A6F72"))
        p.append(f'<line x1="{s.pad}" y1="{gap_y}" x2="{s.W-s.pad}" y2="{gap_y}" stroke="{AMBER}" '
                 f'stroke-width="3" stroke-dasharray="9 6" filter="url(#glag)">{pulse(0.7, 1, 2.6)}</line>')
        p.append(t(s.W / 2, gap_y + 22, "AIR GAP · 0 EGRESS PATHS", s.det, AMBER, anchor="middle", ls=1.4))
        for i in range(3):
            sx = s.pad + 30 + i * 90
            p.append(travel(f"M{sx} {top - 20} V{gap_y - 6}", 2.8, i * 0.9, 4, RED))
            p.append(burst(sx, gap_y, 17, 2.8, i * 0.9 + 2.0, AMBER))
        p.append(t(s.pad, enc_y - 14, "VAULT-OS ENCLAVE", s.det, GREEN, ls=1.8))
        for i, (nm, sub) in enumerate(ENCLAVE):
            y = enc_y + i * (rh + 6)
            col = AMBER if nm == "BURN SWITCH" else GREEN
            p.append(f'<g opacity="0">{fade(0.3 + i * 0.12)}{card(s, s.pad, y, s.inner, rh, col, 0.32)}'
                     f'{t(s.pad+12, y+19, nm, s.body, TEXT)}{t(s.pad+12, y+35, sub, s.det, DIM)}'
                     f'<circle cx="{s.W-s.pad-14}" cy="{y+rh/2}" r="3.4" fill="{col}">'
                     f'{pulse(0.2, 1, 2.2, i*0.3)}</circle></g>')
        return "\n".join(p + tail(s, h)), h

    lw = 250
    gap_x = s.pad + lw + 58
    ex = gap_x + 46
    ew = s.W - s.pad - ex
    cw = (ew - 12) / 2
    rh = 52
    h = 92 + 3 * (rh + 10) + 46
    p = head(s, h, "Air-gap architecture: zero egress paths between the network and the enclave", "ag")
    p.append(t(s.pad, 28, "UNTRUSTED NETWORK", s.det, RED, ls=1.8))
    p.append(t(ex, 28, "VAULT-OS ENCLAVE · YOUR HARDWARE", s.det, GREEN, ls=1.8))
    p.append(f'<rect x="{s.pad}" y="40" width="{lw}" height="{h-70}" rx="8" fill="{RED}" '
             f'fill-opacity="0.03" stroke="{RED}" stroke-opacity="0.22" stroke-dasharray="5 4"/>')
    for i, x in enumerate(THREATS):
        y = 66 + i * 26
        p.append(f'<circle cx="{s.pad+14}" cy="{y-4}" r="3" fill="{RED}"/>')
        p.append(t(s.pad + 26, y, x, s.det, "#8A6F72"))
    p.append(f'<line x1="{gap_x}" y1="40" x2="{gap_x}" y2="{h-30}" stroke="{AMBER}" stroke-width="3.5" '
             f'stroke-dasharray="10 7" filter="url(#glag)">{pulse(0.72, 1, 2.6)}</line>')
    p.append(t(gap_x, 28, "AIR GAP", s.det, AMBER, anchor="middle", ls=1.8))
    p.append(t(gap_x, h - 14, "0 EGRESS PATHS", s.det, AMBER, anchor="middle", ls=1.4))
    for i in range(4):
        y = 70 + i * 40
        p.append(travel(f"M{s.pad+lw+6} {y} H{gap_x-8}", 2.9, i * 0.62, 4.2, RED))
        p.append(burst(gap_x, y, 19, 2.9, i * 0.62 + 2.1, AMBER))
    p.append(f'<rect x="{ex-10}" y="40" width="{ew+10}" height="{h-70}" rx="8" fill="{GREEN}" '
             f'fill-opacity="0.035" stroke="{GREEN}" stroke-opacity="0.3"/>')
    for i, (nm, sub) in enumerate(ENCLAVE):
        r, c = divmod(i, 2)
        x, y = ex + c * (cw + 12), 52 + r * (rh + 10)
        col = AMBER if nm == "BURN SWITCH" else GREEN
        p.append(f'<g opacity="0">{fade(0.3 + i * 0.1)}{card(s, x, y, cw, rh, col, 0.32)}'
                 f'{t(x+12, y+21, nm, s.body, TEXT)}{t(x+12, y+38, sub, s.det, DIM)}'
                 f'<circle cx="{x+cw-14}" cy="{y+14}" r="3.4" fill="{col}">'
                 f'{pulse(0.2, 1, 2.2, i*0.3)}</circle></g>')
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- ledger

BLOCKS = [("0x01", "a3f9c1"), ("0x02", "7d2e08"), ("0x03", "b81af4"),
          ("0x04", "2c6b7e"), ("0x05", "9e40aa"), ("0x06", "51c7d2")]
CYCLE = 13.0


def ledger(s):
    blocks = BLOCKS[:4] if s.n else BLOCKS
    tamper = 2  # 0x03 is the block that gets altered
    if s.n:
        bh = 52
        h = 52 + len(blocks) * (bh + 16) + 54
        p = head(s, h, "Tamper-evident audit ledger, SHA-256 chained and RSA signed", "lg")
        p.append(sect(s, 26, "TAMPER-EVIDENT LEDGER"))
        for i, (idx, hsh) in enumerate(blocks):
            y = 46 + i * (bh + 16)
            broken = i >= tamper
            p.append(f'<g opacity="0">{fade(0.15 + i * 0.2)}{card(s, s.pad, y, s.inner, bh, GREEN, 0.45)}'
                     f'{t(s.pad+12, y+21, "BLOCK " + idx, s.det, DIM)}'
                     f'{t(s.pad+12, y+40, hsh + "…", s.body, GREEN)}'
                     f'<circle cx="{s.W-s.pad-14}" cy="{y+18}" r="3.4" fill="{GREEN}"/></g>')
            if broken:
                st = 0.50 + (i - tamper) * 0.06
                p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
                         f'keyTimes="0;{st};{st+0.07};0.90;0.94" dur="{CYCLE}s" repeatCount="indefinite"/>'
                         f'{card(s, s.pad, y, s.inner, bh, RED, 0.75, "#1A0E0E")}'
                         f'{t(s.pad+12, y+21, "BLOCK " + idx, s.det, RED)}'
                         f'{t(s.pad+12, y+40, "INVALID" if i > tamper else "ff01d9…", s.body, RED)}'
                         f'<circle cx="{s.W-s.pad-14}" cy="{y+18}" r="3.4" fill="{RED}">'
                         f'{pulse(0.2, 1, 0.8)}</circle></g>')
            if i < len(blocks) - 1:
                p.append(f'<path d="M{s.pad+22} {y+bh} v16" stroke="{GREEN}" stroke-opacity="0.5" stroke-width="1.6"/>')
        fy = 46 + len(blocks) * (bh + 16) + 8
        p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
                 f'keyTimes="0;0.42;0.48;0.52;0.56" dur="{CYCLE}s" repeatCount="indefinite"/>'
                 f'<circle cx="{s.pad+5}" cy="{fy-4}" r="3.6" fill="{GREEN}"/>'
                 f'{t(s.pad+18, fy, "LEDGER INTACT", s.det, GREEN)}</g>')
        p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
                 f'keyTimes="0;0.56;0.62;0.90;0.94" dur="{CYCLE}s" repeatCount="indefinite"/>'
                 f'<circle cx="{s.pad+5}" cy="{fy-4}" r="3.6" fill="{RED}">{pulse(0.2, 1, 0.8)}</circle>'
                 f'{t(s.pad+18, fy, "TAMPER AT 0x03 · CHAIN BROKEN", s.det, RED)}</g>')
        return "\n".join(p + tail(s, h)), h

    bw = (s.inner - 5 * 14) / 6
    bh = 62
    h = 190
    p = head(s, h, "Tamper-evident audit ledger, SHA-256 chained and RSA signed", "lg")
    p.append(sect(s, 28, "TAMPER-EVIDENT AUDIT LEDGER · SHA-256 CHAINED · RSA SIGNED"))
    for i, (idx, hsh) in enumerate(blocks):
        x = s.pad + i * (bw + 14)
        if i:
            p.append(f'<path d="M{x-14} {58+bh/2} h12" stroke="{GREEN}" stroke-opacity="0.5" stroke-width="1.6"/>')
        p.append(f'<g opacity="0">{fade(0.15 + i * 0.16)}{card(s, x, 58, bw, bh, GREEN, 0.45)}'
                 f'{t(x+12, 80, "BLOCK " + idx, s.det, DIM)}'
                 f'{t(x+12, 100, hsh + "…", s.body, GREEN)}'
                 f'<circle cx="{x+bw-13}" cy="76" r="3.4" fill="{GREEN}"/></g>')
        if i >= tamper:
            st = 0.50 + (i - tamper) * 0.05
            p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
                     f'keyTimes="0;{st};{st+0.06};0.90;0.94" dur="{CYCLE}s" repeatCount="indefinite"/>'
                     f'{card(s, x, 58, bw, bh, RED, 0.8, "#1A0E0E")}'
                     f'{t(x+12, 80, "BLOCK " + idx, s.det, RED)}'
                     f'{t(x+12, 100, "INVALID" if i > tamper else "ff01d9…", s.body, RED)}'
                     f'<circle cx="{x+bw-13}" cy="76" r="3.4" fill="{RED}">{pulse(0.2, 1, 0.8)}</circle></g>')
    p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
             f'keyTimes="0;0.42;0.48;0.52;0.56" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'<circle cx="{s.pad+5}" cy="152" r="3.8" fill="{GREEN}"/>'
             f'{t(s.pad+18, 157, "LEDGER INTACT · 6 BLOCKS VERIFIED · SIGNATURE VALID", s.body, GREEN)}</g>')
    p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
             f'keyTimes="0;0.56;0.62;0.90;0.94" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'<circle cx="{s.pad+5}" cy="152" r="3.8" fill="{RED}">{pulse(0.2, 1, 0.8)}</circle>'
             f'{t(s.pad+18, 157, "TAMPER DETECTED AT 0x03 · CHAIN BROKEN · 3 BLOCKS ORPHANED", s.body, RED)}</g>')
    return "\n".join(p + tail(s, h)), h


# -------------------------------------------------------------------- bootchain

BOOT = [("POWER ON", "cold start", GREEN), ("PCR MEASURE", "TPM 2.0 registers", GREEN),
        ("ATTEST", "licence vs silicon", AMBER), ("UNSEAL", "enclave mounts", GREEN),
        ("OPERATIONAL", "no drive letter", GREEN)]


def bootchain(s):
    if s.n:
        rh = 50
        h = 46 + len(BOOT) * (rh + 12) + 96
        p = head(s, h, "Fail-deadly boot chain", "bc")
        p.append(sect(s, 26, "FAIL-DEADLY BOOT CHAIN"))
        for i, (nm, sub, col) in enumerate(BOOT):
            y = 46 + i * (rh + 12)
            p.append(f'<g opacity="0">{fade(0.15 + i * 0.16)}{card(s, s.pad, y, s.inner, rh, col, 0.38)}'
                     f'{t(s.pad+12, y+21, nm, s.body, col if col == AMBER else TEXT)}'
                     f'{t(s.pad+12, y+38, sub, s.det, DIM)}</g>')
            if i < len(BOOT) - 1:
                p.append(f'<path d="M{s.pad+20} {y+rh} v12" stroke="{GREEN}" stroke-opacity="0.5" stroke-width="1.6"/>')
        ay = 46 + 2 * (rh + 12) + rh / 2
        p.append(travel(f"M{s.pad+20} 52 V{46 + 4 * (rh+12) + rh/2:.0f}", 6.0, 0.9, 4.2, GREEN))
        p.append(burst(s.pad + 20, ay, 16, 3.0, 2.2, AMBER))
        hy = 46 + len(BOOT) * (rh + 12) + 14
        p.append(f'<path d="M{s.pad+20} {hy-14} v14" stroke="{RED}" stroke-opacity="0.5" '
                 f'stroke-width="1.5" stroke-dasharray="5 4"/>')
        p.append(f'{card(s, s.pad, hy, s.inner, 56, RED, 0.55, "#1A0E0E")}')
        p.append(t(s.pad + 12, hy + 22, "HALT · KEYS NEVER DERIVED", s.det, RED))
        p.append(t(s.pad + 12, hy + 40, "enclave stays sealed", s.det, "#8A6F72"))
        p.append(f'<circle cx="{s.W-s.pad-16}" cy="{hy+28}" r="4" fill="{RED}">{pulse(0.15, 1, 1.4)}</circle>')
        return "\n".join(p + tail(s, h)), h

    bw = (s.inner - 4 * 12) / 5
    h = 268
    p = head(s, h, "Fail-deadly boot chain: measure, attest, unseal or halt", "bc")
    p.append(sect(s, 28, "FAIL-DEADLY BOOT CHAIN"))
    for i, (nm, sub, col) in enumerate(BOOT):
        x = s.pad + i * (bw + 12)
        p.append(f'<g opacity="0">{fade(0.15 + i * 0.16)}{card(s, x, 66, bw, 62, col, 0.38)}'
                 f'{t(x+12, 90, nm, s.body, col if col == AMBER else TEXT)}'
                 f'{t(x+12, 110, sub, s.det, DIM)}</g>')
        if i:
            p.append(arrow(x - 12, 97, x - 2, 97, GREEN, 0.5))
    ax = s.pad + 2 * (bw + 12) + bw / 2
    p.append(travel(f"M{s.pad+bw/2:.0f} 97 H{s.pad+4*(bw+12)+bw/2:.0f}", 6.5, 1.0, 4.5, GREEN))
    p.append(burst(ax, 97, 24, 3.2, 2.4, AMBER))
    p.append(t(s.pad + 3 * (bw + 12), 58, "on match", s.det, DIM))
    p.append(f'<path d="M{ax:.0f} 128 V176" stroke="{RED}" stroke-opacity="0.5" stroke-width="1.5" '
             f'stroke-dasharray="5 4"/>'
             f'<path d="M{ax-4:.0f} 172 l4 6 4 -6z" fill="{RED}" fill-opacity="0.7"/>')
    p.append(t(ax + 12, 156, "on mismatch", s.det, "#8A6F72"))
    p.append(card(s, s.pad + 140, 182, s.inner - 280, 58, RED, 0.55, "#1A0E0E"))
    p.append(t(s.pad + 158, 206, "HALT · KEYS NEVER DERIVED", s.body, RED))
    p.append(t(s.pad + 158, 226, "measurement mismatch → enclave stays sealed, ciphertext only",
               s.det, "#8A6F72"))
    p.append(f'<circle cx="{s.W-s.pad-158}" cy="211" r="4.2" fill="{RED}">{pulse(0.15, 1, 1.4)}</circle>')
    return "\n".join(p + tail(s, h)), h


# ----------------------------------------------------------------------- threat

CLOUD = ["network egress path", "vendor API credentials", "third-party subprocessors",
         "container runtime escape", "orchestrator RBAC", "provider prompt retention",
         "cross-border transfer", "shared-tenancy channels"]
VAULT = ["physical access to the machine", "a cleared insider at the console"]


def threat(s):
    if s.n:
        h = 52 + 30 + len(CLOUD) * 24 + 46 + len(VAULT) * 24 + 62
        p = head(s, h, "Attack surface: cloud AI stack versus Vault-OS", "th")
        p.append(sect(s, 26, "ATTACK SURFACE"))
        p.append(t(s.pad, 56, "TYPICAL CLOUD AI STACK", s.det, RED, ls=1.5))
        p.append(f'<text x="{s.W-s.pad}" y="62" font-family="{MONO}" font-size="30" '
                 f'font-weight="700" fill="{RED}" text-anchor="end" opacity="0">{fade(1.6, 0.5)}8</text>')
        y = 84
        for i, x in enumerate(CLOUD):
            p.append(f'<g opacity="0">{fade(0.15 + i * 0.1)}'
                     f'<rect x="{s.pad}" y="{y+i*24-11}" width="5" height="13" fill="{RED}"/>'
                     f'{t(s.pad+15, y+i*24, x, s.det, "#8A6F72")}</g>')
        y2 = y + len(CLOUD) * 24 + 22
        p.append(f'<line x1="{s.pad}" y1="{y2-20}" x2="{s.W-s.pad}" y2="{y2-20}" stroke="{GRID}" stroke-opacity="0.12"/>')
        p.append(t(s.pad, y2, "VAULT-OS", s.det, GREEN, ls=1.5))
        p.append(f'<text x="{s.W-s.pad}" y="{y2+6}" font-family="{MONO}" font-size="30" '
                 f'font-weight="700" fill="{GREEN}" text-anchor="end" opacity="0">{fade(1.9, 0.5)}2</text>')
        for i, x in enumerate(VAULT):
            p.append(f'<g opacity="0">{fade(1.3 + i * 0.15)}'
                     f'<rect x="{s.pad}" y="{y2+28+i*24-11}" width="5" height="13" fill="{GREEN}"/>'
                     f'{t(s.pad+15, y2+28+i*24, x, s.det, MUTE)}</g>')
        fy = y2 + 28 + len(VAULT) * 24 + 24
        p.append(f'<line x1="{s.pad}" y1="{fy-18}" x2="{s.W-s.pad}" y2="{fy-18}" stroke="{GRID}" stroke-opacity="0.12"/>')
        p.append(t(s.pad, fy, "No exfiltration through a path", s.det, AMBER))
        p.append(t(s.pad, fy + 18, "that was never built.", s.det, AMBER))
        return "\n".join(p + tail(s, h)), h

    h = 340
    p = head(s, h, "Attack surface: cloud AI stack versus Vault-OS", "th")
    p.append(sect(s, 28, "ATTACK SURFACE · WHAT AN ADVERSARY CAN REACH"))
    mid = s.W / 2
    p.append(f'<line x1="{mid}" y1="52" x2="{mid}" y2="{h-64}" stroke="{GRID}" stroke-opacity="0.12"/>')
    p.append(t(s.pad, 62, "TYPICAL CLOUD AI STACK", s.det, RED, ls=1.6))
    p.append(f'<text x="{mid-24}" y="74" font-family="{MONO}" font-size="38" font-weight="700" '
             f'fill="{RED}" text-anchor="end" opacity="0">{fade(1.7, 0.5)}8</text>')
    for i, x in enumerate(CLOUD):
        y = 96 + i * 26
        p.append(f'<g opacity="0">{fade(0.15 + i * 0.11)}'
                 f'<rect x="{s.pad}" y="{y-11}" width="5" height="14" fill="{RED}"/>'
                 f'{t(s.pad+16, y, x, s.body, "#8A6F72")}</g>')
    rx = mid + 26
    p.append(t(rx, 62, "VAULT-OS", s.det, GREEN, ls=1.6))
    p.append(f'<text x="{s.W-s.pad}" y="74" font-family="{MONO}" font-size="38" font-weight="700" '
             f'fill="{GREEN}" text-anchor="end" opacity="0">{fade(1.9, 0.5)}2</text>')
    for i, x in enumerate(VAULT):
        y = 96 + i * 26
        p.append(f'<g opacity="0">{fade(1.3 + i * 0.16)}'
                 f'<rect x="{rx}" y="{y-11}" width="5" height="14" fill="{GREEN}"/>'
                 f'{t(rx+16, y, x, s.body, MUTE)}</g>')
    budget = chars(s.W - s.pad - (rx + 16), s.det)
    note = ["Both are physical, both are auditable, and both already sit "
            "inside your existing security perimeter.",
            "The six that disappear are the six an attacker can reach "
            "without ever entering your building."]
    g = [f'<g opacity="0">{fade(2.2, 0.6)}']
    yy = 168
    for para in note:
        for ln in wrap(para, budget):
            g.append(t(rx + 16, yy, ln, s.det, DIM))
            yy += 18
        yy += 12
    g.append('</g>')
    p.append("".join(g))
    p.append(f'<line x1="{s.pad}" y1="{h-56}" x2="{s.W-s.pad}" y2="{h-56}" stroke="{GRID}" stroke-opacity="0.1"/>')
    p.append(t(s.pad, h - 28, "There is no exfiltration through a path that was never built.", s.body, AMBER))
    return "\n".join(p + tail(s, h)), h


# --------------------------------------------------------------------- pipeline

STAGES = [("INGEST", "documents, audio, images"), ("EMBED", "local model, 768 dims"),
          ("INDEX", "pgvector HNSW + graph"), ("RETRIEVE", "hybrid rank, entity boost"),
          ("CRITIC", "adversarial second pass"), ("GROUNDED", "cited, or refused")]


def pipeline(s):
    if s.n:
        rh = 50
        h = 46 + len(STAGES) * (rh + 12) + 30
        p = head(s, h, "Retrieval pipeline: nothing leaves the enclave", "pl")
        p.append(sect(s, 26, "RETRIEVAL PIPELINE"))
        for i, (nm, sub) in enumerate(STAGES):
            y = 46 + i * (rh + 12)
            col = AMBER if nm == "CRITIC" else GREEN
            p.append(f'<g opacity="0">{fade(0.15 + i * 0.14)}{card(s, s.pad, y, s.inner, rh, col, 0.34)}'
                     f'{t(s.pad+12, y+21, nm, s.body, col if col == AMBER else TEXT)}'
                     f'{t(s.pad+12, y+38, sub, s.det, DIM)}</g>')
            if i < len(STAGES) - 1:
                p.append(f'<path d="M{s.pad+20} {y+rh} v12" stroke="{GREEN}" stroke-opacity="0.5" stroke-width="1.6"/>')
        cy = 46 + 4 * (rh + 12) + rh / 2
        p.append(travel(f"M{s.pad+20} 52 V{46 + 5 * (rh+12) + rh/2:.0f}", 7.0, 0.9, 4.2, GREEN))
        p.append(burst(s.pad + 20, cy, 16, 3.4, 2.6, AMBER))
        return "\n".join(p + tail(s, h)), h

    bw = (s.inner - 5 * 10) / 6
    h = 250
    p = head(s, h, "Retrieval pipeline: ingest, embed, index, retrieve, critic, grounded answer", "pl")
    p.append(sect(s, 28, "RETRIEVAL PIPELINE · NOTHING LEAVES THE ENCLAVE"))
    budget = chars(bw - 20, s.det)
    for i, (nm, sub) in enumerate(STAGES):
        x = s.pad + i * (bw + 10)
        col = AMBER if nm == "CRITIC" else GREEN
        lines = wrap(sub, budget)
        g = [f'<g opacity="0">{fade(0.15 + i * 0.14)}', card(s, x, 62, bw, 74, col, 0.34),
             t(x + 11, 84, nm, s.body, col if col == AMBER else TEXT)]
        for j, ln in enumerate(lines[:3]):
            g.append(t(x + 11, 104 + j * 15, ln, s.det, DIM))
        g.append('</g>')
        p.append("".join(g))
        if i:
            p.append(arrow(x - 10, 99, x - 2, 99, GREEN, 0.5))
    cx = s.pad + 4 * (bw + 10) + bw / 2
    p.append(travel(f"M{s.pad+bw/2:.0f} 99 H{s.pad+5*(bw+10)+bw/2:.0f}", 7.5, 1.0, 4.5, GREEN))
    p.append(burst(cx, 99, 24, 3.4, 2.8, AMBER))
    back_x = s.pad + 3 * (bw + 10) + bw / 2
    p.append(f'<path d="M{cx:.0f} 136 V166 H{back_x:.0f} V136" fill="none" stroke="{AMBER}" '
             f'stroke-opacity="0.45" stroke-width="1.5" stroke-dasharray="5 4"/>'
             f'<path d="M{back_x-4:.0f} 142 l4 -6 4 6z" fill="{AMBER}" fill-opacity="0.7"/>')
    p.append(travel(f"M{cx:.0f} 136 V166 H{back_x:.0f} V136", 3.4, 3.0, 3.4, AMBER))
    p.append(t((cx + back_x) / 2, 184, "rejected → retrieve again", s.det, LINE, anchor="middle"))
    p.append(f'<line x1="{s.pad}" y1="200" x2="{s.W-s.pad}" y2="200" stroke="{GRID}" stroke-opacity="0.1"/>')
    p.append(t(s.pad, 222, "Every stage runs inside the enclave on bundled open weights. No embedding,", s.det, DIM))
    p.append(t(s.pad, 238, "chunk or prompt reaches a model provider, because there is no route to one.", s.det, DIM))
    return "\n".join(p + tail(s, h)), h


BUILDERS = {"header": org_header, "airgap": airgap, "ledger": ledger,
            "bootchain": bootchain, "threat": threat, "pipeline": pipeline}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        for suffix, narrow in (("", False), ("-narrow", True)):
            svg, h = fn(S(narrow))
            path = f"{OUT}/{name}{suffix}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"{path:44} {S(narrow).W}x{h}")
