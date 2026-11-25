import sys, math, random, wave, subprocess
sys.path.insert(0, "/home/claude/vid")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import fnt, tracked, with_alpha, ease, lerp, WHITE, GREY, DIM, GREEN, RED, W, H, FPS, SS

DUR = 22.0
PANELS = [dict(top=470, ground=830, bottom=1000), dict(top=1040, ground=1400, bottom=1570)]
FIG_X, PLANT_X = 330, 600

# ---------- timeline ----------
YEAR_T = [1.2, 3.8, 6.4, 9.0, 11.6]       # start of years 1..5
QUIT_T = 7.4                              # A stops (year 3)
BURST_T = 12.4                            # bamboo shoots
def year(t):
    y = 1
    for i, s in enumerate(YEAR_T):
        if t >= s: y = i + 1
    return y
def root_growth(t, quitter):
    g = ease((t - 1.2) / 11.0) * 0.92
    if t > BURST_T: g = 0.92 + 0.08 * ease((t - BURST_T) / 1.5)
    if quitter: g = min(g, ease((QUIT_T - 1.2) / 11.0) * 0.92)
    return g

# ---------- roots (shared shape) ----------
random.seed(7)
ROOTS = []  # (x0,y0,x1,y1,order_start,order_end,width)
def grow(x, y, ang, length, w, d0, depth):
    if depth > 6 or length < 8: return
    steps = 4
    for i in range(steps):
        a = ang + random.uniform(-0.35, 0.35)
        nx, ny = x + math.cos(a) * length / steps, y + math.sin(a) * length / steps
        ROOTS.append((x, y, nx, ny, d0 + i * length / steps, d0 + (i + 1) * length / steps, w))
        x, y, ang = nx, ny, a
    for k in range(random.randint(2, 3)):
        grow(x, y, ang + random.uniform(-0.9, 0.9), length * random.uniform(0.55, 0.75), max(1.5, w * 0.7), d0 + length, depth + 1)
grow(0, 0, math.pi / 2, 70, 7, 0, 0)
for a in (2.3, 0.8, 2.8, 0.35):
    grow(0, 6, a, 60, 5, 8, 1)
MAXD = max(r[5] for r in ROOTS)

def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.full((H, W), 10.0, np.float32)
    d = np.sqrt(((xx - 540) / 650) ** 2 + ((yy - 300) / 450) ** 2)
    base += 18 * np.clip(1 - d, 0, 1) ** 1.6
    for p in PANELS:
        d = np.sqrt(((xx - 470) / 520) ** 2 + ((yy - (p["ground"] - 150)) / 260) ** 2)
        m = (yy >= p["top"]) & (yy < p["ground"])
        base += m * 20 * np.clip(1 - d, 0, 1) ** 1.3
    img = np.stack([base, base, base * 1.06], -1)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for p in PANELS:
        dr.rectangle([60, p["ground"], 1020, p["bottom"]], fill=(19, 17, 16))
        for _ in range(260):
            x, y = rnd.uniform(64, 1016), rnd.uniform(p["ground"] + 6, p["bottom"] - 4)
            c = rnd.randint(26, 40); r = rnd.uniform(1, 2.6)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=(c, c - 3, c - 6))
        dr.rectangle([60, p["ground"] - 2, 1020, p["ground"] + 3], fill=(60, 58, 56))
    # fade panel edges
    yy2, xx2 = np.mgrid[0:H, 0:W].astype(np.float32)
    arr = np.asarray(im).astype(np.float32)
    edge = np.clip(np.minimum(xx2 - 60, 1020 - xx2) / 90, 0, 1)[..., None]
    inside = np.zeros((H, W, 1), np.float32)
    for p in PANELS: inside[p["top"]:p["bottom"]] = 1
    bgc = np.array([10, 10, 10.6])
    arr = arr * (1 - inside * (1 - edge)) + bgc * inside * (1 - edge)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
BG = make_bg()

