import sys, math, subprocess
sys.path.insert(0, "/home/claude/vid"); sys.path.insert(0, "/home/claude/vid2")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import fnt, tracked, W, H, FPS
import bamboo

DUR = 32.0
rng = np.random.default_rng(7)
VP = (540, 760)                      # vanishing point
BW = (170, 380, 910, 1150)           # back wall rect

def lerp(a, b, f): return a + (b - a) * f
def grad(h, w, c0, c1, horiz=False):
    f = np.linspace(0, 1, w if horiz else h, dtype=np.float32)
    g = (np.array(c0, np.float32)[None, :] * (1 - f[:, None]) + np.array(c1, np.float32)[None, :] * f[:, None])
    if horiz: return np.broadcast_to(g[None, :, :], (h, w, 3)).copy()
    return np.broadcast_to(g[:, None, :], (h, w, 3)).copy()

def radial(cx, cy, r, col, strength=1.0, shape=1.6):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** shape * strength
    return a[..., None] * np.array(col, np.float32)[None, None, :]

def city_window(w, h, mode):
    """returns RGB array of the view through the window"""
    if mode == "morning":
        sky = grad(h, w, (40, 60, 110), (255, 170, 110))
    elif mode == "rain":
        sky = grad(h, w, (10, 14, 24), (30, 36, 52))
    else:
        sky = grad(h, w, (6, 10, 26), (24, 34, 70))
    im = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(2)
    for layer, (base, col, lit) in enumerate([(0.55, (22, 26, 40), 0.25), (0.7, (14, 16, 26), 0.35)]):
        x = -20
        while x < w:
            bw = int(r.uniform(40, 110)); bh = int(h * r.uniform(0.2, base))
            top = h - bh
            c = col if mode != "morning" else tuple(int(v * 2.2) for v in col)
            d.rectangle([x, top, x + bw, h], fill=c)
            for wy in range(top + 8, h - 6, 14):
                for wx in range(x + 6, x + bw - 6, 12):
                    if r.random() < (lit if mode != "morning" else 0.08):
                        d.rectangle([wx, wy, wx + 5, wy + 7], fill=(255, 210, 130))
            x += bw + int(r.uniform(2, 14))
    if mode == "morning":
        d.ellipse([w * 0.55, h * 0.45, w * 0.55 + 120, h * 0.45 + 120], fill=(255, 230, 180))
    return im.filter(ImageFilter.GaussianBlur(3))

def room(mode):
    """pre-render background (walls, window, floor) — blurred for depth of field"""
    a = np.zeros((H, W, 3), np.float32)
    wall = (34, 38, 48) if mode != "morning" else (70, 58, 52)
    a[:] = wall
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = BW
    # side walls / floor / ceiling as perspective polygons
    d.polygon([(0, 0), (x0, y0), (x0, y1), (0, H)], fill=tuple(int(v * 0.75) for v in wall))
    d.polygon([(W, 0), (x1, y0), (x1, y1), (W, H)], fill=tuple(int(v * 0.7) for v in wall))
    d.polygon([(0, 0), (W, 0), (x1, y0), (x0, y0)], fill=tuple(int(v * 0.55) for v in wall))
    floor = (26, 22, 20) if mode != "morning" else (60, 44, 34)
    d.polygon([(0, H), (x0, y1), (x1, y1), (W, H)], fill=floor)
    for k in range(-8, 9):  # floor boards
        d.line([(540 + k * 160, H), (VP[0] + k * 46, y1)], fill=tuple(int(v * 0.8) for v in floor), width=3)
    # window
    wx0, wy0, wx1, wy1 = 300, 470, 780, 900
    view = city_window(wx1 - wx0, wy1 - wy0, mode)
    im.paste(view, (wx0, wy0))
    d.rectangle([wx0 - 10, wy0 - 10, wx1 + 10, wy1 + 10], outline=(12, 12, 16), width=14)
    d.line([(540, wy0), (540, wy1)], fill=(12, 12, 16), width=10)
    # shelf + plant silhouettes on side wall
    d.polygon([(60, 640), (150, 660), (150, 680), (60, 662)], fill=(20, 18, 18))
    d.rectangle([80, 1080, 150, 1180], fill=(24, 20, 18))
    d.ellipse([60, 960, 170, 1090], fill=(18, 40, 26) if mode != "morning" else (40, 80, 50))
    a = np.asarray(im).astype(np.float32)
    # lighting
    if mode == "morning":
        a = a * 0.9 + radial(560, 690, 900, (255, 160, 90), 0.55)
        a += radial(540, 700, 420, (255, 200, 140), 0.35)
    else:
        a = a * 0.75 + radial(330, 1180, 700, (255, 170, 90), 0.42 if mode == "night" else 0.25)
        a += radial(540, 690, 450, (60, 90, 160), 0.18)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return img.filter(ImageFilter.GaussianBlur(5))

