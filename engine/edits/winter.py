import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import skills_fast as sf
from skills_fast import ease, fig, glow, clock, book, xmark, label, W, H, FPS, FLOOR, fnt

ICE = (127, 211, 255); WHITE = (238, 238, 238); GREY = (120, 125, 140); RED = (225, 70, 70); WARM = (255, 190, 110)
sf.GOLD = ICE  # caption highlight colour

def bg(warm=0.0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = np.clip(1 - np.sqrt(((xx - 540) / 800) ** 2 + ((yy - 900) / 1000) ** 2), 0, 1)
    r = 6 + 10 * v + warm * 70 * v; g = 9 + 16 * v + warm * 45 * v; b = 16 + 30 * v + warm * 10 * v
    im = Image.fromarray(np.clip(np.stack([r, g, b], -1), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle([0, FLOOR, W, H], fill=(28, 34, 46))           # snow ground
    d.line([0, FLOOR, W, FLOOR], fill=(150, 175, 200), width=4)
    return im
BG = bg(); BG_WARM = bg(1.0)

CAP = {}
def cap(parts, size=80): CAP["parts"] = parts; CAP["size"] = size

def fig2(img, x, pose=None, scale=0.62, col=None, dy=0):
    pose = pose or {}
    import bamboo
    fg, _ = bamboo.figure(rai=pose.get("rai", 0), sad=pose.get("sad", 0), cheer=pose.get("cheer", 0), bob=0,
                          walk=pose.get("walk", 0), look=0)
    fg = fg.resize((int(fg.width * scale), int(fg.height * scale)), Image.LANCZOS)
    if col:
        a = np.asarray(fg).astype(np.float32); m = a[..., 0] > 128; a[m, 0], a[m, 1], a[m, 2] = col
        fg = Image.fromarray(a.astype(np.uint8))
    img = img.convert("RGBA"); img.alpha_composite(fg, (int(x - fg.width / 2), int(FLOOR - fg.height + 12 * scale - dy)))
    return img.convert("RGB")

def w1(img, u, t):
    cap([("WINTER ", False), ("ARC.", True)], 110)
    img = glow(img, 540, 1150, 160, ICE, 0.45); d = ImageDraw.Draw(img)
    label(d, 540, 1475, "90 DAYS. NO EXCUSES.", ICE, 34)
    return fig2(img, 540, {}, col=None)

def w2(img, u, t):
    cap([("5:00 ", True), ("AM.", False)])
    d = ImageDraw.Draw(img)
    sh = 8 * math.sin(t * 60) if u < 0.6 else 0
    clock(d, 700 + sh, 1060, 80, ICE, 0.42)
    for k in (-1, 1):
        d.arc([700 + k * 60 - 30 + sh, 950, 700 + k * 60 + 30 + sh, 1000], 180, 360, fill=ICE, width=6)
    return fig2(img, 400, dict(rai=ease(u * 2) * 0.7))

def bed(d, x, y, sleeping=True):
    d.rectangle([x - 110, y - 40, x + 110, y], outline=GREY, width=5)
    d.line([x - 110, y, x - 110, y + 30], fill=GREY, width=5); d.line([x + 110, y, x + 110, y + 30], fill=GREY, width=5)
    if sleeping:
        d.ellipse([x - 100, y - 80, x - 50, y - 30], outline=WHITE, width=5)
        d.rounded_rectangle([x - 50, y - 62, x + 104, y - 38], 10, fill=(60, 66, 80))
    return d

def w3(img, u, t):
    cap([("WHILE THEY ", False), ("SLEEP.", True)])
    d = ImageDraw.Draw(img)
    for k, x in enumerate((300, 780)):
        bed(d, x, FLOOR - 30)
        zz = (t * 1.2 + k * 0.5) % 1
        d.text((x - 60 + 30 * zz, FLOOR - 160 - 60 * zz), "z", font=fnt("k", 40), fill=GREY)
    return fig2(img, 540, dict(walk=t * 7), col=ICE)

def w4(img, u, t):
    cap([("TRAIN.", True)], 110)
    lift = 55 * (0.5 - 0.5 * math.cos(t * 7))
    d = ImageDraw.Draw(img)
    d.line([300, FLOOR - 262, 780, FLOOR - 262], fill=WHITE, width=10)
    d.line([310, FLOOR - 262, 310, FLOOR], fill=GREY, width=8); d.line([770, FLOOR - 262, 770, FLOOR], fill=GREY, width=8)
    return fig2(img, 540, dict(cheer=1), dy=70 + lift)

def w5(img, u, t):
    cap([("RUN. ", True), ("IN THE COLD.", False)])
    d = ImageDraw.Draw(img)
    x = 180 + 720 * u
    for k in range(int(u * 12)):
        fx = 180 + k * 60; d.ellipse([fx - 10, FLOOR + 14 + (k % 2) * 16, fx + 10, FLOOR + 22 + (k % 2) * 16], fill=(90, 110, 140))
    return fig2(img, x, dict(walk=t * 14))

def w6(img, u, t):
    cap([("READ.", True)], 110)
    d = ImageDraw.Draw(img); book(d, 700, 1080, 80, ICE)
    return fig2(img, 400, dict(rai=0.4))

def phone(d, x, y, col):
    d.rounded_rectangle([x - 55, y - 100, x + 55, y + 100], 16, outline=col, width=6)
    d.line([x - 15, y + 80, x + 15, y + 80], fill=col, width=5)

def w7(img, u, t):
    cap([("NO ", False), ("PHONE.", True)])
    d = ImageDraw.Draw(img); phone(d, 700, 1060, WHITE)
    if u > 0.25: xmark(d, 700, 1060, 90, RED, 12)
    return fig2(img, 400, {})

def w8(img, u, t):
    cap([("EAT ", False), ("CLEAN.", True)])
    d = ImageDraw.Draw(img)
    d.ellipse([590, 1010, 810, 1110], outline=ICE, width=6); d.ellipse([630, 1030, 770, 1090], outline=ICE, width=4)
    d.line([560, 990, 560, 1120], fill=WHITE, width=6); d.line([840, 990, 840, 1120], fill=WHITE, width=6)
    return fig2(img, 380, dict(rai=0.3))

def w9(img, u, t):
    day = 1 + int(89 * ease(u * 1.1))
    cap([("DAY ", False), (f"{day}", True)], 120)
    d = ImageDraw.Draw(img)
    for k in range(90):
        x = 210 + (k % 15) * 45; y = 900 + (k // 15) * 45
        d.rectangle([x, y, x + 32, y + 32], fill=ICE if k < day else (36, 44, 58))
    return img

def w10(img, u, t):
    cap([("COLD. DARK. ", False), ("TIRED.", True)])
    img = fig2(img, 540, dict(sad=ease(u * 2)))
    d = ImageDraw.Draw(img)
    d.rectangle([380, FLOOR - 20 * u, 700, FLOOR], fill=(220, 230, 240))
    return img

def w11(img, u, t):
    cap([("DO IT ", False), ("ANYWAY.", True)], 96)
    return fig2(img, 300 + 480 * u, dict(walk=t * 12), col=ICE)

def w12(img, u, t):
    cap([("MARCH 1: ", False), ("NEW YOU.", True)], 92)
    img = glow(img, 540, 1150, 200, WARM, 0.5 + 0.2 * math.sin(t * 3))
    img = glow(img, 540, 1150, 120, ICE, 0.5)
    d = ImageDraw.Draw(img)
    label(d, 540, 1475, "START YOUR WINTER ARC TODAY.", WHITE, 34)
    return fig2(img, 540, dict(cheer=ease(u * 2.5)), col=ICE)

BPM = 128; BEAT = 60 / BPM
PLAN = [(4, w1), (3, w2), (3, w3), (3, w4), (3, w5), (3, w6), (3, w7), (3, w8), (4, w9), (3, w10), (3, w11), (7, w12)]
SCENES = [(b * BEAT, f) for b, f in PLAN]
DUR = sum(d for d, _ in SCENES)

FLAKES = np.random.default_rng(4).uniform(0, 1, (220, 4))
def snow(img, t, amount=1.0):
    d = ImageDraw.Draw(img)
    for k, (x, y, s, ph) in enumerate(FLAKES[: int(220 * amount)]):
        sp = 120 + 260 * s
        yy = (y * H + t * sp) % H; xx = (x * W + 40 * math.sin(t * 0.8 + ph * 6)) % W
        r = 3 + 6 * s
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(220, 232, 245))
    return img

def render(t):
    acc = 0
    for i, (dur, fn) in enumerate(SCENES):
        if t < acc + dur or i == len(SCENES) - 1:
            u = (t - acc) / dur; CAP.clear()
            base = BG_WARM if fn is w12 else BG
            img = fn(base.copy(), u, t); idx = i; break
        acc += dur
    since = t - acc
    punch = 1 - ease(since / 0.22)
    z = 1.5 * (1 + 0.14 * punch) + 0.08 * u
    dirx = 1 if idx % 2 else -1
    cx = 540 + dirx * 140 * punch; cy = 1050 + 20 * math.sin(t * 1.7)
    nw, nh = W / z, H / z
    img = img.crop((int(cx - nw / 2), int(cy - nh / 2), int(cx + nw / 2), int(cy + nh / 2))).resize((W, H), Image.BILINEAR)
    img = snow(img, t, 0.2 if fn is w12 else (0.75 if fn in (w9, w10) else 0.4))
    if CAP:
        cs = CAP["size"] * (1 + 0.25 * (1 - ease(since / 0.15)))
        sf.draw_caption(ImageDraw.Draw(img), CAP["parts"], size=int(cs), reveal=1.0)
    if since < 0.05 and acc > 0:
        img = Image.eval(img, lambda v: min(255, int(v * 1.5 + 25)))
    fa = min(1, (DUR - t) / 0.6)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((200 * len(ims), 356)).save("chk_winter.png")
    elif sys.argv[1] == "dur": print(DUR)
    elif sys.argv[1] == "cuts": print(" ".join(f"{sum(d for d, _ in SCENES[:i]):.4f}" for i in range(1, len(SCENES))))
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
