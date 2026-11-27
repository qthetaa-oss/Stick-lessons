import sys, math, wave, subprocess
sys.path.insert(0, "/home/claude/vid"); sys.path.insert(0, "/home/claude/vid2")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from engine import fnt, tracked, W, H, FPS
import bamboo

DUR = 15.0
BPM = 120
BEAT = 60 / BPM
rng = np.random.default_rng(3)

# ---------- assets ----------
def make_bill(w=900, h=390, seed=0):
    r = np.random.default_rng(seed)
    im = Image.new("L", (w, h), 190); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=60, width=6)
    d.rectangle([22, 22, w - 23, h - 23], outline=110, width=3)
    for k in range(0, w, 9):  # guilloche lines
        d.line([k, 30, k + 40, h - 30], fill=170, width=1)
    cx, cy = w // 2, h // 2
    d.ellipse([cx - 120, cy - 140, cx + 120, cy + 140], fill=205, outline=70, width=5)
    # stick-figure portrait
    d.ellipse([cx - 45, cy - 95, cx + 45, cy - 5], fill=60)
    d.line([cx, cy - 5, cx, cy + 90], fill=60, width=22)
    d.line([cx - 70, cy + 120, cx, cy + 40, cx + 70, cy + 120], fill=60, width=20)
    f = fnt("k", 90)
    for (x, y) in ((40, 30), (w - 200, h - 130)):
        d.text((x, y), "100", font=f, fill=70)
    d.text((cx - 200, h - 70), "STICK LESSONS  RESERVE  NOTE", font=fnt("b", 26), fill=80)
    d.text((40, h - 70), f"SL {r.integers(10**7, 10**8)}", font=fnt("m", 26), fill=90)
    d.text((w - 330, 40), f"SL {r.integers(10**7, 10**8)}", font=fnt("m", 26), fill=90)
    return im.filter(ImageFilter.GaussianBlur(0.6))
BILLS = [make_bill(seed=i) for i in range(3)]

