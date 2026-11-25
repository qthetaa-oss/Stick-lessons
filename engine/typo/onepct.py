import sys, math, wave, subprocess
sys.path.insert(0, "/home/claude/vid"); sys.path.insert(0, "/home/claude/vid2")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import fnt, tracked, ease, W, H, FPS
import bamboo

DUR = 32.0
BGC = 6

def bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 540) / 700) ** 2 + ((yy - 900) / 900) ** 2)
    b = BGC + 10 * np.clip(1 - d, 0, 1)
    return Image.fromarray(np.stack([b, b, b], -1).astype(np.uint8))
BG = bg()

def win(t, a, b, fi=0.35, fo=0.35):
    if t < a or t > b: return 0.0
    return min(1, (t - a) / fi, (b - t) / fo)

def text(img, s, y, size, a, wt="k", glow=True, track=0.08, col=255):
    if a <= 0: return img
    f = fnt(wt, size)
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    tracked(d, (540, y), s, f, int(col * a), track=track, anchor="c")
    if glow:
        g = lay.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.9))
        lay = Image.fromarray(np.clip(np.asarray(lay).astype(np.int16) + np.asarray(g), 0, 255).astype(np.uint8))
    arr = np.maximum(np.asarray(img), np.asarray(lay)[..., None])
    return Image.fromarray(arr.astype(np.uint8))

def pill(dr, s, cx, y, size, a, inv=False):
    if a <= 0: return
    f = fnt("s", size)
    w = tracked(ImageDraw.Draw(Image.new("L", (1, 1))), (0, 0), s, f, 0, track=0.14)
    v = int(235 * a)
    if inv:
        dr.rounded_rectangle([cx - w / 2 - size, y - size * 0.55, cx + w / 2 + size, y + size * 1.45], int(size), outline=(v, v, v), width=3)
        tracked(dr, (cx, y), s, f, (v, v, v), track=0.14, anchor="c")
    else:
        dr.rounded_rectangle([cx - w / 2 - size * 0.8, y - size * 0.45, cx + w / 2 + size * 0.8, y + size * 1.4], int(size), fill=(v, v, v))
        tracked(dr, (cx, y), s, f, (BGC, BGC, BGC), track=0.14, anchor="c")

def mini_fig(img, x, yfeet, t, walking, scale=0.32, a=1.0, cheer=0, sad=0):
    fg, _ = bamboo.figure(rai=0, sad=sad, cheer=cheer, bob=0, walk=(t * 9) if walking else 0, look=0)
    fg = fg.resize((int(fg.width * scale), int(fg.height * scale)), Image.LANCZOS)
    if a < 1: fg = fg.copy(); fg.putalpha(fg.split()[3].point(lambda v: int(v * a)))
    img = img.convert("RGBA"); img.alpha_composite(fg, (int(x - fg.width / 2), int(yfeet - fg.height + 20 * scale)))
    return img.convert("RGB")

X0, X1 = 150, 930
def days_up(t):
    if t < 6.8: return 0
    if t < 10.5: return 60 * ease((t - 6.8) / 3.7)
    if t < 13.6: return 60 + 120 * ease((t - 10.5) / 3.1)
    if t < 16.0: return 180 + 185 * ease((t - 13.6) / 2.4)
    return 365
def days_dn(t):
    if t < 20.6: return 0
    return 365 * ease((t - 20.6) / 3.6)

def curve(dr, fn, d, ybase, ytop, vmax, a, width=5):
    pts = []
    for k in range(0, int(d) + 1, 2):
        v = fn(k); pts.append((X0 + (X1 - X0) * k / 365, ybase - (ybase - ytop) * (v - 0) / vmax))
    v = fn(d); pts.append((X0 + (X1 - X0) * d / 365, ybase - (ybase - ytop) * v / vmax))
    c = int(240 * a)
    if len(pts) > 1: dr.line(pts, fill=(c, c, c), width=width, joint="curve")
    return pts[-1]

