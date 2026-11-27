import sys, math, wave, subprocess
sys.path.insert(0, "/home/claude/vid"); sys.path.insert(0, "/home/claude/vid2")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import fnt, tracked, with_alpha, ease, WHITE, GREY, DIM, GREEN, RED, W, H, FPS
import bamboo

DUR = 26.0
NST = 22
X0, Y0 = 50, 1580          # bottom-left of staircase
SW, SH = 38.5, 42.0        # step width/height
AMBER = (240, 180, 60)

def step_xy(s):
    """feet position for (fractional) step index s"""
    i = int(max(0, min(NST, s)))
    x = X0 + 20 + s * SW
    y = Y0 - i * SH
    return x, y

def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.full((H, W), 9.0, np.float32)
    d = np.sqrt(((xx - 700) / 800) ** 2 + ((yy - 700) / 900) ** 2)
    base += 14 * np.clip(1 - d, 0, 1) ** 1.5
    im = Image.fromarray(np.clip(np.stack([base, base, base * 1.06], -1), 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    for i in range(NST + 1):
        x = X0 + i * SW; y = Y0 - i * SH
        dr.rectangle([x, y, W if i == NST else x + SW + 1, H], fill=(22, 22, 26))
        dr.line([x, y, x + SW, y], fill=(70, 70, 78), width=3)
        dr.line([x, y, x, y + SH], fill=(40, 40, 46), width=2)
    # summit marker
    tx, ty = step_xy(NST)
    dr.line([tx + 30, ty, tx + 30, ty - 120], fill=(90, 90, 96), width=4)
    dr.polygon([(tx + 32, ty - 120), (tx + 92, ty - 102), (tx + 32, ty - 84)], fill=GREEN)
    return im
BG = make_bg()

GLOW = Image.new("L", (900, 900), 0)
ImageDraw.Draw(GLOW).ellipse([260, 260, 640, 640], fill=255)
GLOW = GLOW.filter(ImageFilter.GaussianBlur(95))

def days(t):
    segs = [(0, 1.5, 0, 0), (1.5, 6.0, 0, 30), (6.0, 9.0, 30, 70), (9.0, 12.0, 70, 190),
            (12.0, 14.5, 190, 240), (14.5, 18.5, 240, 365)]
    for a, b, d0, d1 in segs:
        if t < b: return d0 + (d1 - d0) * (t - a) / (b - a)
    return 365.0

def clamp(x, a, b): return max(a, min(b, x))

def characters(d, t):
    """returns list of (name, s, pose dict, alpha, label colour, note)"""
    out = []
    # HYPE: sprints, burns out day 7, slides down & fades
    if d < 7: s = d * 1.45; p = dict(walk=t * 13); a = 1; note = None
    elif d < 15: s = 10.1; p = dict(sad=ease((d - 7) / 2)); a = 1; note = ("BURNED OUT", RED)
    else:
        f = clamp((d - 15) / 25, 0, 1); s = 10.1 * (1 - f); p = dict(sad=1, walk=t * 6 if f < 1 else 0); a = 1 - f; note = None
    out.append(("HYPE", s, p, a, AMBER, note))
    # MOTIVATION: fast, bad day at 21 → turns back
    if d < 21: s = d * 0.42; p = dict(walk=t * 10); a = 1; note = None
    elif d < 30: s = 8.8; p = dict(sad=ease((d - 21) / 4)); a = 1; note = ("BAD DAY", RED)
    else:
        f = clamp((d - 30) / 35, 0, 1); s = 8.8 * (1 - f); p = dict(sad=0.6, walk=t * 7 if f < 1 else 0); a = 1 - f; note = None
    out.append(("MOTIVATION", s, p, a, (235, 110, 110), note))
    # TALENT: confident, stops at day 60 "tomorrow"
    if d < 60: s = d * 0.2; p = dict(walk=t * 7); a = 1; note = None
    else: s = 12.0; p = dict(sad=0.55); a = max(0.45, 1 - (d - 60) / 150); note = ("\"TOMORROW.\"", GREY) if d < 160 else None
    out.append(("TALENT", s, p, a, (190, 190, 200), note))
    # DISCIPLINE: slow, steady, setback at 200
    sb = 0.0
    if 200 <= d < 203: sb = (d - 200) / 3
    elif d >= 203: sb = max(0.0, 1 - (d - 203) / 45)
    s = NST * d / 365 - 2.2 * sb
    p = dict(walk=t * 6 if d < 365 else 0, sad=0.5 * sb if 200 <= d < 215 else 0,
             cheer=ease((t - 19.0) / 0.8))
    note = ("SETBACK", RED) if 200 <= d < 225 else None
    out.append(("DISCIPLINE", s, p, 1, GREEN, note))
    return out

CAPS = [
    (0.0, 18.6, 175, "WHO MAKES IT TO THE TOP?", 54, WHITE, "k"),
    (19.2, 99, 175, "DISCIPLINE ISN'T THE FASTEST.", 44, WHITE, "s"),
    (20.8, 99, 245, "IT'S THE ONE STILL CLIMBING.", 50, GREEN, "k"),
]

def render(t):
    img = BG.copy(); d = days(t)
    chars = characters(d, t)
    # glow behind discipline
    ds = chars[-1][1]; gx, gy = step_xy(ds)
    gi = 0.55 + 0.45 * ease((t - 18.5) / 1.5)
    lay = Image.new("RGB", (W, H), (0, 0, 0))
    lay.paste(Image.new("RGB", GLOW.size, tuple(int(c * gi * 0.5) for c in GREEN)), (int(gx - 450), int(gy - 520)), GLOW)
    img = Image.fromarray(np.clip(np.asarray(img).astype(np.int16) + np.asarray(lay), 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(img)
    for t0, t1, y, text, size, col, wt in CAPS:
        if t0 <= t < t1:
            a = min(1, (t1 - t) / 0.3) if t0 == 0 else min(1, (t - t0) / 0.25, (t1 - t) / 0.3)
            rv = len(text) if t0 == 0 else min(len(text), int((t - t0) * 34) + 1)
            tracked(dr, (540, y), text, fnt(wt, size), with_alpha(col, a), track=0.08, anchor="c", reveal=rv)
    txt = f"DAY {max(1, int(d))}"
    if t < 18.9: tracked(dr, (540, 290), txt, fnt("s", 32), GREEN if d >= 365 else GREY, track=0.18, anchor="c")
    img = img.convert("RGBA")
    for name, s, p, a, col, note in chars:
        if a <= 0.01: continue
        fg, _ = bamboo.figure(rai=0, sad=p.get("sad", 0), cheer=p.get("cheer", 0), bob=0, walk=p.get("walk", 0), look=0)
        sc = 0.52
        fg = fg.resize((int(fg.width * sc), int(fg.height * sc)), Image.LANCZOS)
        if a < 1:
            fg = fg.copy(); fg.putalpha(fg.split()[3].point(lambda v: int(v * a)))
        x, y = step_xy(s)
        img.alpha_composite(fg, (int(x - fg.width / 2), int(y - fg.height + 8)))
        dr = ImageDraw.Draw(img)
        lc = col if name == "DISCIPLINE" else with_alpha(col, a)
        tracked(dr, (x, y - 180), name, fnt("s", 20), lc + (255,), track=0.15, anchor="c")
        if note and a > 0.3:
            tracked(dr, (x, y - 212), note[0], fnt("b", 22), with_alpha(note[1], a) + (255,), track=0.08, anchor="c")
        if name == "MOTIVATION" and note:
            # small rain cloud
            cx, cy = x, y - 265
            for ox, r in ((-26, 20), (0, 28), (26, 20)):
                dr.ellipse([cx + ox - r, cy - r, cx + ox + r, cy + r], fill=(70, 70, 80, 255))
            for k in range(6):
                ph = (t * 3 + k / 6) % 1
                dx = cx - 30 + k * 12; dy = cy + 20 + ph * 60
                dr.line([dx, dy, dx - 3, dy + 10], fill=(120, 150, 200, 255), width=2)
    img = img.convert("RGB")
    fa = min(1, (DUR - t) / 0.6)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img

def audio(path):
    SR = 44100; n = int(SR * DUR); tt = np.arange(n) / SR; out = np.zeros(n)
    def add(t0, sig):
        i = int(t0 * SR); j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    def tone(f, d, a, dec):
        x = np.arange(int(SR * d)) / SR; return a * np.sin(2 * np.pi * f * x) * np.exp(-x * dec)
    # soft footsteps for discipline
    for k in range(int(1.5 * 2), int(18.5 * 2)):
        add(k / 2, tone(300, 0.08, 0.05, 60))
    # events: find times when days cross thresholds
    ts = np.arange(0, DUR, 0.01); dd = np.array([days(x) for x in ts])
    for thr, f in ((7, 140), (21, 120), (60, 100), (200, 80)):
        te = ts[np.argmax(dd >= thr)]
        add(te, tone(f, 1.2, 0.35, 2.5)); add(te, tone(f * 1.5, 1.2, 0.15, 3))
    for t0, base in ((18.6, 523), (20.8, 659)):
        for mm, a in ((1, .12), (1.5, .07), (2, .05)): add(t0, tone(base * mm, 3.0, a, 1.3))
    out *= np.minimum(1, (DUR - tt) / 1.2); out = out / np.max(np.abs(out)) * 0.8
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((300 * len(ims), 533)).save("chk_climb.png")
    elif sys.argv[1] == "audio": audio("climb.wav")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
