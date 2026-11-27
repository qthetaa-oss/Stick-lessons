import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(F + n, s)
LIGHT = lambda s: font("Inter-Light.otf", s)
MED = lambda s: font("Inter-Medium.otf", s)
SEMI = lambda s: font("Inter-SemiBold.otf", s)

def ease(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.6, fo=0.6):
    if t < a or t > b: return 0.0
    return min(1, (t - a) / fi, (b - t) / fo)

# ---- data ----
COLS, ROWS = 52, 80
N = COLS * ROWS                      # 4160 weeks = 80 years
GONE = 30 * 52                       # 1560
rng = np.random.default_rng(12)
rest = rng.permutation(np.arange(GONE, N))
SLEEP = rest[:867]; WORK = rest[867:867 + 405]; CHORES = rest[1272:1272 + 326]
FREE = rest[1598:]                   # 1002
PHONE = FREE[:217]
order_rank = np.zeros(N); order_rank[rest] = np.arange(len(rest)) / len(rest)

GX0, GY0, STEP = 150, 470, 15.0
pos = np.array([(GX0 + (i % COLS) * STEP, GY0 + (i // COLS) * STEP) for i in range(N)])
cat = np.zeros(N, int)               # 0 free/undecided 1 gone 2 sleep 3 work 4 chores 5 phone
cat[:GONE] = 1; cat[SLEEP] = 2; cat[WORK] = 3; cat[CHORES] = 4; cat[PHONE] = 5

DUR = 56.0
SUBS = [
    (0.6, 5.0, "If you live to 80, you get about 4,000 weeks."),
    (5.4, 10.0, "This is all of them. Every dot is one week."),
    (10.4, 16.0, "If you're 30, 1,560 of them are already gone."),
    (16.4, 22.0, "About a third of what's left, you'll sleep."),
    (22.4, 28.0, "Work, commuting and chores take roughly another 700."),
    (28.4, 33.0, "That leaves about 1,000 weeks that are truly yours."),
    (33.4, 39.5, "Two hours a day on your phone? That's 217 of them."),
    (40.0, 47.0, "So the question isn't \"Do I have time?\""),
    (43.5, 47.0, "It's \"What do I do with this week?\""),
    (47.6, 55.5, "This one. Right now."),
]

def dot_colour(i, t):
    """returns (r,g,b) or None for each dot index, vectorised over all"""
    pass

def grid_colours(t):
    n = np.arange(N)
    appear = ease((t - 5.0) / 3.5 - (n // COLS) / ROWS * 0.9)          # rows ripple in
    base = np.tile(np.array([205, 205, 210], float), (N, 1))
    # gone: sequential fade 10.5..15
    g = np.clip((t - 10.5) / 4.5 - n / GONE, 0, 1) * (cat == 1)
    # sleep 16.5..21, work/chores 22.5..27 (random order)
    s = np.clip((t - 16.5) / 4.5 * 1.0 - order_rank * 0.6, 0, 1) * (cat == 2)
    w = np.clip((t - 22.5) / 4.5 - order_rank * 0.6, 0, 1) * ((cat == 3) | (cat == 4))
    dim = np.maximum(g, np.maximum(s, w))[:, None]
    dimcol = np.where((cat == 1)[:, None], np.array([42, 42, 46.0]), np.array([62, 62, 70.0]))
    col = base * (1 - dim) + dimcol * dim
    # free highlight 28.5..30
    hl = ease((t - 28.5) / 1.5) * ((cat == 0) | (cat == 5))
    col = col * (1 - hl[:, None]) + np.array([250, 250, 250.0]) * hl[:, None]
    # phone red 33.5..37.5
    pr = np.clip((t - 33.5) / 4 - order_rank * 0.4, 0, 1) * (cat == 5)
    col = col * (1 - pr[:, None]) + np.array([230, 70, 70.0]) * pr[:, None]
    return col, appear

def text_center(d, y, s, f, fill):
    w = d.textlength(s, font=f); d.text((540 - w / 2, y), s, font=f, fill=fill)

def pill(d, y, s, a, strike=0.0, filled=False):
    f = MED(36); w = d.textlength(s, font=f)
    c = int(235 * a)
    box = [540 - w / 2 - 34, y - 8, 540 + w / 2 + 34, y + 52]
    if filled:
        d.rounded_rectangle(box, 30, fill=(c, c, c)); d.text((540 - w / 2, y), s, font=f, fill=(0, 0, 0))
    else:
        d.rounded_rectangle(box, 30, outline=(c, c, c), width=3); d.text((540 - w / 2, y), s, font=f, fill=(c, c, c))
    if strike > 0:
        d.line([box[0] + 10, y + 22, box[0] + 10 + (box[2] - box[0] - 20) * strike, y + 22], fill=(c, c, c), width=4)

def subtitle(d, t):
    f = MED(40)
    for a, b, s in SUBS:
        al = win(t, a, b, 0.4, 0.4)
        if al <= 0: continue
        if a == 40.0 and t > 43.5: continue
        words = s.split(); lines = [""]
        for wd in words:
            if d.textlength(lines[-1] + " " + wd, font=f) > 900: lines.append(wd)
            else: lines[-1] = (lines[-1] + " " + wd).strip()
        for k, ln in enumerate(lines):
            text_center(d, 1690 + k * 54, ln, f, tuple(int(220 * al) for _ in range(3)))

def big_number(d, t):
    f = LIGHT(150)
    if t < 5.5:
        v = int(4160 * ease((t - 0.5) / 3.5)); a = win(t, 0.3, 5.5, 0.4, 0.5)
        text_center(d, 230, f"{v:,}", f, tuple(int(245 * a) for _ in range(3)))
        text_center(d, 410, "WEEKS", SEMI(34), tuple(int(160 * a) for _ in range(3)))
    pills = [(5.6, 10.2, "80 YEARS = 4,160 WEEKS"), (10.6, 16.2, "AGE 30: 1,560 GONE"), (16.6, 22.2, "SLEEP: 867"),
             (22.6, 28.2, "WORK + CHORES: 731")]
    for a_, b_, s in pills:
        al = win(t, a_, b_, 0.5, 0.4)
        if al > 0: pill(d, 330, s, al)
    if 28.4 < t < 33.3:
        al = win(t, 28.4, 33.3, 0.5, 0.4)
        text_center(d, 250, "~1,000", LIGHT(130), tuple(int(250 * al) for _ in range(3)))
        text_center(d, 405, "WEEKS THAT ARE YOURS", SEMI(30), tuple(int(170 * al) for _ in range(3)))
    if 33.4 < t < 39.8:
        al = win(t, 33.4, 39.8, 0.5, 0.4)
        v = int(217 * ease((t - 33.6) / 3.5))
        text_center(d, 250, f"{v}", LIGHT(140), (int(230 * al), int(70 * al), int(70 * al)))
        text_center(d, 405, "WEEKS ON YOUR PHONE", SEMI(30), tuple(int(170 * al) for _ in range(3)))

def render(t):
    img = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    gfade = 1 - ease((t - 39.6) / 1.2)
    if 4.9 < t and gfade > 0:
        col, appear = grid_colours(t)
        for i in range(N):
            a = appear[i] * gfade
            if a <= 0.01: continue
            x, y = pos[i]; r = 4.6 * (0.4 + 0.6 * a)
            c = tuple(int(v * a) for v in col[i])
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
        # "you are here" marker
        ma = win(t, 11.0, 39.6, 0.6, 0.6) * gfade
        if ma > 0:
            x, y = pos[GONE]; rr = 14 + 3 * math.sin(t * 4)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(int(250 * ma),) * 3, width=3)
            d.text((x + 22, y - 18), "YOU", font=SEMI(26), fill=(int(250 * ma),) * 3)
    big_number(d, t)
    # question scene
    if 40.0 < t < 47.4:
        a1 = win(t, 40.2, 47.2, 0.5, 0.4)
        pill(d, 820, "DO I HAVE TIME?", a1 * (0.45 if t > 43.2 else 1), strike=ease((t - 42.6) / 0.6))
        a2 = win(t, 43.6, 47.2, 0.5, 0.4)
        if a2 > 0: pill(d, 940, "WHAT DO I DO WITH THIS WEEK?", a2, filled=True)
    # final: one glowing dot with orbiting particles
    if t > 47.4:
        a = ease((t - 47.4) / 1.2) * min(1, (DUR - t) / 0.8)
        rng2 = np.random.default_rng(3)
        for k in range(260):
            r0 = rng2.uniform(80, 470); ang = rng2.uniform(0, 2 * math.pi) + t * (0.25 + 40 / r0) * (1 if k % 2 else -1) * 0.3
            x = 540 + r0 * math.cos(ang); y = 960 + r0 * math.sin(ang) * 0.95
            rr = rng2.uniform(1.5, 3.5); c = int(rng2.uniform(80, 220) * a)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(c, c, c))
        glow = Image.new("L", (400, 400), 0); ImageDraw.Draw(glow).ellipse([150, 150, 250, 250], fill=int(255 * a))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        img.paste(Image.new("RGB", (400, 400), (255, 255, 255)), (340, 760), glow.point(lambda v: v // 2))
        d = ImageDraw.Draw(img)
        d.ellipse([528, 948, 552, 972], fill=(int(255 * a),) * 3)
        a3 = win(t, 51.0, 56.0, 0.8, 0.8)
        if a3 > 0: text_center(d, 330, "MAKE IT COUNT.", SEMI(64), tuple(int(245 * a3) for _ in range(3)))
    subtitle(d, t)
    return img

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((240 * len(ims), 427)).save("chk_weeks.png")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
