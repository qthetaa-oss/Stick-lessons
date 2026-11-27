import sys, math, subprocess
sys.path.insert(0, "/home/claude/vid"); sys.path.insert(0, "/home/claude/vid2")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import fnt, W, H, FPS
import bamboo

GOLD = (242, 179, 61); WHITE = (238, 238, 238); GREY = (120, 120, 128); RED = (225, 70, 70)
FLOOR = 1430
SS = 2  # supersample for line art

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)

def base_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 8 + 12 * np.clip(1 - np.sqrt(((xx - 540) / 800) ** 2 + ((yy - 900) / 1000) ** 2), 0, 1)
    im = Image.fromarray(np.stack([v, v, v * 1.05], -1).astype(np.uint8)); d = ImageDraw.Draw(im)
    for x in range(0, W, 26):
        d.line([x, FLOOR, x + 12, FLOOR], fill=(55, 55, 60), width=3)
    return im
BG = base_bg()

def glow(im, cx, cy, r, col, a):
    if a <= 0: return im
    g = Image.new("L", (int(r * 6), int(r * 6)), 0)
    ImageDraw.Draw(g).ellipse([2 * r, 2 * r, 4 * r, 4 * r], fill=int(255 * min(1, a)))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.6))
    lay = Image.new("RGB", g.size, col)
    arr = np.asarray(im).astype(np.int16)
    x0, y0 = int(cx - 3 * r), int(cy - 3 * r)
    sub = Image.new("RGB", (W, H), (0, 0, 0)); sub.paste(lay, (x0, y0), g.point(lambda v: v // 2))
    return Image.fromarray(np.clip(arr + np.asarray(sub), 0, 255).astype(np.uint8))

CAP = {}
def caption(d, parts, y=None, size=None, a=1.0, reveal=1.0):
    CAP["parts"] = parts; CAP["size"] = size or 78; CAP["reveal"] = 1.0

def draw_caption(d, parts, y=260, size=78, a=1.0, reveal=1.0):
    """parts: list of (text, gold?) ; drawn centered on one line"""
    f = fnt("k", size)
    full = "".join(p for p, _ in parts)
    tw = d.textlength(full, font=f)
    if tw > 980:
        f = fnt("k", int(size * 980 / tw)); tw = d.textlength(full, font=f)
    x = 540 - tw / 2
    n = int(len(full) * reveal) + 1
    used = 0
    for p, g in parts:
        seg = p[:max(0, n - used)]; used += len(p)
        col = GOLD if g else WHITE
        d.text((x, y), seg, font=f, fill=tuple(int(c * a) for c in col))
        x += d.textlength(p, font=f)

def fig(img, x, pose=None, scale=0.62, col=None, alpha=1.0):
    pose = pose or {}
    fg, _ = bamboo.figure(rai=pose.get("rai", 0), sad=pose.get("sad", 0), cheer=pose.get("cheer", 0), bob=pose.get("bob", 0),
                          walk=pose.get("walk", 0), look=0)
    fg = fg.resize((int(fg.width * scale), int(fg.height * scale)), Image.LANCZOS)
    if col:  # tint white parts
        a = np.asarray(fg).astype(np.float32)
        m = (a[..., 0] > 128)
        a[m, 0], a[m, 1], a[m, 2] = col
        fg = Image.fromarray(a.astype(np.uint8))
    if alpha < 1:
        fg = fg.copy(); fg.putalpha(fg.split()[3].point(lambda v: int(v * alpha)))
    img = img.convert("RGBA"); img.alpha_composite(fg, (int(x - fg.width / 2), int(FLOOR - fg.height + 12 * scale)))
    return img.convert("RGB")

# ---------- line icons (drawn directly, width w) ----------
def clock(d, cx, cy, r, col, t=0, w=5):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)
    a = t * 2 * math.pi
    d.line([cx, cy, cx + r * 0.75 * math.sin(a), cy - r * 0.75 * math.cos(a)], fill=col, width=w)
    d.line([cx, cy, cx + r * 0.45 * math.sin(a / 12), cy - r * 0.45 * math.cos(a / 12)], fill=col, width=w)

def gear(d, cx, cy, r, col, rot=0, w=5, fill=None):
    pts = []
    for k in range(32):
        ang = rot + k * 2 * math.pi / 32
        rr = r if (k // 2) % 2 == 0 else r * 0.78
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, outline=col, fill=fill, width=w)
    d.ellipse([cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32], outline=col, width=w)

def book(d, cx, cy, s, col, w=5):
    d.polygon([(cx - s, cy - s * 0.6), (cx, cy - s * 0.45), (cx, cy + s * 0.7), (cx - s, cy + s * 0.55)], outline=col, width=w)
    d.polygon([(cx + s, cy - s * 0.6), (cx, cy - s * 0.45), (cx, cy + s * 0.7), (cx + s, cy + s * 0.55)], outline=col, width=w)

def xmark(d, cx, cy, s, col, w=8):
    d.line([cx - s, cy - s, cx + s, cy + s], fill=col, width=w); d.line([cx - s, cy + s, cx + s, cy - s], fill=col, width=w)

def check(d, cx, cy, s, col, w=8):
    d.line([cx - s, cy, cx - s * 0.3, cy + s * 0.7, cx + s, cy - s * 0.7], fill=col, width=w, joint="curve")

def shield(d, cx, cy, s, col, w=6):
    d.polygon([(cx, cy - s), (cx + s * 0.85, cy - s * 0.6), (cx + s * 0.7, cy + s * 0.4), (cx, cy + s), (cx - s * 0.7, cy + s * 0.4), (cx - s * 0.85, cy - s * 0.6)], outline=col, width=w)

def label(d, x, y, text, col=GREY, size=26):
    f = fnt("s", size); tw = d.textlength(text, font=f)
    d.text((x - tw / 2, y), text, font=f, fill=col)

def box(d, x, y, w_, h_, text, col, size=40):
    d.rounded_rectangle([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2], 14, outline=col, width=4)
    f = fnt("k", size); tw = d.textlength(text, font=f)
    d.text((x - tw / 2, y - size * 0.62), text, font=f, fill=col)

# ---------- scenes: (duration, fn(img, u, t) -> img) ----------
def s1(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("YOU DON'T GET PAID FOR ", False), ("HOURS.", True)], reveal=1)
    clock(d, 700, 1100, 90, WHITE, t * 0.8)
    return fig(img, 420, dict(bob=2 * math.sin(t * 2)))

