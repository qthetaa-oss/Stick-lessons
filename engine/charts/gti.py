import sys, math, wave, subprocess
sys.path.insert(0, "/home/claude/vid")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import fnt, tracked, with_alpha, ease, WHITE, GREY, DIM, GREEN, RED, W, H, FPS, figure_sprite, BILL, money

DUR = 21.0
AMBER = (240, 180, 60)
COLS = [180, 540, 900]
NAMES = ["GAMBLER", "TRADER", "INVESTOR"]
COLORS = [RED, AMBER, GREEN]
CH_T, CH_B, CH_W = 560, 770, 300
DESK_Y = 1120
T0, T1 = 1.6, 14.0   # chart drawing window (10 years)

# ---- price paths (value in $) as function of u in [0,1] ----
rng = np.random.default_rng(4)
N = 400
u = np.linspace(0, 1, N)
gam = np.where(u < 0.32, 10000 + 30000 * (u / 0.32) ** 1.6, 0)
crash = (u >= 0.32) & (u < 0.46)
gam[crash] = 40000 * (1 - ((u[crash] - 0.32) / 0.14) ** 0.7)
gam[u >= 0.46] = 0
gam += np.where(u < 0.46, rng.normal(0, 900, N), 0); gam = np.clip(gam, 0, None); gam[u >= 0.46] = 0; gam[0] = 10000
noise = np.cumsum(rng.normal(0, 1, N)); noise -= np.linspace(0, noise[-1], N)
trd = 10000 + 1400 * np.sin(u * 37) * np.exp(-u * 0.3) + 600 * noise / np.abs(noise).max() - 1800 * u
trd[0] = 10000; trd[-1] = 8200
inv = 10000 * 1.07 ** (u * 10)
dip = np.exp(-((u - 0.55) / 0.05) ** 2) * 2200
inv = inv - dip + rng.normal(0, 120, N); inv[0] = 10000; inv[-1] = 10000 * 1.07 ** 10
PATHS = [gam, trd, inv]

def at(arr, uu):
    x = max(0, min(1, uu)) * (N - 1); i = int(x)
    if i >= N - 1: return arr[-1]
    f = x - i; return arr[i] * (1 - f) + arr[i + 1] * f

def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.full((H, W), 12.0, np.float32)
    for cx in COLS:
        # light cone from lamp at (cx, 430)
        dy = yy - 440; spread = 60 + dy * 0.42
        cone = np.clip(1 - np.abs(xx - cx) / np.maximum(spread, 1), 0, 1) * (dy > 0) * np.clip(1 - dy / 900, 0, 1)
        base += 22 * cone ** 1.2
    base[1150:] *= 0.75
    im = Image.fromarray(np.clip(np.stack([base, base * 0.98, base * 0.95], -1), 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 1150, W, 1156], fill=(30, 29, 28))
    for i, cx in enumerate(COLS):
        dr.polygon([(cx - 50, 440), (cx + 50, 440), (cx + 28, 418), (cx - 28, 418)], fill=(36, 36, 40), outline=(10, 10, 12))
        dr.line([cx, 360, cx, 418], fill=(36, 36, 40), width=4)
        dr.ellipse([cx - 22, 432, cx + 22, 450], fill=(235, 230, 210))
        # chart frame
        dr.rounded_rectangle([cx - CH_W / 2 - 6, CH_T - 6, cx + CH_W / 2 + 6, CH_B + 6], 8, fill=(10, 10, 12))
        dr.rounded_rectangle([cx - CH_W / 2, CH_T, cx + CH_W / 2, CH_B], 6, fill=(22, 22, 26))
        for k in range(1, 4):
            y = CH_T + k * (CH_B - CH_T) / 4
            dr.line([cx - CH_W / 2 + 8, y, cx + CH_W / 2 - 8, y], fill=(34, 34, 40), width=1)
        # desk
        dr.rectangle([cx - 140, DESK_Y - 4, cx + 140, DESK_Y + 26], fill=(10, 10, 12))
        dr.rectangle([cx - 136, DESK_Y, cx + 136, DESK_Y + 22], fill=(58, 52, 46))
        dr.rectangle([cx - 136, DESK_Y + 22, cx + 136, DESK_Y + 30], fill=(40, 36, 32))
        for lx in (cx - 120, cx + 108):
            dr.rectangle([lx - 2, DESK_Y + 26, lx + 14, 1152], fill=(10, 10, 12))
            dr.rectangle([lx + 2, DESK_Y + 28, lx + 10, 1152], fill=(48, 43, 38))
    return im
BG = make_bg()

