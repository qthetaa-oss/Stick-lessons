import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 45.0
SS = 3  # supersampling for sprites

F = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(F + name, size)
FONT_CACHE = {}
def fnt(weight, size):
    k = (weight, size)
    if k not in FONT_CACHE:
        FONT_CACHE[k] = font({"b": "Inter-Bold.otf", "s": "Inter-SemiBold.otf", "m": "Inter-Medium.otf", "k": "Inter-Black.otf"}[weight], size)
    return FONT_CACHE[k]

WHITE = (240, 240, 242)
GREY = (150, 150, 158)
DIM = (95, 95, 102)
GREEN = (57, 229, 140)
RED = (235, 72, 72)

FLOORS = [840, 1200, 1560]
NAMES = ["SPENDER", "SAVER", "INVESTOR"]
SUB = ["SPENT EVERYTHING", "SAVINGS ACCOUNT  2%", "INDEX FUND  ~7%"]
FIG_X = 230
STACK_X = 500  # center
STACK_W = 170
NUM_X = 640

# ---------------- money model ----------------
inv = [0.0]; sav = [0.0]
r, s = 0.07 / 12, 0.02 / 12
a = b = 0.0
for m in range(1, 241):
    a += 100; b += 100
    if 85 <= m <= 90: a *= 0.96
    elif 91 <= m <= 102: a *= 1.018
    else: a *= 1 + r
    b *= 1 + s
    inv.append(a); sav.append(b)

def interp(arr, m):
    m = max(0.0, min(240.0, m)); i = int(m)
    if i >= 240: return arr[240]
    f = m - i
    return arr[i] * (1 - f) + arr[i + 1] * f

# bill events (months 1..24)
EVENTS = []
for k in range(1, 25):
    if k <= 12:
        te = 2.5 + (k - 1) * 0.75; d = 0.55
    else:
        te = 11.5 + (k - 13) * 0.29; d = 0.27
    EVENTS.append((k, te, d))

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def ease_in(x): x = max(0, min(1, x)); return x * x * x

def months(t):
    if t < 15.0:
        return float(sum(1 for k, te, d in EVENTS if te + d <= t))
    if t < 19.0: return 24 + 36 * ease((t - 15) / 4)
    if t < 21.5: return 60.0
    if t < 24.5: return 60 + 24 * ease((t - 21.5) / 3)
    if t < 28.5: return 84 + 8 * ((t - 24.5) / 4.0)
    if t < 33.5: return 92 + 148 * ease_in((t - 28.5) / 5.0) ** 0.75
    return 240.0

# ---------------- background ----------------
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.full((H, W), 11.0, np.float32)
    # top spotlight
    d = np.sqrt(((xx - 540) / 620) ** 2 + ((yy - 380) / 520) ** 2)
    base += 26 * np.clip(1 - d, 0, 1) ** 1.6
    # floor pools per row
    for fy in FLOORS:
        d = np.sqrt(((xx - 520) / 520) ** 2 + ((yy - (fy - 120)) / 210) ** 2)
        base += 16 * np.clip(1 - d, 0, 1) ** 1.4
    # vignette
    v = np.sqrt(((xx - 540) / 760) ** 2 + ((yy - 960) / 1150) ** 2)
    base *= np.clip(1.25 - v * 0.75, 0.35, 1)
    img = np.stack([base, base, base * 1.06], -1)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    for fy in FLOORS:
        dr.rectangle([70, fy, 1010, fy + 20], fill=(24, 24, 28))
        dr.rectangle([70, fy, 1010, fy + 3], fill=(48, 48, 54))
        dr.rectangle([70, fy + 20, 1010, fy + 32], fill=(15, 15, 18))
    return im

BG = make_bg()

# ---------------- helpers ----------------
def tracked(draw, xy, text, f, fill, track=0.12, anchor="l", reveal=None):
    """draw tracked caps text; anchor l / c."""
    sp = f.size * track
    widths = [f.getlength(c) for c in text]
    total = sum(widths) + sp * (len(text) - 1)
    x, y = xy
    if anchor == "c": x -= total / 2
    n = len(text) if reveal is None else reveal
    for i, c in enumerate(text[:n]):
        draw.text((x, y), c, font=f, fill=fill)
        x += widths[i] + sp
    return total

def with_alpha(col, a):
    return tuple(int(c * a + 11 * (1 - a)) for c in col)

def lerp(p, q, f): return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)