def rooftop():
    sky = grad(H, W, (30, 40, 90), (255, 160, 100))
    sky[int(H * 0.55):] = grad(H - int(H * 0.55), W, (255, 160, 100), (255, 200, 150))
    im = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([620, 980, 820, 1180], fill=(255, 236, 200))
    r = np.random.default_rng(9)
    for layer, (h0, h1, col) in enumerate([(0.18, 0.38, (120, 80, 90)), (0.12, 0.3, (60, 40, 55)), (0.08, 0.22, (30, 22, 32))]):
        x = -30
        while x < W:
            bw = int(r.uniform(60, 160)); bh = int(H * r.uniform(h0, h1))
            d.rectangle([x, 1250 - bh + layer * 60, x + bw, 1500], fill=col)
            x += bw + int(r.uniform(0, 20))
    im = im.filter(ImageFilter.GaussianBlur(4)); d = ImageDraw.Draw(im)
    a = np.asarray(im).astype(np.float32) + radial(720, 1080, 900, (255, 170, 100), 0.45)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    # rooftop ledge (sharp, foreground)
    d.polygon([(0, 1500), (W, 1440), (W, H), (0, H)], fill=(24, 20, 24))
    d.polygon([(0, 1500), (W, 1440), (W, 1470), (0, 1530)], fill=(70, 50, 50))
    return im

BGS = {m: room(m) for m in ("night", "rain", "morning")}
ROOF = rooftop()

def zoom(im, s, cx=0.5, cy=0.5):
    w, h = im.size; nw, nh = int(w / s), int(h / s)
    x0 = int((w - nw) * cx); y0 = int((h - nh) * cy)
    return im.crop((x0, y0, x0 + nw, y0 + nh)).resize((w, h), Image.BICUBIC)

DESK_TOP, DESK_FRONT = 1330, 1400