def stack_sprite(w=300, h=160, k=0):
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    top = BILLS[k % 3].resize((w, 130))
    im.paste(top, (0, 0))
    for y in range(130, h, 3):
        d.line([2, y, w - 3, y], fill=120 + (y % 6) * 12)
    d.rectangle([w // 2 - 26, 0, w // 2 + 26, h], fill=228)
    tracked(d, (w // 2, 52), "$10K", fnt("b", 18), 60, anchor="c")
    d.rectangle([0, 0, w - 1, h - 1], outline=30, width=2)
    return im
STACK = stack_sprite()
STACKS = [stack_sprite(k=i) for i in range(3)]

def zoom(im, s, cx=0.5, cy=0.5):
    w, h = im.size
    nw, nh = int(w / s), int(h / s)
    x0 = int((w - nw) * cx); y0 = int((h - nh) * cy)
    return im.crop((x0, y0, x0 + nw, y0 + nh)).resize((w, h), Image.BILINEAR)

def canvas(v=8): return Image.new("L", (W, H), v)

def big_text(im, text, size, y=None, fill=235, track=0.06):
    d = ImageDraw.Draw(im); f = fnt("k", size)
    if y is None: y = H // 2 - size // 2
    tracked(d, (W // 2, y), text, f, fill, track=track, anchor="c")
    return im

# ---------- scenes (local time u in seconds, dur) ----------
def sc_stacks(u, dur, txt=None):
    im = canvas(10)
    r3 = np.random.default_rng(5)
    for r in range(14):
        for c in range(5):
            x = c * 290 - 140 + (r % 2) * 145 + int(r3.uniform(-15, 15)); y = r * 150 - 80 + int(r3.uniform(-10, 10))
            st = STACKS[(r + c) % 3].rotate(r3.uniform(-4, 4), expand=True, fillcolor=0)
            im.paste(st, (x, y), st.point(lambda v: 255 if v > 0 else 0))
    im = zoom(im, 1.0 + 0.12 * u / dur, 0.5, 0.45)
    im = Image.eval(im, lambda v: int(v * 0.6))
    if txt: big_text(im, txt, 150)
    return im

def sc_bill(u, dur, k=0, txt=None):
    im = canvas(12)
    b = BILLS[k].resize((1800, 780)).rotate(-8 + 4 * k, expand=True, fillcolor=12)
    x = int(-500 + 220 * u / dur - 120 * k); y = H // 2 - b.height // 2
    im.paste(b, (x, y))
    im = Image.eval(im, lambda v: int(v * 0.8))
    if txt: big_text(im, txt, 150)
    return im

def sc_counter(u, dur):
    im = canvas(6); d = ImageDraw.Draw(im)
    # machine body
    d.rounded_rectangle([140, 900, 940, 1500], 40, fill=35, outline=70, width=6)
    d.rectangle([220, 1380, 860, 1440], fill=20)
    tracked(d, (540, 1395), f"{int(u * 240) % 100:02d}", fnt("k", 44), 200, anchor="c")
    # flipping bills
    for k in range(6):
        ph = (u * 14 + k / 6) % 1
        ang = -70 + 140 * ph
        b = BILLS[k % 3].resize((560, 240)).rotate(ang, expand=True, fillcolor=0)
        mask = b.point(lambda v: 255 if v > 0 else 0)
        im.paste(b, (540 - b.width // 2, 880 - b.height // 2 - int(80 * math.sin(ph * math.pi))), mask)
    return im

def sc_fan(u, dur):
    im = canvas(8)
    n = 9
    for k in range(n):
        ang = -60 + 120 * k / (n - 1) + 6 * math.sin(u * 3)
        b = BILLS[k % 3].resize((820, 350))
        base = Image.new("L", (1700, 1700), 0); base.paste(b, (850, 850 - 175))
        mask = Image.new("L", (1700, 1700), 0); ImageDraw.Draw(mask).rectangle([850, 675, 1670, 1025], fill=255)
        base = base.rotate(ang + 90, center=(850, 850)); mask = mask.rotate(ang + 90, center=(850, 850))
        im.paste(base, (540 - 850, 1250 - 850), mask)
    return zoom(im, 1.05 + 0.05 * u / dur)

def sc_streaks(u, dur):
    im = canvas(4); d = ImageDraw.Draw(im)
    r2 = np.random.default_rng(11)
    for k in range(40):
        y = int(r2.uniform(600, 1400)); sp = r2.uniform(1500, 4000); ln = r2.uniform(150, 600)
        x = (r2.uniform(0, W) + u * sp) % (W + 600) - 300
        c = int(r2.uniform(120, 255)); wdt = int(r2.uniform(2, 7))
        d.line([x, y, x + ln, y], fill=c, width=wdt)
    return im.filter(ImageFilter.GaussianBlur(2))

def sc_figure(u, dur, on_stack=False):
    im = canvas(5); d = ImageDraw.Draw(im)
    # spotlight
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cone = np.clip(1 - np.abs(xx - 540) / (80 + (yy - 200) * 0.32 + 1), 0, 1) * (yy > 200)
    im = Image.fromarray(np.clip(5 + 70 * cone, 0, 255).astype(np.uint8))
    if on_stack:
        for k in range(9):
            im.paste(STACK.resize((420, 120)), (330, 1700 - k * 115))
        fy = 1700 - 8 * 115 + 10
    else:
        fy = 1500
    fg, _ = bamboo.figure(rai=0, sad=0, cheer=1 if on_stack else 0, bob=0, walk=0 if on_stack else u * 9, look=0)
    fg = ImageOps.grayscale(fg.convert("RGBA").convert("RGB")).point(lambda v: v)
    alpha = bamboo.figure(rai=0, sad=0, cheer=1 if on_stack else 0, bob=0, walk=0 if on_stack else u * 9, look=0)[0].split()[3]
    sc = 1.5
    fg = fg.resize((int(fg.width * sc), int(fg.height * sc))); alpha = alpha.resize(fg.size)
    x = 540 - fg.width // 2 + (0 if on_stack else int(-120 + 240 * u / dur))
    im.paste(fg, (x, fy - fg.height + 30), alpha)
    return zoom(im, 1.0 + 0.06 * u / dur, 0.5, 0.55)

def sc_million(u, dur):
    im = canvas(6)
    v = int(1_000_000 * min(1, (u / (dur * 0.55)) ** 0.5))
    big_text(im, f"${v:,}", 140, fill=240)
    return im

def sc_text(u, dur, t1, t2=None):
    im = canvas(4)
    big_text(im, t1, 190, y=820 if t2 else None)
    if t2: big_text(im, t2, 72, y=1060, fill=200, track=0.12)
    return im

SCENES = [  # (duration in beats, fn)
    (2, lambda u, d: sc_stacks(u, d, "SAVE.")),
    (1, lambda u, d: sc_bill(u, d, 0)),
    (1, lambda u, d: sc_text(u, d, "INVEST.")),
    (1, sc_counter),
    (1, lambda u, d: sc_text(u, d, "WAIT.")),
    (1, sc_fan),
    (1, lambda u, d: sc_text(u, d, "REPEAT.")),
    (4, lambda u, d: sc_stacks(u, d)),
    (1, sc_streaks),
    (1, lambda u, d: sc_bill(u, d, 1)),
    (1, sc_counter),
    (1, lambda u, d: sc_figure(u, d)),
    (3, sc_million),
    (1, lambda u, d: sc_stacks(u, d)),
    (1, sc_fan),
    (1, sc_streaks),
    (3, lambda u, d: sc_figure(u, d, on_stack=True)),
    (5, lambda u, d: sc_text(u, d, "BORING", "MAKES MILLIONAIRES.") if u > 0.6 else sc_text(u, d, "BORING")),
]
TOT = sum(b for b, _ in SCENES)
assert abs(TOT * BEAT - DUR) < 1e-6, TOT * BEAT

GRAIN = [np.random.default_rng(i).normal(0, 9, (H // 2, W // 2)).astype(np.float32) for i in range(6)]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = np.clip(1.25 - np.sqrt(((xx - 540) / 700) ** 2 + ((yy - 960) / 1100) ** 2) * 0.8, 0.25, 1)

def render(t):
    acc = 0.0
    for beats, fn in SCENES:
        d = beats * BEAT
        if t < acc + d or (beats, fn) == SCENES[-1]:
            u = t - acc; im = fn(u, d); break
        acc += d
    a = np.asarray(im).astype(np.float32)
    # beat punch: brief brightness + zoom-in at each cut
    since = u
    punch = max(0, 1 - since / 0.12)
    a = a * (1 + 0.35 * punch)
    g = GRAIN[int(t * FPS) % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)
    a = (a + g) * VIGN
    # micro shake
    a = np.clip(a, 0, 255).astype(np.uint8)
    img = Image.fromarray(a)
    if punch > 0: img = zoom(img, 1 + 0.04 * punch)
    fa = min(1, (DUR - t) / 0.5)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img.convert("RGB")

def audio(path):
    SR = 44100; n = int(SR * DUR); out = np.zeros(n)
    def add(t0, sig):
        i = int(t0 * SR); j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    x = np.arange(int(SR * 0.5)) / SR
    kick = np.sin(2 * np.pi * (45 + 120 * np.exp(-x * 30)) * x) * np.exp(-x * 9) * 0.9
    xs = np.arange(int(SR * 0.25)) / SR
    snare = rng.normal(0, 1, len(xs)) * np.exp(-xs * 22) * 0.35 + np.sin(2 * np.pi * 190 * xs) * np.exp(-xs * 25) * 0.3
    xh = np.arange(int(SR * 0.05)) / SR
    hat = rng.normal(0, 1, len(xh)) * np.exp(-xh * 120) * 0.12
    hat = np.diff(np.concatenate([[0], hat]))  # brighten
    # dark bass / pad notes (D minor)
    notes = [38, 38, 41, 36]
    for bar in range(int(DUR / (4 * BEAT)) + 1):
        f = 440 * 2 ** ((notes[bar % 4] - 69) / 12)
        xb = np.arange(int(SR * 4 * BEAT)) / SR
        bass = (np.sin(2 * np.pi * f * xb) + 0.3 * np.sin(2 * np.pi * 2 * f * xb)) * 0.22 * np.minimum(1, xb * 20) * np.exp(-xb * 0.4)
        pad = sum(np.sin(2 * np.pi * f * m * 2 * xb) for m in (1, 1.189, 1.498)) * 0.04
        add(bar * 4 * BEAT, bass + pad)
    nb = int(DUR / BEAT)
    for b in range(nb):
        t0 = b * BEAT
        if b >= 2 and not (26 <= b < 28):
            add(t0, kick)
            if b % 2 == 1: add(t0, snare)
        for k in range(2): add(t0 + k * BEAT / 2, hat * 20)
    # riser into the million + final impact
    i0, i1 = int(9.0 * SR), int(9.5 * SR)
    xr = np.arange(i1 - i0) / SR; out[i0:i1] += rng.normal(0, 1, i1 - i0) * (xr / xr[-1]) ** 2 * 0.25
    add(12.5, kick * 1.3)
    out *= np.minimum(1, (DUR - np.arange(n) / SR) / 0.8)
    out = np.tanh(out * 1.2); out = out / np.max(np.abs(out)) * 0.9
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((240 * len(ims), 427)).save("chk_edit.png")
    elif sys.argv[1] == "audio": audio("edit.wav")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