def s2(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("YOU GET PAID FOR ", False), ("SKILLS.", True)], reveal=ease(u * 6))
    img = glow(img, 700, 1100, 120, GOLD, ease(u * 2) * 0.6); d = ImageDraw.Draw(img)
    gear(d, 700, 1100, 95, GOLD, rot=t * 1.2)
    return fig(img, 420, dict(rai=ease(u * 2) * 0.8))

def s3(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("SAME ", False), ("8 HOURS.", True)], reveal=ease(u * 6))
    for x in (330, 750):
        clock(d, x, 980, 60, WHITE, t * 0.8)
        label(d, x, 1060, "8 HOURS")
    img = fig(img, 330, dict(bob=2 * math.sin(t * 2)))
    return fig(img, 750, dict(bob=2 * math.sin(t * 2 + 1)))

def s4(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("DIFFERENT ", False), ("PAY.", True)], reveal=ease(u * 6))
    v1 = int(15 * ease(u * 1.5)); v2 = int(80 * ease(u * 1.5))
    box(d, 330, 1000, 300, 110, f"${v1}/HR", GREY, 52)
    img = glow(img, 750, 1000, 110, GOLD, 0.5); d = ImageDraw.Draw(img)
    box(d, 750, 1000, 300, 110, f"${v2}/HR", GOLD, 52)
    img = fig(img, 330, dict(sad=0.4))
    return fig(img, 750, dict(cheer=ease(u * 2) * 0.6), col=GOLD)

def s5(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("THE DIFFERENCE? ", False), ("ONE SKILL.", True)], reveal=ease(u * 5))
    img = glow(img, 750, 1010, 110, GOLD, 0.7); d = ImageDraw.Draw(img)
    gear(d, 750, 1010, 70, GOLD, rot=t * 1.5)
    gear(d, 330, 1010, 70, (60, 60, 66), rot=0)
    xmark(d, 330, 1010, 30, (80, 80, 86), 6)
    img = fig(img, 330, dict(sad=0.4))
    return fig(img, 750, {}, col=GOLD)

def s6(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("LEARN ", False), ("30 MIN", True), (" A DAY.", False)], reveal=ease(u * 5))
    clock(d, 400, 1020, 70, GOLD, t * 0.5)
    d.pieslice([330, 950, 470, 1090], -90, -90 + 180 * ease(u * 1.5), fill=(90, 66, 20))
    clock(d, 400, 1020, 70, GOLD, t * 0.5)
    book(d, 680, 1030, 70, WHITE)
    return fig(img, 560, dict(rai=0.3 + 0.2 * math.sin(t * 3)))

def s7(img, u, t):
    d = ImageDraw.Draw(img)
    h = int(182 * ease(u * 1.3))
    caption(d, [("1 YEAR = ", False), (f"{h} HOURS.", True)])
    # stacked blocks representing hours
    n = int(18 * ease(u * 1.3))
    for k in range(n):
        y = FLOOR - 40 - k * 32
        d.rectangle([680, y, 820, y + 26], outline=GOLD, width=4)
    return fig(img, 430, dict(walk=t * 6))

def s8(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("THAT'S A ", False), ("NEW SKILL.", True)], reveal=ease(u * 5))
    img = glow(img, 640, 1000, 130, GOLD, 0.6 * ease(u * 2)); d = ImageDraw.Draw(img)
    gear(d, 640, 1000, 90, GOLD, rot=t)
    check(d, 640, 1000, 34, GOLD, 8)
    return fig(img, 380, dict(cheer=ease(u * 2)))