def draw_desk(im, stacks=0, cups=1, laptop_glow=1.0, mode="night", lamp_on=True, ui=None):
    d = ImageDraw.Draw(im)
    wood = (58, 40, 30) if mode != "morning" else (95, 66, 46)
    d.polygon([(90, DESK_TOP), (990, DESK_TOP), (1040, DESK_FRONT), (40, DESK_FRONT)], fill=wood)
    d.rectangle([40, DESK_FRONT, 1040, 1760], fill=tuple(int(v * 0.6) for v in wood))
    d.line([(40, DESK_FRONT), (1040, DESK_FRONT)], fill=tuple(min(255, int(v * 1.6)) for v in wood), width=4)
    # lamp
    d.line([(200, DESK_TOP + 10), (230, 1150), (320, 1080)], fill=(20, 20, 22), width=12)
    d.polygon([(280, 1050), (380, 1060), (360, 1120), (300, 1110)], fill=(30, 30, 34))
    if lamp_on:
        d.ellipse([310, 1100, 350, 1125], fill=(255, 220, 150))
    # laptop
    d.polygon([(560, DESK_TOP + 18), (840, DESK_TOP + 18), (860, DESK_TOP + 38), (540, DESK_TOP + 38)], fill=(40, 42, 48))
    d.polygon([(585, DESK_TOP + 18), (815, DESK_TOP + 18), (800, 1130), (600, 1130)], fill=(28, 30, 36))
    g = int(120 * laptop_glow)
    d.polygon([(600, DESK_TOP + 10), (800, DESK_TOP + 10), (788, 1142), (612, 1142)], fill=(40 + g // 3, 60 + g // 2, 90 + g))
    if ui:
        title, prog, money = ui
        c = (235, 240, 255) if laptop_glow > 0.5 else (150, 160, 180)
        tracked(d, (700, 1158), title, fnt("b", 17), c, track=0.08, anchor="c")
        d.rectangle([625, 1205, 775, 1217], fill=(20, 30, 50))
        d.rectangle([625, 1205, 625 + int(150 * prog), 1217], fill=(57, 229, 140))
        tracked(d, (700, 1235), money, fnt("k", 34), (57, 229, 140) if laptop_glow > 0.5 else (90, 140, 110), track=0.02, anchor="c")
    # money stacks
    for k in range(stacks):
        col, row = k % 4, k // 4
        x = 880 - col * 0 + (k % 2) * 6 + (k // 2) * 0
        x = 870 + (k % 2) * 70
        y = DESK_TOP + 20 - (k // 2) * 34
        d.rectangle([x, y - 30, x + 62, y], fill=(70, 110, 70), outline=(20, 30, 20), width=2)
        d.rectangle([x + 24, y - 30, x + 38, y], fill=(220, 220, 200))
    # coffee cups
    for k in range(cups):
        x = 420 + k * 34; y = DESK_TOP + 30 - (k % 2) * 6
        d.rectangle([x, y - 38, x + 26, y], fill=(225, 225, 220), outline=(40, 40, 40), width=2)
        d.arc([x + 20, y - 30, x + 38, y - 12], 270, 90, fill=(225, 225, 220), width=4)

def light(im, mode, laptop_glow, t):
    a = np.asarray(im).astype(np.float32)
    if mode in ("night", "rain"):
        flick = 1.0 + 0.03 * math.sin(t * 13)
        a += radial(330, 1110, 520, (255, 170, 80), 0.55 * flick if mode == "night" else 0.35)
        a += radial(700, 1180, 380, (70, 120, 220), 0.35 * laptop_glow)
    else:
        a += radial(560, 700, 1000, (255, 170, 100), 0.25)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def figure(pose, scale=1.7):
    fg, _ = bamboo.figure(rai=pose.get("rai", 0), sad=pose.get("sad", 0), cheer=pose.get("cheer", 0),
                          bob=pose.get("bob", 0), walk=pose.get("walk", 0), look=pose.get("look", 0))
    return fg.resize((int(fg.width * scale), int(fg.height * scale)), Image.LANCZOS)

def calendar(im, day, mode):
    d = ImageDraw.Draw(im)
    x, y = 960, 820
    d.polygon([(x, y), (x + 90, y - 20), (x + 90, y + 120), (x, y + 140)], fill=(225, 220, 210) if mode != "rain" else (150, 150, 150))
    d.polygon([(x, y), (x + 90, y - 20), (x + 90, y + 10), (x, y + 30)], fill=(190, 60, 60))
    tracked(d, (x + 45, y + 55), f"{day}", fnt("k", 40 if day < 100 else 32), (40, 40, 40), track=0.0, anchor="c")

def grade(im, t):
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) if not hasattr(grade, "v") else (None, None)
    if not hasattr(grade, "v"):
        grade.v = np.clip(1.3 - np.sqrt(((xx - 540) / 760) ** 2 + ((yy - 960) / 1150) ** 2) * 0.85, 0.3, 1)[..., None]
        grade.g = [np.random.default_rng(i).normal(0, 6, (H // 2, W // 2, 1)).astype(np.float32) for i in range(5)]
    g = np.repeat(np.repeat(grade.g[int(t * FPS) % 5], 2, 0), 2, 1)
    a = (a + g) * grade.v
    a[..., 2] *= 1.04; a[..., 0] *= 1.02
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def rain_overlay(im, t):
    d = ImageDraw.Draw(im)
    for k in range(70):
        r = np.random.default_rng(k)
        x = 300 + r.uniform(0, 480); sp = r.uniform(500, 900)
        y = 470 + (r.uniform(0, 430) + t * sp) % 430
        d.line([x, y, x - 4, y + 22], fill=(150, 170, 200), width=2)
    return im

SCENES = [(0, 6.5), (6.5, 13), (13, 19), (19, 25.5), (25.5, 32)]

def scene_room(t, u, mode, day, stacks, cups, pose, glow=1.0, zoom_s=(1.0, 1.08), ui=None):
    im = BGS[mode].copy()
    if mode == "rain": im = rain_overlay(im, t)
    calendar(im, day, mode)
    fg = figure(pose)
    im = im.convert("RGBA")
    im.alpha_composite(fg, (int(540 - fg.width / 2 - 60), int(DESK_TOP + 230 - fg.height)))
    im = im.convert("RGB")
    draw_desk(im, stacks, cups, glow, mode, lamp_on=mode != "morning", ui=ui)
    im = light(im, mode, glow, t)
    return zoom(im, lerp(zoom_s[0], zoom_s[1], u), 0.5, 0.62)

CAPS = [
    (0.0, 6.3, 250, "9-TO-5 JOB. NO FREE TIME.", 58, (245, 245, 245), "k"),
    (2.2, 6.3, 325, "BUT EVERY NIGHT: 1 HOUR.", 58, (57, 229, 140), "k"),
    (6.7, 12.8, 250, "NO ONE SAW IT.", 58, (245, 245, 245), "k"),
    (8.6, 12.8, 325, "HE KEPT GOING ANYWAY.", 58, (245, 245, 245), "k"),
    (13.3, 18.8, 250, "DAY 180.", 58, (245, 245, 245), "k"),
    (14.6, 18.8, 325, "IT FELT POINTLESS.", 58, (235, 90, 90), "k"),
    (19.3, 25.3, 250, "DAY 365.", 58, (245, 245, 245), "k"),
    (21.0, 25.3, 325, "HIS SIDE BUSINESS: $10,000.", 52, (57, 229, 140), "k"),
    (25.8, 99, 250, "1 HOUR A DAY", 64, (245, 245, 245), "k"),
    (27.0, 99, 335, "= 365 HOURS A YEAR.", 54, (245, 245, 245), "k"),
    (28.8, 99, 1650, "START TONIGHT.", 76, (57, 229, 140), "k"),
]

def captions(im, t):
    d = ImageDraw.Draw(im)
    for t0, t1, y, text, size, col, wt in CAPS:
        if t0 <= t < t1:
            a = min(1, (t - t0) / 0.2, (t1 - t) / 0.3) if t0 > 0 else min(1, (t1 - t) / 0.3)
            rv = len(text) if t0 == 0 else min(len(text), int((t - t0) * 40) + 1)
            f = fnt(wt, size); txt = text[:rv]
            full = d.textlength(text, font=f)
            x = 540 - full / 2
            c = tuple(int(v * a) for v in col)
            d.text((x, y), txt, font=f, fill=c, stroke_width=6, stroke_fill=(0, 0, 0))
    return im

def render(t):
    bob = 3 * math.sin(t * 2)
    if t < 6.5:
        u = t / 6.5
        im = scene_room(t, u, "night", 1, 0, 1, dict(rai=0.5 + 0.3 * abs(math.sin(t * 9)), bob=bob), ui=("MY SIDE BUSINESS", 0.03, "$0"))
    elif t < 13:
        u = (t - 6.5) / 6.5; f = min(1, u * 1.1)
        day = 1 + int(179 * f ** 1.3)
        im = scene_room(t, u, "night", day, int(5 * f), 1 + int(6 * f),
                        dict(rai=0.5 + 0.3 * abs(math.sin(t * 14)), bob=bob), zoom_s=(1.08, 1.0),
                        ui=("MY SIDE BUSINESS", 0.03 + 0.37 * f, f"${int(1240 * f ** 2):,}"))
    elif t < 19:
        u = (t - 13) / 6
        im = scene_room(t, u, "rain", 180, 5, 7, dict(sad=min(1, u * 2.5), bob=bob * 0.5), glow=0.35, zoom_s=(1.0, 1.12),
                        ui=("MY SIDE BUSINESS", 0.4, "$1,240"))
    elif t < 25.5:
        u = (t - 19) / 6.5
        im = scene_room(t, u, "morning", 365, 5 + int(5 * min(1, u * 2)), 7,
                        dict(cheer=max(0, min(1, (u - 0.45) * 3)), look=min(1, u * 3), bob=bob), glow=0.9, zoom_s=(1.12, 1.04),
                        ui=("MY SIDE BUSINESS", 0.4 + 0.6 * min(1, u * 1.6), f"${int(1240 + 8760 * min(1, u * 1.6) ** 1.5):,}"))
    else:
        u = (t - 25.5) / 6.5
        im = zoom(ROOF, lerp(1.0, 1.1, u), 0.55, 0.6).convert("RGBA")
        fg = figure(dict(cheer=min(1, u * 1.6), bob=bob), scale=1.3)
        im.alpha_composite(fg, (300 - fg.width // 2, 1490 - fg.height + 20))
        im = im.convert("RGB")
    im = grade(im, t)
    im = captions(im, t)
    # dip to black between scenes
    for a, b in SCENES[1:]:
        dt = abs(t - a)
        if dt < 0.3:
            im = Image.eval(im, lambda v, k=dt / 0.3: int(v * k))
    fa = min(1, (DUR - t) / 0.8)
    if fa < 1: im = Image.eval(im, lambda v: int(v * fa))
    return im

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((300 * len(ims), 533)).save("chk_story.png")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