def figure_sprite(pose):
    """pose: dict raise(0-1 right arm), sad(0-1), cheer(0-1), bob(px). returns RGBA, anchor bottom-center"""
    w, h = 300, 360
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = w / 2, h - 20
    sad, cheer, rai, bob = pose.get("sad", 0), pose.get("cheer", 0), pose.get("raise", 0), pose.get("bob", 0)
    hip = (0, -110 + bob * 0.5)
    neck = (sad * 14, -200 + bob + sad * 12)
    head = (sad * 26, -240 + bob + sad * 30)
    sh = (neck[0], neck[1] + 8)
    # arms
    lhand = lerp((-40, -112 + bob), (-56, -260 + bob), cheer)
    lelb = lerp((-30, -155 + bob), (-48, -230 + bob), cheer)
    rh_idle = (40, -112 + bob)
    rh_up = (70, -250 + bob)
    rhand = lerp(lerp(rh_idle, rh_up, rai), (56, -260 + bob), cheer)
    relb = lerp(lerp((30, -155 + bob), (58, -190 + bob), rai), (48, -230 + bob), cheer)
    if sad:
        lhand = lerp(lhand, (-14 + sad * 10, -104 + bob), sad)
        rhand = lerp(rhand, (34 + sad * 10, -104 + bob), sad)
    segs = [
        [hip, (-14, -55), (-30, 0)], [hip, (14, -55), (30, 0)],
        [hip, neck], [sh, lelb, lhand], [sh, relb, rhand],
    ]
    def P(p): return ((ox + p[0]) * SS, (oy + p[1]) * SS)
    for wdt, col in ((30, (10, 10, 12, 255)), (18, (242, 242, 244, 255))):
        for sg in segs:
            pts = [P(p) for p in sg]
            d.line(pts, fill=col, width=wdt * SS, joint="curve")
            for p in (pts[0], pts[-1]):
                rr = wdt * SS / 2
                d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=col)
    hc = P(head); R = 34 * SS
    d.ellipse([hc[0] - R - 6 * SS, hc[1] - R - 6 * SS, hc[0] + R + 6 * SS, hc[1] + R + 6 * SS], fill=(10, 10, 12, 255))
    d.ellipse([hc[0] - R, hc[1] - R, hc[0] + R, hc[1] + R], fill=(246, 246, 248, 255))
    return im.resize((w, h), Image.LANCZOS)

FIG_CACHE = {}
def figure(pose):
    k = tuple(round(pose.get(x, 0), 2) for x in ("raise", "sad", "cheer", "bob"))
    if k not in FIG_CACHE:
        if len(FIG_CACHE) > 4000: FIG_CACHE.clear()
        FIG_CACHE[k] = figure_sprite(dict(zip(("raise", "sad", "cheer", "bob"), k)))
    return FIG_CACHE[k]

def bill_sprite():
    w, h = 170, 76
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2 * SS, 2 * SS, (w - 2) * SS, (h - 2) * SS], 10 * SS, fill=(10, 10, 12, 255))
    d.rounded_rectangle([7 * SS, 7 * SS, (w - 7) * SS, (h - 7) * SS], 6 * SS, fill=(226, 236, 228, 255))
    d.rounded_rectangle([15 * SS, 15 * SS, (w - 15) * SS, (h - 15) * SS], 4 * SS, outline=(150, 170, 155, 255), width=2 * SS)
    cx, cy, R = w / 2 * SS, h / 2 * SS, 21 * SS
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(40, 60, 48, 255))
    f = fnt("b", 30 * SS)
    d.text((cx, cy), "$", font=f, fill=(226, 236, 228, 255), anchor="mm")
    return im.resize((w, h), Image.LANCZOS)
BILL = bill_sprite()

def draw_stack(img, dr, cx, floor, hpx, col, line_col, glow=0.0, shake=0):
    if hpx < 1: return
    x0, x1 = cx - STACK_W / 2 + shake, cx + STACK_W / 2 + shake
    top = floor - hpx
    if glow > 0:
        pad = 80
        box = (int(x0 - pad), int(top - pad), int(x1 + pad), int(floor + 10))
        layer = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
        ImageDraw.Draw(layer).rectangle([pad, pad, pad + STACK_W, pad + hpx], fill=int(255 * glow))
        layer = layer.filter(ImageFilter.GaussianBlur(34))
        region = img.crop(box)
        colimg = Image.new("RGB", region.size, col)
        region = Image.composite(colimg, region, layer.point(lambda v: v * 0.55))
        img.paste(region, box[:2])
    dr.rectangle([x0 - 4, top - 4, x1 + 4, floor], fill=(10, 10, 12))
    dr.rectangle([x0, top, x1, floor], fill=col)
    y = floor - 7
    while y > top + 3:
        dr.line([x0 + 6, y, x1 - 6, y], fill=line_col, width=2)
        y -= 7
    dr.rectangle([x0, top, x1, top + 3], fill=tuple(min(255, c + 25) for c in col))