def s9(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("3 YEARS. ", False), ("3 SKILLS.", True)], reveal=ease(u * 5))
    for k, x in enumerate((360, 560, 760)):
        a = ease(u * 3 - k * 0.5)
        if a > 0:
            img = glow(img, x, 980, 80, GOLD, 0.4 * a); d = ImageDraw.Draw(img)
            gear(d, x, 980, 60 * (0.6 + 0.4 * a), GOLD, rot=t * (1 if k % 2 else -1))
            label(d, x, 1065, ["DESIGN", "SALES", "VIDEO"][k], GOLD if a > 0.9 else GREY)
    return img

def s10(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("SKILLS ", False), ("STACK.", True)], reveal=ease(u * 6))
    # staircase of gears, figure climbs
    steps = [(330, FLOOR - 0), (540, FLOOR - 160), (750, FLOOR - 320)]
    for k, (x, y) in enumerate(steps):
        d.rectangle([x - 110, y, x + 110, y + 14], outline=GOLD, width=4)
        gear(d, x, y + 70, 40, (110, 85, 40), rot=t)
    pos = ease(u * 1.2) * 2
    i = min(1, int(pos)); f = pos - i
    x = steps[i][0] + (steps[min(2, i + 1)][0] - steps[i][0]) * f
    y = steps[i][1] + (steps[min(2, i + 1)][1] - steps[i][1]) * f
    fg, _ = bamboo.figure(rai=0, sad=0, cheer=1 if u > 0.85 else 0, bob=0, walk=t * 8 if u < 0.85 else 0, look=0)
    fg = fg.resize((int(fg.width * 0.62), int(fg.height * 0.62)))
    a = np.asarray(fg).astype(np.float32); m = a[..., 0] > 128; a[m, 0], a[m, 1], a[m, 2] = GOLD
    fg = Image.fromarray(a.astype(np.uint8))
    img = img.convert("RGBA"); img.alpha_composite(fg, (int(x - fg.width / 2), int(y - fg.height + 8))); return img.convert("RGB")

def s11(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("A BOSS CAN TAKE ", False), ("YOUR JOB.", False)], reveal=ease(u * 5))
    box(d, 700, 1050, 260, 140, "JOB", WHITE, 56)
    if u > 0.4: xmark(d, 700, 1050, 80, RED, 10)
    return fig(img, 380, dict(sad=ease((u - 0.4) * 3)))

def s12(img, u, t):
    d = ImageDraw.Draw(img); caption(d, [("NOT YOUR ", False), ("SKILLS.", True)], reveal=ease(u * 6))
    img = glow(img, 540, 1050, 160, GOLD, 0.7); d = ImageDraw.Draw(img)
    shield(d, 540, 1050, 130, GOLD, 7)
    gear(d, 540, 1040, 50, GOLD, rot=t)
    return img

def s13(img, u, t):
    d = ImageDraw.Draw(img)
    caption(d, [("START WITH ", False), ("ONE.", True)], y=170, size=80, reveal=ease(u * 4))
    img = glow(img, 540, 1250, 140, GOLD, 0.6 + 0.2 * math.sin(t * 3)); d = ImageDraw.Draw(img)
    gear(d, 540, 900, 80, GOLD, rot=t)
    label(d, 540, 1010, "30 MINUTES. TONIGHT.", GOLD, 34)
    return fig(img, 540, dict(cheer=ease(u * 2)), col=GOLD)

BPM = 128; BEAT = 60 / BPM
BEATS = [3, 3, 3, 4, 3, 3, 4, 3, 4, 5, 3, 3, 7]
SCENES = [(b * BEAT, f) for b, f in zip(BEATS, [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13])]
DUR = sum(d for d, _ in SCENES)

def render(t):
    acc = 0
    for dur, fn in SCENES:
        if t < acc + dur or fn is SCENES[-1][1]:
            u = (t - acc) / dur; CAP.clear(); img = fn(BG.copy(), u, t); break
        acc += dur
    since = t - acc
    idx = [f for _, f in SCENES].index(fn)
    punch = 1 - ease(since / 0.22)
    w, h = img.size; z = 1.5 * (1 + 0.14 * punch) + 0.08 * u
    dirx = 1 if idx % 2 else -1
    cx = 540 + dirx * 140 * punch; cy = 1050 + 20 * math.sin(t * 1.7)
    nw, nh = w / z, h / z
    img = img.crop((int(cx - nw / 2), int(cy - nh / 2), int(cx + nw / 2), int(cy + nh / 2))).resize((w, h), Image.BILINEAR)
    if CAP:
        cs = CAP["size"] * (1 + 0.25 * (1 - ease(since / 0.15)))
        draw_caption(ImageDraw.Draw(img), CAP["parts"], size=int(cs), reveal=1.0)
    if since < 0.05 and acc > 0:
        img = Image.eval(img, lambda v: min(255, int(v * 1.6 + 25)))
    fa = min(1, (DUR - t) / 0.6)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((220 * len(ims), 391)).save("chk_fast.png")
    elif sys.argv[1] == "dur": print(DUR)
    elif sys.argv[1] == "cuts": print(" ".join(f"{sum(d for d, _ in SCENES[:i]):.4f}" for i in range(1, len(SCENES))))
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
