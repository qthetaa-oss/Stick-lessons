import sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SS = 3
F = "/usr/share/fonts/opentype/inter/"
_FC = {}
def fnt(w, size):
    k = (w, size)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(F + {"b": "Inter-Bold.otf", "s": "Inter-SemiBold.otf", "m": "Inter-Medium.otf", "k": "Inter-Black.otf"}[w], size)
    return _FC[k]

WHITE = (240, 240, 242); GREY = (150, 150, 158); DIM = (95, 95, 102)
GREEN = (57, 229, 140); RED = (235, 72, 72)
STACK_COLS = {"white": ((196, 198, 204), (150, 152, 160)), "green": (GREEN, (30, 150, 90)), "red": ((215, 80, 72), (150, 45, 40))}
FIG_X, STACK_X, STACK_W, NUM_X, LABEL_X = 230, 500, 170, 640, 92

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def ease_in(x): x = max(0, min(1, x)); return x ** 2.25
def lerp(p, q, f): return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)
def money(v): return "${:,.0f}".format(v)
def with_alpha(col, a): return tuple(int(c * a + 11 * (1 - a)) for c in col)

def interp(arr, m):
    m = max(0.0, min(len(arr) - 1.0, m)); i = int(m)
    if i >= len(arr) - 1: return arr[-1]
    f = m - i
    return arr[i] * (1 - f) + arr[i + 1] * f

def monthly_events():
    ev = []
    for k in range(1, 25):
        if k <= 12: ev.append((k, 2.5 + (k - 1) * 0.75, 0.55))
        else: ev.append((k, 11.5 + (k - 13) * 0.29, 0.27))
    return ev

def tracked(draw, xy, text, f, fill, track=0.12, anchor="l", reveal=None):
    sp = f.size * track
    widths = [f.getlength(c) for c in text]
    total = sum(widths) + sp * (len(text) - 1)
    x, y = xy
    if anchor == "c": x -= total / 2
    n = len(text) if reveal is None else reveal
    for i, c in enumerate(text[:n]):
        draw.text((x, y), c, font=f, fill=fill); x += widths[i] + sp
    return total