def money(v): return "${:,.0f}".format(v)

CAPTIONS = [
    # t0, t1, y, text, size, color, weight
    (0.3, 21.0, 180, "THREE PEOPLE.", 42, WHITE, "s"),
    (1.1, 21.0, 238, "$100 LEFT OVER EVERY MONTH.", 42, WHITE, "s"),
    (19.0, 24.3, 300, "AFTER 5 YEARS: ALMOST NO DIFFERENCE.", 34, GREY, "s"),
    (24.6, 30.0, 180, "YEAR 8: THE MARKET CRASHES.", 42, RED, "s"),
    (25.9, 30.0, 238, "THE INVESTOR DOESN'T SELL.", 42, WHITE, "s"),
    (30.3, 33.8, 180, "THEN COMPOUNDING TAKES OVER.", 42, GREEN, "s"),
    (34.2, 99, 160, "SAME $100. SAME 20 YEARS.", 42, WHITE, "s"),
    (36.8, 99, 218, "ONLY ONE PUT IT TO WORK.", 42, WHITE, "s"),
    (39.8, 99, 285, "START TODAY.", 70, GREEN, "k"),
]

def render(t):
    img = BG.copy()
    dr = ImageDraw.Draw(img)
    m = months(t)
    final = ease((t - 34.0) / 1.2)

    # captions
    for t0, t1, y, text, size, col, wt in CAPTIONS:
        if t0 <= t < t1:
            a = min(1, (t - t0) / 0.25, (t1 - t) / 0.3)
            rev = int((t - t0) * 34) + 1
            tracked(dr, (540, y), text, fnt(wt, size), with_alpha(col, a), track=0.1, anchor="c", reveal=min(len(text), rev))

    # counter
    year = min(20, int(m // 12) + 1)
    ctop = 392
    label = f"YEAR {year}"
    if t < 15: label += f"   ·   MONTH {int(m % 12) + 1 if m < 24 else 12}"
    tracked(dr, (540, ctop), label, fnt("s", 30), GREY, track=0.18, anchor="c")
    seg_w, gap = 34, 6
    x = 540 - (20 * seg_w + 19 * gap) / 2
    filled = m / 12
    for i in range(20):
        f = max(0, min(1, filled - i))
        dr.rectangle([x, ctop + 52, x + seg_w, ctop + 58], fill=(38, 38, 44))
        if f > 0:
            dr.rectangle([x, ctop + 52, x + seg_w * f, ctop + 58], fill=GREEN if i >= 0 and f >= 1 else (120, 200, 160))
        x += seg_w + gap

    # scale
    cur_max = max(interp(inv, m), interp(sav, m), 6000)
    scale = 250 / cur_max

    crash = 1.0 if 84.5 <= m <= 90.5 and t < 30 else 0.0
    shake = int(4 * math.sin(t * 60)) if crash else 0

    vals = [0.0, interp(sav, m), interp(inv, m)]
    for i, fy in enumerate(FLOORS):
        # label
        lc = GREEN if i == 2 else GREY
        tracked(dr, (FIG_X - 2, fy - 312), NAMES[i], fnt("s", 24), lc, track=0.2, anchor="c")
        # stack
        if i == 1:
            draw_stack(img, dr, STACK_X, fy, vals[1] * scale, (196, 198, 204), (150, 152, 160))
        if i == 2:
            col = GREEN if not crash else (215, 90, 80)
            lcol = (30, 150, 90) if not crash else (150, 50, 45)
            glow = 0.35 + 0.65 * final * (0.8 + 0.2 * math.sin(t * 3))
            draw_stack(img, dr, STACK_X, fy, vals[2] * scale, col, lcol, glow=glow, shake=shake)
        # number
        if i == 0:
            dr.text((NUM_X, fy - 190), "$0", font=fnt("b", 66), fill=with_alpha(WHITE, 0.55))
            tracked(dr, (NUM_X + 2, fy - 105), "SPENT " + money(100 * m), fnt("m", 22), RED if m > 0 else GREY, track=0.12)
        else:
            col = WHITE if i == 1 else (GREEN if not crash else RED)
            dr.text((NUM_X, fy - 190), money(vals[i]), font=fnt("b", 66), fill=col)
            tracked(dr, (NUM_X + 2, fy - 105), SUB[i], fnt("m", 22), GREY, track=0.12)

    # bills & figures
    raise_amt = [0, 0, 0]
    for k, te, d in EVENTS:
        if te - 0.15 <= t <= te + d + 0.2:
            p = (t - te) / d
            for i, fy in enumerate(FLOORS):
                if i == 0:
                    raise_amt[0] = max(raise_amt[0], ease(1 - abs(p - 0.9) * 2.2))
                    if p < 1:
                        x0, y0 = FIG_X + 40, fy - 420
                        tx, ty = FIG_X + 60, fy - 270
                        x = x0 + (tx - x0) * ease(p); y = y0 + (ty - y0) * ease(p) ** 1.5
                        if p > 0: img.alpha_composite if False else img.paste(BILL, (int(x - 85), int(y - 38)), BILL)
                else:
                    if 0 < p < 1:
                        top = fy - vals[i] * scale
                        x, y0 = STACK_X, fy - 440
                        y = y0 + (top - 38 - y0) * (ease(p) ** 1.6)
                        img.paste(BILL, (int(x - 85), int(y - 38)), BILL)
        # spender: bill flies away after landing
        p2 = (t - te - d) / 0.7
        if 0 <= p2 <= 1:
            fy = FLOORS[0]
            x = FIG_X + 60 + 520 * ease(p2); y = fy - 270 - 120 * math.sin(p2 * math.pi) * 0.6
            a = 1 - p2
            if p2 < 0.75:
                b = BILL.copy(); al = b.split()[3].point(lambda v: int(v * (1 - p2 / 0.75)))
                b.putalpha(al)
                b = b.rotate(-30 * p2, expand=True, resample=Image.BICUBIC)
                img.paste(b, (int(x - b.width / 2), int(y - b.height / 2)), b)
            tracked(dr, (FIG_X + 120, fy - 330 - 50 * p2), "-$100", fnt("b", 34), with_alpha(RED, a), track=0.05)
    # yearly spending floats in fast phase
    if t >= 15 and t < 33.6:
        for yv in range(3, 21):
            mt = yv * 12 - 12  # month where year begins
            # find time when m crossed mt: approximate by sampling
            pass
    if 15 <= t < 33.6:
        frac = (m / 12) % 1.0
        a = 1 - frac
        if m < 239:
            tracked(dr, (FIG_X + 120, FLOORS[0] - 330 - 50 * frac), "-$1,200", fnt("b", 34), with_alpha(RED, a * 0.9), track=0.05)

    bob = 3 * math.sin(t * 2.2)
    poses = [
        {"raise": raise_amt[0], "sad": final, "bob": bob},
        {"raise": 0, "bob": bob * 0.8},
        {"raise": 0, "cheer": final * ease((t - 34.5) / 1.0), "bob": bob * 0.9},
    ]
    img = img.convert("RGBA")
    for i, fy in enumerate(FLOORS):
        fg = figure(poses[i])
        img.alpha_composite(fg, (int(FIG_X - fg.width / 2), int(fy - fg.height + 20)))
    img = img.convert("RGB")
    dr = ImageDraw.Draw(img)

    # disclaimer
    if t > 40.5:
        a = min(1, (t - 40.5) / 0.6)
        tracked(dr, (540, 1700), "ILLUSTRATION ONLY. ASSUMES 2% INTEREST / ~7% AVG. RETURN.", fnt("m", 19), with_alpha(DIM, a), track=0.08, anchor="c")
        tracked(dr, (540, 1730), "NOT FINANCIAL ADVICE.", fnt("m", 19), with_alpha(DIM, a), track=0.08, anchor="c")

    # fade in / out
    fa = min(1, t / 0.4, (DUR - t) / 0.6)
    if fa < 1:
        img = Image.eval(img, lambda v: int(v * fa))
    return img

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for tt in sys.argv[2:]:
            render(float(tt)).save(f"still_{tt}.png")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        n0, n1 = round(t0 * FPS), round(t1 * FPS)
        for n in range(n0, n1):
            p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