def chart(dr, img, i, uu):
    cx = COLS[i]; arr = PATHS[i]; col = COLORS[i]
    lo, hi = 0, 42000 if i == 0 else 22000
    if i == 1: lo, hi = 5000, 15000
    x0 = cx - CH_W / 2 + 14; wdt = CH_W - 28
    n = min(N, max(2, int(min(1, uu) * (N - 1)) + 1))
    pts = [(x0 + wdt * k / (N - 1), CH_B - 12 - (CH_B - CH_T - 24) * (arr[k] - lo) / (hi - lo)) for k in range(n)]
    if i == 2 and n > 2:
        poly = pts + [(pts[-1][0], CH_B - 6), (pts[0][0], CH_B - 6)]
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).polygon(poly, fill=(57, 229, 140, 40))
        img.alpha_composite(lay)
        dr = ImageDraw.Draw(img)
    dr.line(pts, fill=(10, 10, 12), width=9, joint="curve")
    dr.line(pts, fill=col, width=5, joint="curve")
    hx, hy = pts[-1]
    dr.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=col, outline=(10, 10, 12), width=3)
    return dr

def laptop(dr, cx, col, flick):
    dr.polygon([(cx + 30, DESK_Y), (cx + 120, DESK_Y), (cx + 112, DESK_Y - 70), (cx + 40, DESK_Y - 70)], fill=(10, 10, 12))
    c = tuple(int(v * (0.35 + 0.25 * flick)) for v in col)
    dr.polygon([(cx + 38, DESK_Y - 6), (cx + 113, DESK_Y - 6), (cx + 106, DESK_Y - 64), (cx + 45, DESK_Y - 64)], fill=c)
    dr.rectangle([cx + 20, DESK_Y - 6, cx + 132, DESK_Y], fill=(10, 10, 12))

SMALL_BILL = BILL.resize((86, 38), Image.LANCZOS)

CAPTIONS = [
    (0.2, 99, 200, "GAMBLER  vs  TRADER  vs  INVESTOR", 34, WHITE, "s"),
    (0.9, 14.0, 252, "SAME $10,000.", 34, GREY, "s"),
    (14.3, 99, 1290, "ONE CHASED FAST MONEY.", 36, WHITE, "s"),
    (15.5, 99, 1340, "ONE CHASED EVERY MOVE.", 36, WHITE, "s"),
    (16.7, 99, 1390, "ONE JUST WAITED.", 36, WHITE, "s"),
    (18.0, 99, 1462, "BORING WINS.", 64, GREEN, "k"),
]