def make_bg(floors):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.full((H, W), 11.0, np.float32)
    d = np.sqrt(((xx - 540) / 620) ** 2 + ((yy - 380) / 520) ** 2)
    base += 26 * np.clip(1 - d, 0, 1) ** 1.6
    for fy in floors:
        d = np.sqrt(((xx - 520) / 520) ** 2 + ((yy - (fy - 120)) / 210) ** 2)
        base += 16 * np.clip(1 - d, 0, 1) ** 1.4
    v = np.sqrt(((xx - 540) / 760) ** 2 + ((yy - 960) / 1150) ** 2)
    base *= np.clip(1.25 - v * 0.75, 0.35, 1)
    im = Image.fromarray(np.clip(np.stack([base, base, base * 1.06], -1), 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    for fy in floors:
        dr.rectangle([70, fy, 1010, fy + 20], fill=(24, 24, 28))
        dr.rectangle([70, fy, 1010, fy + 3], fill=(48, 48, 54))
        dr.rectangle([70, fy + 20, 1010, fy + 32], fill=(15, 15, 18))
    return im

def figure_sprite(rai, sad, cheer, bob):
    w, h = 300, 360
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy = w / 2, h - 20
    hip = (0, -110 + bob * 0.5); neck = (sad * 14, -200 + bob + sad * 12)
    head = (sad * 26, -240 + bob + sad * 30); sh = (neck[0], neck[1] + 8)
    lhand = lerp((-40, -112 + bob), (-56, -260 + bob), cheer)
    lelb = lerp((-30, -155 + bob), (-48, -225 + bob), cheer)
    rhand = lerp(lerp((40, -112 + bob), (70, -250 + bob), rai), (56, -260 + bob), cheer)
    relb = lerp(lerp((30, -155 + bob), (58, -190 + bob), rai), (48, -225 + bob), cheer)
    if sad:
        lhand = lerp(lhand, (-4, -104 + bob), sad); rhand = lerp(rhand, (44, -104 + bob), sad)
    segs = [[hip, (-14, -55), (-30, 0)], [hip, (14, -55), (30, 0)], [hip, neck], [sh, lelb, lhand], [sh, relb, rhand]]
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
    return im.resize((w, h), Image.LANCZOS)

_FIG = {}
def figure(p):
    k = tuple(round(p.get(x, 0), 2) for x in ("raise", "sad", "cheer", "bob"))
    if k not in _FIG:
        if len(_FIG) > 4000: _FIG.clear()
        _FIG[k] = figure_sprite(*k)
    return _FIG[k]

def bill_sprite():
    w, h = 170, 76
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([2 * SS, 2 * SS, (w - 2) * SS, (h - 2) * SS], 10 * SS, fill=(10, 10, 12, 255))
    d.rounded_rectangle([7 * SS, 7 * SS, (w - 7) * SS, (h - 7) * SS], 6 * SS, fill=(226, 236, 228, 255))
    d.rounded_rectangle([15 * SS, 15 * SS, (w - 15) * SS, (h - 15) * SS], 4 * SS, outline=(150, 170, 155, 255), width=2 * SS)
    cx, cy, R = w / 2 * SS, h / 2 * SS, 21 * SS
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(40, 60, 48, 255))
    d.text((cx, cy), "$", font=fnt("b", 30 * SS), fill=(226, 236, 228, 255), anchor="mm")
    return im.resize((w, h), Image.LANCZOS)
BILL = bill_sprite()

def paste_bill(img, x, y, alpha=1.0, rot=0):
    b = BILL
    if alpha < 1 or rot:
        b = BILL.copy(); b.putalpha(b.split()[3].point(lambda v: int(v * alpha)))
        if rot: b = b.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.paste(b, (int(x - b.width / 2), int(y - b.height / 2)), b)

def draw_stack(img, dr, fy, hpx, col, lcol, glow=0.0, shake=0):
    if hpx < 1: return
    x0, x1 = STACK_X - STACK_W / 2 + shake, STACK_X + STACK_W / 2 + shake
    top = fy - hpx
    if glow > 0:
        pad = 80
        box = (int(x0 - pad), int(top - pad), int(x1 + pad), int(fy + 10))
        layer = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
        ImageDraw.Draw(layer).rectangle([pad, pad, pad + STACK_W, pad + hpx], fill=int(255 * min(1, glow)))
        layer = layer.filter(ImageFilter.GaussianBlur(34))
        region = img.crop(box)
        region = Image.composite(Image.new("RGB", region.size, col), region, layer.point(lambda v: v * 0.55))
        img.paste(region, box[:2])
    dr.rectangle([x0 - 4, top - 4, x1 + 4, fy], fill=(10, 10, 12))
    dr.rectangle([x0, top, x1, fy], fill=col)
    y = fy - 7
    while y > top + 3:
        dr.line([x0 + 6, y, x1 - 6, y], fill=lcol, width=2); y -= 7
    dr.rectangle([x0, top, x1, top + 3], fill=tuple(min(255, c + 25) for c in col))


class Video:
    """cfg keys: M, counter(m,t)->str, years, rows, captions, keys[(t,m)], events, scale_min, floors,
       crash(m)->row idx or None, final_t, dur, disclaimer, thuds"""
    def __init__(self, cfg):
        self.c = cfg
        self.c.setdefault("events", monthly_events())
        self.c.setdefault("floors", [840, 1200, 1560])
        self.c.setdefault("dur", 45.0)
        self.c.setdefault("final_t", 34.0)
        self.c.setdefault("scale_min", 6000)
        self.c.setdefault("crash", lambda m: None)
        self.c.setdefault("thuds", [])
        self.bg = make_bg(self.c["floors"])
        ts = np.arange(0, self.c["dur"] + 0.01, 1 / 120)
        self._ts = ts; self._ms = np.array([self.months(t) for t in ts])

    def months(self, t):
        keys = self.c["keys"]
        if t < keys[0][0]:
            return float(max([k for k, te, d in self.c["events"] if te + d <= t] + [0]))
        for (t0, m0), (t1, m1) in zip(keys, keys[1:]):
            if t < t1:
                x = (t - t0) / (t1 - t0)
                last = (t1, m1) == keys[-1]
                return m0 + (m1 - m0) * (ease_in(x) ** 0.8 if last and m1 - m0 > 60 else ease(x))
        return float(keys[-1][1])

    def time_of(self, m):
        idx = np.argmax(self._ms >= m - 1e-6)
        return self._ts[idx] if self._ms[idx] >= m - 1e-6 else 1e9

    def render(self, t):
        c = self.c
        img = self.bg.copy(); dr = ImageDraw.Draw(img)
        m = self.months(t)
        fin = ease((t - c["final_t"]) / 1.2)
        for t0, t1, y, text, size, col, wt in c["captions"]:
            if t0 <= t < t1:
                a = min(1, (t - t0) / 0.25, (t1 - t) / 0.3) if t0 > 0 else min(1, (t1 - t) / 0.3)
                rv = len(text) if t0 == 0 else min(len(text), int((t - t0) * 34) + 1)
                tracked(dr, (540, y), text, fnt(wt, size), with_alpha(col, a), track=0.1, anchor="c", reveal=rv)
        ctop = 392
        tracked(dr, (540, ctop), c["counter"](m, t), fnt("s", 30), GREY, track=0.18, anchor="c")
        ny = c["years"]; gap = 6; seg_w = (800 - gap * (ny - 1)) / ny
        x = 540 - 400
        for i in range(ny):
            f = max(0, min(1, m / 12 - i))
            dr.rectangle([x, ctop + 52, x + seg_w, ctop + 58], fill=(38, 38, 44))
            if f > 0: dr.rectangle([x, ctop + 52, x + seg_w * f, ctop + 58], fill=GREEN if f >= 1 else (120, 200, 160))
            x += seg_w + gap
        rows = c["rows"]
        vals = [interp(r["value"], m) if "value" in r else 0 for r in rows]
        cur_max = max([v for v, r in zip(vals, rows) if r.get("stack")] + [c["scale_min"]])
        scale = 250 / cur_max
        crash_row = c["crash"](m) if t < c["final_t"] else None
        for i, (r, fy) in enumerate(zip(rows, c["floors"])):
            tracked(dr, (LABEL_X, fy - 312), r["name"], fnt("s", 24), GREEN if r.get("accent") else GREY, track=0.2)
            if r.get("stack"):
                col, lcol = STACK_COLS[r["stack"]]
                shake = 0
                if crash_row == i:
                    col, lcol = STACK_COLS["red"]; shake = int(4 * math.sin(t * 60))
                glow = 0
                if r["stack"] == "green" and crash_row != i:
                    glow = 0.35 + 0.65 * fin * (0.8 + 0.2 * math.sin(t * 3))
                draw_stack(img, dr, fy, vals[i] * scale, col, lcol, glow=glow, shake=shake)
            txt, col = r["num"](m, vals[i], i == crash_row)
            dr.text((NUM_X, fy - 190), txt, font=fnt("b", 66), fill=col)
            stx, scol = r["sub"](m, vals[i])
            tracked(dr, (NUM_X + 2, fy - 105), stx, fnt("m", 22), scol, track=0.12)
        raise_amt = [0.0] * len(rows)
        for k, te, d in c["events"]:
            if not (te - 0.2 <= t <= te + d + 0.9): continue
            p = (t - te) / d
            for i, (r, fy) in enumerate(zip(rows, c["floors"])):
                mode = r.get("mode", lambda k: None)(k)
                if mode == "deposit" and 0 < p < 1:
                    top = fy - vals[i] * scale
                    y0 = fy - 440
                    paste_bill(img, STACK_X, y0 + (top - 38 - y0) * ease(p) ** 1.6)
                elif mode == "spend":
                    raise_amt[i] = max(raise_amt[i], ease(1 - abs(p - 0.9) * 2.2))
                    if 0 < p < 1:
                        x0, y0, tx, ty = FIG_X + 40, fy - 420, FIG_X + 60, fy - 270
                        paste_bill(img, x0 + (tx - x0) * ease(p), y0 + (ty - y0) * ease(p) ** 1.5)
                    p2 = (t - te - d) / 0.7
                    if 0 <= p2 <= 1:
                        x = FIG_X + 60 + 520 * ease(p2); y = fy - 270 - 72 * math.sin(p2 * math.pi)
                        if p2 < 0.75: paste_bill(img, x, y, alpha=1 - p2 / 0.75, rot=-30 * p2)
                        tracked(dr, (NUM_X + 2, fy - 250 - 40 * p2), r["amt"], fnt("b", 34), with_alpha(RED, 1 - p2), track=0.05)
                elif mode == "pay":
                    raise_amt[i] = max(raise_amt[i], ease(1 - abs(p - 0.1) * 2.0))
                    if 0 < p < 1:
                        top = fy - vals[i] * scale
                        x = FIG_X + 70 + (STACK_X - FIG_X - 70) * ease(p)
                        y = (fy - 250) + ((top - 20) - (fy - 250)) * ease(p) - 40 * math.sin(p * math.pi)
                        paste_bill(img, x, y, alpha=1 - max(0, p - 0.7) / 0.3)
        if c["keys"][0][0] <= t < c["keys"][-1][0] + 0.1:
            frac = (m / 12) % 1.0
            for i, (r, fy) in enumerate(zip(rows, c["floors"])):
                if r.get("float") and r.get("mode", lambda k: None)(int(m) + 1) == "spend" and m < c["M"] - 1:
                    tracked(dr, (NUM_X + 2, fy - 250 - 40 * frac), r["float"], fnt("b", 34), with_alpha(RED, (1 - frac) * 0.9), track=0.05)
        bob = 3 * math.sin(t * 2.2)
        img = img.convert("RGBA")
        for i, (r, fy) in enumerate(zip(rows, c["floors"])):
            p = {"raise": raise_amt[i], "bob": bob * (1 - 0.1 * i)}
            fp = r.get("final")
            if fp == "sad": p["sad"] = fin
            if fp == "cheer": p["cheer"] = fin * ease((t - c["final_t"] - 0.5) / 1.0)
            if "cheer_at" in r:
                tc = self.time_of(r["cheer_at"])
                p["cheer"] = max(p.get("cheer", 0), ease((t - tc - 0.2) / 0.6))
            fg = figure(p)
            img.alpha_composite(fg, (int(FIG_X - fg.width / 2), int(fy - fg.height + 20)))
        img = img.convert("RGB"); dr = ImageDraw.Draw(img)
        dt = c["final_t"] + 6.5
        if t > dt:
            a = min(1, (t - dt) / 0.6)
            for j, line in enumerate(c["disclaimer"]):
                tracked(dr, (540, 1700 + 30 * j), line, fnt("m", 19), with_alpha(DIM, a), track=0.08, anchor="c")
        fa = min(1, (t / 0.4) if c.get("fade_in", True) else 1, (c["dur"] - t) / 0.6)
        if fa < 1: img = Image.eval(img, lambda v: int(v * fa))
        return img

    def audio(self, path):
        SR = 44100; dur = self.c["dur"]; n = int(SR * dur); t = np.arange(n) / SR
        out = np.zeros(n)
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
        for f, a in ((55, .10), (82.4, .06), (110, .035), (164.8, .02)):
            out += a * lfo * np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 0.13 * t))
        def add(t0, sig):
            i = int(t0 * SR); j = min(n, i + len(sig))
            if i < n: out[i:j] += sig[:j - i]
        def tone(f, d, a, decay):
            tt = np.arange(int(SR * d)) / SR; return a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)
        for k, te, d in self.c["events"]:
            add(te + d, tone(1800, 0.05, 0.18, 90)); add(te + d, tone(900, 0.08, 0.12, 60)); add(te + d + 0.02, tone(2400, 0.4, 0.05, 12))
        for r in self.c["rows"]:
            if "cheer_at" in r:
                tc = self.time_of(r["cheer_at"])
                if tc < dur - 2:
                    for mm, a in ((1, .10), (1.25, .07), (1.5, .06)): add(tc, tone(660 * mm, 1.5, a, 2.5))
        for tt0 in self.c["thuds"]:
            tt = np.arange(int(SR * 1.6)) / SR; add(tt0, 0.5 * np.sin(2 * np.pi * (60 - 25 * tt) * tt) * np.exp(-tt * 2.5))
        keys = self.c["keys"]
        s0, s1 = keys[-2][0], keys[-1][0]
        if s1 - s0 > 3:
            i0, i1 = int(s0 * SR), int(s1 * SR); tt = np.arange(i1 - i0) / SR; L = tt[-1]
            ph = 2 * np.pi * np.cumsum(110 + 330 * (tt / L) ** 2) / SR; env = (tt / L) ** 1.5 * 0.12
            out[i0:i1] += env * (np.sin(ph) + 0.5 * np.sin(2 * ph))
        fins = sorted({cp[0] for cp in self.c["captions"] if cp[0] >= self.c["final_t"]})
        for t0, base in zip(fins, (440, 494, 587)):
            for mm, a in ((1, .12), (1.5, .07), (2, .05)): add(t0, tone(base * mm, 3.0, a, 1.4))
        out *= np.minimum(1, np.minimum(t / 0.5, (dur - t) / 1.2))
        out = out / np.max(np.abs(out)) * 0.8
        st = (np.stack([out, out], 1) * 32767).astype(np.int16)
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

    def encode(self, t0, t1, out):
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)):
            p.stdin.write(self.render(n / FPS).tobytes())
        p.stdin.close(); return p.wait()