# ---------- figure ----------
def figure_sprite(rai, sad, cheer, bob, walk, look):
    w, h = 320, 380
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy = w / 2, h - 20
    sw = math.sin(walk) * (1 if walk else 0)
    hip = (0, -110 + bob * 0.5); neck = (sad * 14, -200 + bob + sad * 12)
    head = (sad * 26 - look * 6, -240 + bob + sad * 30 - look * 4); sh = (neck[0], neck[1] + 8)
    lhand = lerp((-40 - sw * 20, -112 + bob), (-56, -260 + bob), cheer)
    lelb = lerp((-30 - sw * 12, -155 + bob), (-48, -225 + bob), cheer)
    rhand = lerp(lerp((40 + sw * 20, -112 + bob), (92, -170 + bob), rai), (56, -260 + bob), cheer)
    relb = lerp(lerp((30 + sw * 12, -155 + bob), (52, -168 + bob), rai), (48, -225 + bob), cheer)
    if sad:
        lhand = lerp(lhand, (-4, -104 + bob), sad); rhand = lerp(rhand, (44, -104 + bob), sad * (1 - rai))
    lfoot = (-30 + sw * 34, 0 - max(0, -sw) * 6); rfoot = (30 - sw * 34, 0 - max(0, sw) * 6)
    segs = [[hip, (-14 + sw * 14, -55), lfoot], [hip, (14 - sw * 14, -55), rfoot], [hip, neck], [sh, lelb, lhand], [sh, relb, rhand]]
    P = lambda p: ((ox + p[0]) * SS, (oy + p[1]) * SS)
    for wdt, col in ((30, (10, 10, 12, 255)), (18, (242, 242, 244, 255))):
        for sg in segs:
            pts = [P(p) for p in sg]
            d.line(pts, fill=col, width=wdt * SS, joint="curve")
            for p in (pts[0], pts[-1]):
                rr = wdt * SS / 2; d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=col)
    hc = P(head); R = 34 * SS
    d.ellipse([hc[0] - R - 6 * SS, hc[1] - R - 6 * SS, hc[0] + R + 6 * SS, hc[1] + R + 6 * SS], fill=(10, 10, 12, 255))
    d.ellipse([hc[0] - R, hc[1] - R, hc[0] + R, hc[1] + R], fill=(246, 246, 248, 255))
    return im.resize((w, h), Image.LANCZOS), (rhand[0], rhand[1])

_FC = {}
def figure(**k):
    key = tuple(round(k.get(x, 0), 2) for x in ("rai", "sad", "cheer", "bob", "walk", "look"))
    if key not in _FC:
        if len(_FC) > 3000: _FC.clear()
        _FC[key] = figure_sprite(*key)
    return _FC[key]