def render(t):
    img = BG.copy().convert("RGBA"); dr = ImageDraw.Draw(img)
    for t0, t1, y, text, size, col, wt in CAPTIONS:
        if t0 <= t < t1:
            a = min(1, (t - t0) / 0.25, (t1 - t) / 0.3)
            tracked(dr, (540, y), text, fnt(wt, size), with_alpha(col, a) + (255,), track=0.1, anchor="c", reveal=min(len(text), int((t - t0) * 40) + 1))
    uu = (t - T0) / (T1 - T0)
    yr = min(10, max(1, int(max(0, uu) * 10) + 1))
    txt = f"YEAR {yr}"; f = fnt("s", 26)
    tracked(dr, (540, 308), txt, f, GREY + (255,), track=0.18, anchor="c")
    for i, cx in enumerate(COLS):
        lab = NAMES[i]; lf = fnt("s", 22)
        wdt = tracked(ImageDraw.Draw(Image.new("L", (1, 1))), (0, 0), lab, lf, 0, track=0.16)
        dr.rounded_rectangle([cx - wdt / 2 - 14, 482, cx + wdt / 2 + 14, 520], 6, fill=(10, 10, 12), outline=COLORS[i], width=2)
        tracked(dr, (cx, 488), lab, lf, COLORS[i] + (255,), track=0.16, anchor="c")
        if t >= T0:
            dr = chart(dr, img, i, uu)
        v = at(PATHS[i], uu) if t >= T0 else 10000
        if i == 1 and uu >= 1: v = PATHS[1][-1]
        vt = money(v)
        col = COLORS[i] if (i != 0 or v > 0) else RED
        dr.text((cx, 810), vt, font=fnt("b", 48), fill=col + (255,), anchor="mt")
        if uu >= 1:
            pct = (v / 10000 - 1) * 100
            tracked(dr, (cx, 872), f"{pct:+.0f}%", fnt("s", 24), COLORS[i] + (255,), track=0.1, anchor="c")
    # figures
    bob = 3 * math.sin(t * 2.2)
    fin = ease((t - 14.2) / 1.0)
    if fin > 0:
        lay = Image.new("L", (W, H), 0)
        ImageDraw.Draw(lay).ellipse([COLS[2] - 220, 820, COLS[2] + 220, 1200], fill=int(90 * fin))
        lay = lay.filter(ImageFilter.GaussianBlur(70))
        img = Image.composite(Image.new("RGBA", (W, H), GREEN + (255,)), img, lay.point(lambda v: int(v * 0.45)))
        # redraw investor figure on top of glow is not necessary; glow is subtle
    dr = ImageDraw.Draw(img)
    for i, cx in enumerate(COLS):
        k = dict()
        if i == 0:
            rise = ease((uu - 0.05) / 0.2) * (1 - ease((uu - 0.33) / 0.05))
            k = dict(rai=0, sad=ease((uu - 0.38) / 0.1), cheer=rise, bob=bob + rise * 6 * math.sin(t * 9))
        elif i == 1:
            busy = 1 if 0 < uu < 1 else 0
            k = dict(rai=busy * (0.5 + 0.5 * math.sin(t * 7)), sad=fin * 0.55, cheer=0, bob=bob + busy * 3 * math.sin(t * 11))
        else:
            k = dict(rai=0, sad=0, cheer=fin * ease((t - 14.8) / 0.8), bob=bob * 0.7)
        fg = figure_sprite(round(k["rai"], 2), round(k["sad"], 2), round(k["cheer"], 2), round(k["bob"], 1)).resize((240, 288), Image.LANCZOS)
        img.alpha_composite(fg, (int(cx - 60 - fg.width / 2), int(DESK_Y + 125 - fg.height)))
    dr = ImageDraw.Draw(img)
    for i, cx in enumerate(COLS):
        dr.rectangle([cx - 140, DESK_Y - 4, cx + 140, DESK_Y + 26], fill=(10, 10, 12))
        dr.rectangle([cx - 136, DESK_Y, cx + 136, DESK_Y + 22], fill=(58, 52, 46))
        laptop(dr, cx, COLORS[i], 0.5 + 0.5 * math.sin(t * (9 if i == 1 else 2)))
    # gambler: money flying during rise
    if T0 < t:
        for j in range(8):
            ph = (t * 0.9 + j / 8) % 1
            st = T0 + (T1 - T0) * 0.08 + j * 0.35
            if st < t < T0 + (T1 - T0) * 0.36:
                x = COLS[0] - 60 + (j - 4) * 22 + math.sin(ph * 6 + j) * 40
                y = DESK_Y - 160 - ph * 380
                b = SMALL_BILL.rotate((j * 47 + t * 120) % 360, expand=True)
                b.putalpha(b.split()[3].point(lambda v: int(v * (1 - ph))))
                img.alpha_composite(b, (int(x - b.width / 2), int(y - b.height / 2)))
    # crash flash
    dr = ImageDraw.Draw(img)
    tc = T0 + (T1 - T0) * 0.40
    if tc < t < tc + 2.2:
        a = 1 - (t - tc) / 2.2
        tracked(dr, (COLS[0], 905), "-100%", fnt("k", 46), with_alpha(RED, a) + (255,), track=0.05, anchor="c")
    tp = T0 + (T1 - T0) * 0.25
    if tp < t < tp + 2.0:
        a = min(1, (t - tp) / 0.3) * (1 - max(0, t - tp - 1.4) / 0.6)
        tracked(dr, (COLS[0], 905), "+300%!", fnt("k", 46), with_alpha(GREEN, a) + (255,), track=0.05, anchor="c")
    img = img.convert("RGB")
    if t > 18.6:
        d2 = ImageDraw.Draw(img); a = min(1, (t - 18.6) / 0.5)
        tracked(d2, (540, 1560), "ILLUSTRATION ONLY. ~7% AVG. RETURN ASSUMED. NOT FINANCIAL ADVICE.", fnt("m", 18), with_alpha(DIM, a), track=0.08, anchor="c")
    fa = min(1, t / 0.4, (DUR - t) / 0.6)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img

def audio(path):
    SR = 44100; n = int(SR * DUR); tt = np.arange(n) / SR; out = np.zeros(n)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * tt)
    for f, a in ((55, .09), (82.4, .05), (110, .03)): out += a * lfo * np.sin(2 * np.pi * f * tt)
    def add(t0, sig):
        i = int(t0 * SR); j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    def tone(f, d, a, dec):
        x = np.arange(int(SR * d)) / SR; return a * np.sin(2 * np.pi * f * x) * np.exp(-x * dec)
    for y in range(1, 10): add(T0 + (T1 - T0) * y / 10, tone(1400, 0.15, 0.08, 30))
    # rising tone during gambler pump, crash thud
    i0, i1 = int((T0 + 0.4) * SR), int((T0 + (T1 - T0) * 0.33) * SR); x = np.arange(i1 - i0) / SR; L = x[-1]
    ph = 2 * np.pi * np.cumsum(200 + 400 * (x / L)) / SR; out[i0:i1] += 0.06 * (x / L) * np.sin(ph)
    x = np.arange(int(SR * 1.6)) / SR; add(T0 + (T1 - T0) * 0.4, 0.5 * np.sin(2 * np.pi * (60 - 25 * x) * x) * np.exp(-x * 2.5))
    for t0, base in ((14.3, 392), (15.5, 440), (16.7, 494), (18.0, 587)):
        for mm, a in ((1, .1), (1.5, .06), (2, .04)): add(t0, tone(base * mm, 3.0, a, 1.4))
    out *= np.minimum(1, np.minimum(tt / 0.5, (DUR - tt) / 1.2)); out = out / np.max(np.abs(out)) * 0.8
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((360 * len(ims), 640)).save("chk.png")
    elif sys.argv[1] == "audio": audio("gti.wav")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