def render(t):
    img = BG.copy()
    # S1
    img = text(img, "1% BETTER", 820, 130, win(t, 0.3, 3.3) * ease((t - 0.3) / 0.6))
    a = win(t, 1.4, 3.3); dr = ImageDraw.Draw(img); pill(dr, "EVERY DAY", 540, 1000, 30, a)
    # S2
    img = text(img, "NOBODY NOTICES.", 900, 84, win(t, 3.6, 6.2))
    # S3 graph up
    ga = win(t, 6.4, 18.0, 0.4, 0.5)
    if ga > 0:
        dr = ImageDraw.Draw(img); c = int(90 * ga)
        ybase, ytop = 1250, 560
        dr.line([X0, ybase, X1, ybase], fill=(c, c, c), width=3)
        dr.line([X0, ybase, X0, ytop - 40], fill=(c, c, c), width=3)
        d = days_up(t)
        hx, hy = curve(dr, lambda k: 1.01 ** k, d, ybase, ytop, 1.01 ** 365, ga)
        if d < 364:
            img = mini_fig(img, hx, hy, t, True, a=ga)
        else:
            img = mini_fig(img, hx, hy, t, False, a=ga, cheer=ease((t - 16.0) / 0.6))
        dr = ImageDraw.Draw(img)
        pill(dr, f"DAY {int(d)}", 540, 430, 26, ga)
        mult = 1.01 ** d
        img = text(img, f"{mult:.1f}x", 1330, 72 if d < 364 else 110, ga, glow=d >= 364)
        img = text(img, "STILL NOTHING.", 520 if False else 1490, 40, win(t, 8.6, 10.6), wt="s", glow=False, track=0.12, col=170)
        img = text(img, "THEN IT STARTS TO SHOW.", 1490, 40, win(t, 12.2, 15.4), wt="s", glow=False, track=0.12, col=170)
        img = text(img, "ONE YEAR. ALMOST 38 TIMES BETTER.", 1490, 40, win(t, 16.2, 18.0), wt="s", glow=False, track=0.12)
    # S4
    img = text(img, "AND 1% WORSE?", 900, 96, win(t, 18.3, 20.4))
    gb = win(t, 20.4, 25.4, 0.4, 0.5)
    if gb > 0:
        dr = ImageDraw.Draw(img); c = int(90 * gb)
        ybase, ytop = 1250, 640
        dr.line([X0, ybase, X1, ybase], fill=(c, c, c), width=3)
        dr.line([X0, ybase, X0, ytop - 40], fill=(c, c, c), width=3)
        d = days_dn(t)
        hx, hy = curve(dr, lambda k: 0.99 ** k, d, ybase, ytop, 1.0, gb * 0.75)
        img = mini_fig(img, hx, hy, t, d < 364, a=gb, sad=ease((t - 24.2) / 0.6))
        dr = ImageDraw.Draw(img)
        pill(dr, f"DAY {int(d)}", 540, 430, 26, gb, inv=True)
        img = text(img, f"{0.99 ** d:.2f}x", 1330, 72, gb * 0.8, glow=False, col=200)
    # S5
    img = text(img, "SAME 365 DAYS.", 840, 80, win(t, 25.7, 28.4))
    img = text(img, "OPPOSITE ENDINGS.", 950, 80, win(t, 26.5, 28.4), col=150, glow=False)
    # S6
    a = win(t, 28.7, 99, 0.4, 0.1)
    if a > 0:
        img = text(img, "1% IS ENOUGH.", 800, 44, a, wt="s", glow=False, track=0.14, col=190)
        press = 1 - 0.06 * math.sin(max(0, min(1, (t - 30.0) / 0.3)) * math.pi)
        s = int(52 * press)
        lay = Image.new("RGB", (W, H), (0, 0, 0)); pill(ImageDraw.Draw(lay), "START TODAY", 540, 905, s, a)
        g = lay.filter(ImageFilter.GaussianBlur(26))
        arr = np.clip(np.asarray(img).astype(np.int16) + (np.asarray(g) * 0.6).astype(np.int16), 0, 255).astype(np.uint8)
        img = Image.fromarray(arr); dr = ImageDraw.Draw(img); pill(dr, "START TODAY", 540, 905, s, a)
    fa = min(1, t / 0.3, (DUR - t) / 0.6)
    if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
    return img

def audio(path):
    SR = 44100; n = int(SR * DUR); tt = np.arange(n) / SR; out = np.zeros(n)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * tt)
    for f, a in ((65.4, .09), (98, .05), (130.8, .03)): out += a * lfo * np.sin(2 * np.pi * f * tt)
    def add(t0, sig):
        i = int(t0 * SR); j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    def tone(f, d, a, dec):
        x = np.arange(int(SR * d)) / SR; return a * np.sin(2 * np.pi * f * x) * np.exp(-x * dec)
    for t0 in (0.3, 3.6, 6.4, 18.3, 20.4, 25.7, 26.5): add(t0, tone(880, 0.25, 0.08, 14)); add(t0, tone(440, 0.4, 0.06, 8))
    i0, i1 = int(10.5 * SR), int(16.0 * SR); x = np.arange(i1 - i0) / SR; L = x[-1]
    ph = 2 * np.pi * np.cumsum(130 + 400 * (x / L) ** 2) / SR; out[i0:i1] += (x / L) ** 2 * 0.12 * np.sin(ph)
    for mm, a in ((1, .12), (1.5, .07), (2, .05)): add(16.0, tone(523 * mm, 3.0, a, 1.3))
    i0, i1 = int(20.6 * SR), int(24.2 * SR); x = np.arange(i1 - i0) / SR; L = x[-1]
    ph = 2 * np.pi * np.cumsum(300 - 220 * (x / L)) / SR; out[i0:i1] += 0.06 * np.sin(ph)
    x = np.arange(int(SR * 1.5)) / SR; add(24.2, 0.4 * np.sin(2 * np.pi * (60 - 20 * x) * x) * np.exp(-x * 2.5))
    for mm, a in ((1, .12), (1.25, .08), (1.5, .07)): add(28.7, tone(440 * mm, 3.0, a, 1.2))
    add(30.0, tone(1200, 0.12, 0.15, 40))
    out *= np.minimum(1, np.minimum(tt / 0.5, (DUR - tt) / 1.2)); out = out / np.max(np.abs(out)) * 0.8
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((300 * len(ims), 533)).save("chk.png")
    elif sys.argv[1] == "audio": audio("onepct.wav")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