def can_sprite(tilt):
    s = 4
    im = Image.new("RGBA", (180 * s, 140 * s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    body = [(40, 40), (110, 40), (104, 110), (46, 110)]
    spout = [(108, 62), (165, 30), (170, 38), (110, 78)]
    for poly, fill in ((spout, (200, 202, 208)), (body, (200, 202, 208))):
        d.polygon([(x * s, y * s) for x, y in poly], fill=fill, outline=(10, 10, 12), width=5 * s)
    d.arc([18 * s, 30 * s, 60 * s, 90 * s], 90, 270, fill=(10, 10, 12), width=12 * s)
    d.arc([18 * s, 30 * s, 60 * s, 90 * s], 90, 270, fill=(200, 202, 208), width=6 * s)
    im = im.resize((126, 98), Image.LANCZOS)
    return im.rotate(-tilt, expand=True, resample=Image.BICUBIC)
CANS = {a: can_sprite(a) for a in range(0, 46)}

def draw_roots(dr, p, g, bright):
    ox, oy = PLANT_X, p["ground"] + 2
    lim = g * MAXD
    for x0, y0, x1, y1, d0, d1, w in ROOTS:
        if d0 >= lim: continue
        f = min(1, (lim - d0) / (d1 - d0))
        xe, ye = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        yb = p["bottom"] - p["ground"] - 8
        if y0 > yb: continue
        c = (150, 132, 100) if bright else (110, 100, 84)
        dr.line([ox + x0, oy + y0, ox + xe, oy + min(ye, yb)], fill=c, width=max(1, int(w * 0.8)))

def draw_bamboo(img, p, hgt, t):
    if hgt < 2: return
    x0, x1 = PLANT_X - 18, PLANT_X + 18
    base = p["ground"]
    top = base - hgt
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).rectangle([x0 - 10, top, x1 + 10, base], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(50)).point(lambda v: int(v * 0.55))
    img.paste(Image.composite(Image.new("RGB", (W, H), GREEN), img, glow))
    dr = ImageDraw.Draw(img)
    dr.rectangle([x0 - 4, top, x1 + 4, base], fill=(10, 10, 12))
    dr.rectangle([x0, top, x1, base], fill=GREEN)
    dr.rectangle([x0 + 6, top, x0 + 11, base], fill=(130, 245, 185))
    y = base - 70
    while y > top + 10:
        dr.rectangle([x0 - 4, y - 4, x1 + 4, y + 4], fill=(20, 120, 70))
        # leaves at some nodes
        if int((base - y) / 70) % 2 == 0 and base - y > 140:
            side = 1 if int((base - y) / 140) % 2 else -1
            lx = x1 if side > 0 else x0
            dr.polygon([(lx, y), (lx + side * 80, y - 30), (lx + side * 90, y - 22), (lx + side * 8, y + 6)], fill=GREEN, outline=(10, 10, 12))
        y -= 70
    dr.polygon([(x0, top), (x1, top), (PLANT_X, top - 30)], fill=GREEN)

def sprout(dr, p, size):
    if size <= 0: return
    x, y = PLANT_X, p["ground"]
    dr.line([x, y, x, y - 14 * size], fill=(10, 10, 12), width=9)
    dr.line([x, y, x, y - 14 * size], fill=(120, 200, 150), width=4)
    dr.ellipse([x, y - 16 * size, x + 12 * size, y - 9 * size], fill=(120, 200, 150))

CAPTIONS = [
    (0.4, 11.9, 200, "TWO PEOPLE PLANT THE SAME SEED.", 40, WHITE, "s"),
    (3.0, 11.9, 258, "THEY WATER IT EVERY DAY.", 40, WHITE, "s"),
    (5.0, 11.9, 316, "NOTHING HAPPENS.", 40, GREY, "s"),
    (QUIT_T + 0.2, 11.9, 374, "ONE GIVES UP.", 40, RED, "s"),
    (15.0, 99, 200, "IT WAS GROWING", 46, WHITE, "s"),
    (15.8, 99, 262, "THE WHOLE TIME.", 46, WHITE, "s"),
    (18.0, 99, 344, "DON'T QUIT BEFORE IT SHOWS.", 44, GREEN, "k"),
]

def render(t):
    img = BG.copy(); dr = ImageDraw.Draw(img)
    for t0, t1, y, text, size, col, wt in CAPTIONS:
        if t0 <= t < t1:
            a = min(1, (t - t0) / 0.25, (t1 - t) / 0.3)
            tracked(dr, (540, y), text, fnt(wt, size), with_alpha(col, a), track=0.1, anchor="c", reveal=min(len(text), int((t - t0) * 34) + 1))
    yr = year(t)
    if t > 0.8 and t < 14.8:
        a = min(1, (t - 0.8) / 0.3, (14.8 - t) / 0.4)
        tracked(dr, (970, 490), f"YEAR {yr}", fnt("s", 28), with_alpha(GREEN if yr == 5 else GREY, a), track=0.18, anchor="r" if False else "l") if False else None
        f = fnt("s", 28); txt = f"YEAR {yr}"
        wdt = tracked(ImageDraw.Draw(Image.new("L", (1, 1))), (0, 0), txt, f, 0, track=0.18)
        tracked(dr, (990 - wdt, 492), txt, f, with_alpha(GREEN if yr == 5 else GREY, a), track=0.18)
    burst = ease((t - BURST_T) / 2.2) ** 1.4
    for i, p in enumerate(PANELS):
        quitter = i == 0
        g = root_growth(t, quitter)
        draw_roots(dr, p, g, bright=(not quitter and t > BURST_T))
        if quitter or t < BURST_T:
            sprout(dr, p, min(1, max(0, (t - 2.5) / 3)))
    # bamboo
    hb = burst * 930
    if hb > 0:
        draw_bamboo(img, PANELS[1], hb, t); dr = ImageDraw.Draw(img)
        if t < BURST_T + 0.4:
            fl = 1 - (t - BURST_T) / 0.4
            img = Image.blend(img, Image.new("RGB", (W, H), (200, 255, 220)), max(0, fl) * 0.25); dr = ImageDraw.Draw(img)
    # labels
    if t > QUIT_T + 1.2:
        a = min(1, (t - QUIT_T - 1.2) / 0.4) * (1 - ease((t - BURST_T - 0.6) / 1.5) * 0.6)
        tracked(dr, (92, PANELS[0]["top"] + 28), "QUIT IN YEAR 3", fnt("s", 24), with_alpha(RED, a), track=0.2)
    if t > BURST_T + 0.6:
        a = min(1, (t - BURST_T - 0.6) / 0.4)
        tracked(dr, (92, PANELS[1]["top"] + 28), "KEPT GOING", fnt("s", 24), with_alpha(GREEN, a), track=0.2)
    img = img.convert("RGBA")
    bob = 3 * math.sin(t * 2.2)
    # watering cycle
    def water_amt(tt):
        c = (tt % 1.3) / 1.3
        return ease(min(1, c / 0.25)) * (1 - ease(max(0, (c - 0.7) / 0.3)))
    for i, p in enumerate(PANELS):
        quitter = i == 0
        x = FIG_X; kw = dict(bob=bob)
        show_can = t > 1.4
        wa = water_amt(t - 1.4 - i * 0.15) if t > 1.4 else 0
        alpha = 1.0
        if quitter:
            if t > QUIT_T:
                st = t - QUIT_T
                wa *= max(0, 1 - st / 0.3)
                kw["sad"] = ease(st / 0.6)
                show_can = st < 0.9
                if st > 1.4:
                    wt = st - 1.4
                    x = FIG_X - 160 * wt ** 1.1
                    kw["walk"] = wt * 7; kw["sad"] = 0.6
                    alpha = max(0, 1 - wt / 2.2)
        else:
            if t > BURST_T:
                st = t - BURST_T
                wa *= max(0, 1 - st / 0.3); show_can = st < 0.4
                kw["look"] = ease(st / 0.6)
                kw["cheer"] = ease((st - 1.4) / 0.8)
        kw["rai"] = 0.55 + 0.45 * wa if show_can else 0
        if alpha <= 0: continue
        fg, hand = figure(**kw)
        if alpha < 1:
            fg = fg.copy(); fg.putalpha(fg.split()[3].point(lambda v: int(v * alpha)))
        fx, fy = int(x - fg.width / 2), int(p["ground"] - fg.height + 20)
        img.alpha_composite(fg, (fx, fy))
        if show_can:
            tilt = int(45 * wa)
            cs = CANS[tilt]
            hx, hy = fx + fg.width / 2 + hand[0], fy + fg.height - 20 + hand[1]
            img.alpha_composite(cs, (int(hx - 20), int(hy - 30)))
            if wa > 0.6:
                for k in range(6):
                    ph = ((t * 2.2 + k / 6) % 1)
                    dx = hx + 128 + ph * 10 + (k % 3) * 6
                    dy = hy - 10 + ph * (p["ground"] - hy + 10)
                    ImageDraw.Draw(img).ellipse([dx - 3, dy - 5, dx + 3, dy + 5], fill=(150, 190, 230, 255))
    # dropped can for quitter
    if t > QUIT_T + 0.9:
        cs = CANS[0].rotate(80, expand=True)
        img.alpha_composite(cs, (FIG_X + 60, PANELS[0]["ground"] - cs.height + 6))
    img = img.convert("RGB")
    fa = min(1, t / 0.4, (DUR - t) / 0.6)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img

def audio(path):
    SR = 44100; n = int(SR * DUR); tt = np.arange(n) / SR; out = np.zeros(n)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * tt)
    for f, a in ((55, .10), (82.4, .06), (110, .035)): out += a * lfo * np.sin(2 * np.pi * f * tt + np.sin(2 * np.pi * 0.13 * tt))
    def add(t0, sig):
        i = int(t0 * SR); j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    def tone(f, d, a, dec):
        x = np.arange(int(SR * d)) / SR; return a * np.sin(2 * np.pi * f * x) * np.exp(-x * dec)
    for y in YEAR_T[1:]: add(y, tone(1200, 0.5, 0.08, 8)); add(y, tone(600, 0.5, 0.08, 6))
    add(QUIT_T, tone(98, 2.0, 0.35, 1.5)); add(QUIT_T, tone(73.4, 2.0, 0.25, 1.2))
    i0, i1 = int((BURST_T - 2.0) * SR), int(BURST_T * SR); x = np.arange(i1 - i0) / SR; L = x[-1]
    ph = 2 * np.pi * np.cumsum(110 + 500 * (x / L) ** 2) / SR; out[i0:i1] += (x / L) ** 2 * 0.15 * (np.sin(ph) + 0.4 * np.sin(2 * ph))
    x = np.arange(int(SR * 1.5)) / SR; add(BURST_T, 0.5 * np.sin(2 * np.pi * (70 - 30 * x) * x) * np.exp(-x * 3))
    for t0, base in ((BURST_T, 523), (15.0, 440), (18.0, 587)):
        for mm, a in ((1, .12), (1.5, .07), (2, .05)): add(t0, tone(base * mm, 3.5, a, 1.2))
    out *= np.minimum(1, np.minimum(tt / 0.5, (DUR - tt) / 1.2)); out = out / np.max(np.abs(out)) * 0.8
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((360 * len(ims), 640)).save("chk.png")
    elif sys.argv[1] == "audio": audio("bamboo.wav")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
