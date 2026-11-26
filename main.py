#!/usr/bin/env python3
"""Draw a 1024x1024 summary image of 26 November 2026 world news.

Pure Python standard library only: a hand-rolled PNG encoder and a 5x7
bitmap font. No network, no clock, no randomness: two runs write the
same bytes. Writes to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Layout: a dark wire-desk board. A gold-ruled masthead names the day;
a lead panel, two right-column panels and two middle panels carry the
day's stories from a data table; a ticker strip and a footer separate
the day's news from earlier reports.
"""

import os
import struct
import zlib
from math import atan2, degrees, hypot

W, H = 1024, 1024

BG = (15, 27, 45)
PANEL = (23, 41, 63)
BORDER = (51, 80, 122)
GOLD = (232, 180, 74)
WHITE = (245, 241, 232)
MUTED = (159, 176, 195)
RED = (217, 79, 61)
TEAL = (63, 167, 160)
DARK = (10, 18, 30)

# 5x7 bitmap font: 7 rows of 5 bits per glyph. All copy is uppercase.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "10001", "11001", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "—": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    "•": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def hline(self, x0, x1, y, color, thick=1):
        x0, x1, y = int(round(x0)), int(round(x1)), int(round(y))
        for t in range(thick):
            for x in range(x0, x1 + 1):
                self.set(x, y + t, color)

    def vline(self, x, y0, y1, color, thick=1):
        x, y0, y1 = int(round(x)), int(round(y0)), int(round(y1))
        for t in range(thick):
            for y in range(y0, y1 + 1):
                self.set(x + t, y, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err, x, y = dx - dy, x0, y0
        while True:
            for t in range(thick):
                self.set(x + t, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def rect(self, x, y, w, h, color):
        x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def outline(self, x, y, w, h, color, thick=1):
        x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        for t in range(thick):
            self.hline(x + t, x + w - 1 - t, y + t, color)
            self.hline(x + t, x + w - 1 - t, y + h - 1 - t, color)
            self.vline(x + t, y + t, y + h - 1 - t, color)
            self.vline(x + w - 1 - t, y + t, y + h - 1 - t, color)

    def circle(self, cx, cy, r, color, fill=False):
        cx, cy, r = int(round(cx)), int(round(cy)), int(round(r))
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            pts = [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                   (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                   (cx + y, cy - x), (cx - y, cy - x)]
            if fill:
                for yy in (cy + y, cy - y):
                    self.hline(cx - x, cx + x, yy, color)
                for yy in (cy + x, cy - x):
                    self.hline(cx - y, cx + y, yy, color)
            else:
                for px, py in pts:
                    self.set(px, py, color)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def fill_poly(self, points, color):
        points = [(int(round(px)), int(round(py))) for px, py in points]
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, color)

    def trefoil(self, cx, cy, r, color):
        # Radiation trefoil: centre disc + three 60-degree blades.
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                dx, dy = x - cx, y - cy
                dist = hypot(dx, dy)
                if dist <= r * 0.30:
                    self.set(x, y, color)
                elif r * 0.36 <= dist <= r:
                    ang = degrees(atan2(-dy, dx)) % 360
                    if min(abs(ang - c) for c in (90, 210, 330)) <= 30:
                        self.set(x, y, color)
        self.circle(cx, cy, r, color)

    def text(self, x, y, s, scale, color, spacing=1):
        adv = (5 + spacing) * scale
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += adv
        return cx - spacing * scale - x

    def text_width(self, s, scale, spacing=1):
        if not s:
            return 0
        return len(s) * (5 + spacing) * scale - spacing * scale

    def wrap(self, s, scale, max_w, spacing=1):
        words, lines, cur = s.split(" "), [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale, spacing) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, max_w, color, leading=6, spacing=1):
        lines = self.wrap(s, scale, max_w, spacing)
        lh = 7 * scale + leading
        for i, line in enumerate(lines):
            self.text(x, y + i * lh, line, scale, color, spacing)
        return len(lines)


def encode_png(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def draw_chip(cv, cx, cy, s, color):
    cv.outline(cx - s, cy - s, 2 * s, 2 * s, color, 3)
    cv.outline(cx - s // 2, cy - s // 2, s, s, color, 3)
    for i in (-1, 0, 1):
        off = i * (2 * s // 3)
        cv.rect(cx + off - 2, cy - s - 10, 5, 10, color)
        cv.rect(cx + off - 2, cy + s, 5, 10, color)
        cv.rect(cx - s - 10, cy + off - 2, 10, 5, color)
        cv.rect(cx + s, cy + off - 2, 10, 5, color)
    cv.rect(cx - 3, cy - 3, 7, 7, color)


def draw_chart(cv, cx, cy, s, color):
    cv.vline(cx - s, cy - s, cy + s, color, 3)
    cv.hline(cx - s, cx + s, cy + s, color, 3)
    pts = [(cx - s, cy - s * 0.55), (cx - s // 3, cy - s * 0.25),
           (cx + s // 3, cy + s * 0.1), (cx + s, cy + s * 0.75)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], color, 4)
    for px, py in pts:
        cv.circle(px, py, 5, color, fill=True)
    cv.fill_poly([(cx + s, cy + s * 0.75), (cx + s - 14, cy + s * 0.75 - 4),
                  (cx + s - 6, cy + s * 0.75 + 12)], color)


ICONS = {"chip": draw_chip, "chart": draw_chart}


# Story panels, all first reported Thursday 26 November 2026.
# head: headline lines (already split to fit); body: wrapped caption.
PANELS = [
    dict(x=616, y=132, w=380, h=180, border=BORDER,
         tag=("UKRAINE WAR", TEAL), tag_xy=(636, 148),
         head=["TWO GRAIN SHIPS", "HIT OFF ODESA"], head_xy=(636, 172),
         body="UKRAINE SAID RUSSIA STRUCK TWO FOREIGN GRAIN SHIPS "
              "OVERNIGHT NEAR ODESA.",
         body_xy=(636, 240), body_w=340, icon=None),
    dict(x=616, y=328, w=380, h=184, border=BORDER,
         tag=("FRANCE", GOLD), tag_xy=(636, 344),
         head=["BARDELLA FACES", "NEW CLAIMS"], head_xy=(636, 368),
         body="FRENCH MEDIA PUBLISHED FRESH CLAIMS OF PAST ANTISEMITIC "
              "REMARKS BY THE FAR-RIGHT LEADER.",
         body_xy=(636, 436), body_w=340, icon=None),
    dict(x=28, y=528, w=476, h=260, border=BORDER,
         tag=None, head=["AI FIRM'S USER", "DATA ACCESSED"],
         head_xy=(150, 566),
         body="A RESEARCHER NAMED CHINA'S MINIMAX AS THE AI FIRM WHOSE "
              "USER DATA WAS ACCESSED BY UNIDENTIFIED PARTIES. "
              "REPORTED THURSDAY.",
         body_xy=(48, 656), body_w=420,
         icon=("chip", 100, 600, 30, TEAL)),
    dict(x=520, y=528, w=476, h=260, border=BORDER,
         tag=None, head=["AI SELL-OFF", "HITS NASDAQ"],
         head_xy=(652, 566),
         body="STOCKS SLID AGAIN AS AI SHARES FELL; S&P WARNED NVIDIA'S "
              "BOARD MAY BE COMPROMISED. MARKETS, THURSDAY.",
         body_xy=(540, 656), body_w=420,
         icon=("chart", 592, 600, 30, RED)),
]


def story_panel(cv, spec):
    cv.rect(spec["x"], spec["y"], spec["w"], spec["h"], PANEL)
    cv.outline(spec["x"], spec["y"], spec["w"], spec["h"],
               spec["border"], 2)
    if spec["tag"]:
        tx, ty = spec["tag_xy"]
        cv.text(tx, ty, spec["tag"][0], 2, spec["tag"][1], spacing=2)
    if spec["icon"]:
        name, cx, cy, s, color = spec["icon"]
        ICONS[name](cv, cx, cy, s, color)
    hx, hy = spec["head_xy"]
    for i, line in enumerate(spec["head"]):
        cv.text(hx, hy + i * 28, line, 3, WHITE)
    bx, by = spec["body_xy"]
    cv.para(bx, by, spec["body"], 2, spec["body_w"], MUTED, leading=5)


def render():
    cv = Canvas(W, H, BG)
    # Dot grid texture.
    for gy in range(24, H, 32):
        for gx in range(24, W, 32):
            cv.set(gx, gy, (22, 38, 62))
    cv.outline(8, 8, W - 16, H - 16, BORDER, 2)

    # Masthead: the day, named in full.
    cv.text(28, 30, "THE WORLD IN ONE IMAGE", 2, GOLD, spacing=2)
    cv.text(28, 56, "THURSDAY 26 NOVEMBER 2026", 6, WHITE)
    cv.hline(28, 996, 116, GOLD, 3)

    # Lead panel: Kim / tactical nuclear weapons, reported by KCNA.
    cv.rect(28, 132, 572, 380, PANEL)
    cv.outline(28, 132, 572, 380, GOLD, 3)
    cv.text(48, 150, "LEAD STORY", 2, RED, spacing=2)
    cv.text(48, 180, "KIM ORDERS TACTICAL", 4, WHITE)
    cv.text(48, 224, "NUCLEAR PUSH", 4, WHITE)
    cv.trefoil(128, 392, 66, GOLD)
    cv.para(232, 292, "KCNA: KIM ORDERED TACTICAL NUCLEAR ARMS SPREAD "
            "OVER LAND, SEA AND AIR, AND OUTPUT EXPANDED.", 3, 360,
            MUTED, leading=8)
    cv.text(232, 452, "REPORTED THURSDAY BY KCNA", 2, GOLD, spacing=1)

    for spec in PANELS:
        story_panel(cv, spec)

    # Ticker strip: more of the same day.
    cv.rect(28, 804, 968, 100, DARK)
    cv.outline(28, 804, 968, 100, BORDER, 2)
    cv.text(48, 818, "ALSO ON 26 NOVEMBER", 2, GOLD, spacing=2)
    cv.para(48, 846, "NEARLY 2000 MIGRANTS REACH THE CANARY ISLANDS "
            "IN A DAY  •  INDIA ASKS NETFLIX NOT TO AIR A PAKISTANI "
            "SHOW  •  DURAN DURAN GUITARIST ANDY TAYLOR DIES AT 65",
            2, 928, WHITE, leading=5)

    # Footer: earlier news, kept out of the main content.
    cv.text(28, 922, "REPORTED EARLIER — NOT 26 NOVEMBER NEWS:", 2,
            MUTED, spacing=1)
    cv.para(28, 948, "US TARIFFS ON 14 PARTNERS (25 NOV)  •  HORMUZ "
            "MINE CLAIMS (25 NOV)  •  CAIRO TANKER FIRE (25 NOV)  •  "
            "SHENZHOU-24 LAUNCH (25 NOV)  •  SAVASLEYKA AIRBASE "
            "CLAIM (25 NOV)", 2, 968, MUTED, leading=4)
    cv.text(28, 986, "SOURCES: REUTERS, AP, KCNA, MEDIAPART / LE MONDE",
            2, MUTED, spacing=1)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(encode_png(render()))


if __name__ == "__main__":
    main()
