import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(F + n, s)
LIGHT = lambda s: font("Inter-Light.otf", s); MED = lambda s: font("Inter-Medium.otf", s); SEMI = lambda s: font("Inter-SemiBold.otf", s)
GREEN = (57, 229, 140); RED = (230, 70, 70)

def ease(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.5, fo=0.5):
    if t < a or t > b: return 0.0
    return float(min(1, (t - a) / fi, (b - t) / fo))
def sc(c, a): return tuple(int(v * a) for v in c)
def tc(d, y, s, f, fill):
    w = d.textlength(s, font=f); d.text((540 - w / 2, y), s, font=f, fill=fill)

def pill(d, y, s, a, strike=0.0, filled=False, size=36):
    f = MED(size); w = d.textlength(s, font=f); c = int(235 * a)
    box = [540 - w / 2 - 34, y - 8, 540 + w / 2 + 34, y + size + 16]
    if filled:
        d.rounded_rectangle(box, 30, fill=(c, c, c)); d.text((540 - w / 2, y), s, font=f, fill=(0, 0, 0))
    else:
        d.rounded_rectangle(box, 30, outline=(c, c, c), width=3); d.text((540 - w / 2, y), s, font=f, fill=(c, c, c))
    if strike > 0:
        d.line([box[0] + 10, (box[1] + box[3]) / 2, box[0] + 10 + (box[2] - box[0] - 20) * strike, (box[1] + box[3]) / 2], fill=(c, c, c), width=4)

# ---- numbers (30 years, 7%) ----
r = 0.07 / 12; PM = 1e6 * r / ((1 + r) ** 360 - 1)
VAL = [0.0]; PAID = [0.0]; v = 0
for m in range(1, 361):
    v = (v + PM) * (1 + r); VAL.append(v); PAID.append(PM * m)

SUBS = [
    (0.3, 4.5, "Your first million only looks impossible from the wrong angle."),
    (4.7, 9.0, "Looked at as one giant number, it is impossible."),
    (9.2, 14.0, "Spread over 30 years, it's $33,333 a year."),
    (14.2, 18.0, "That's $2,778 a month."),
    (18.2, 22.0, "Or $91 a day. Still a lot? Change the angle again."),
    (22.2, 27.0, "Invest it and let it grow at around 7% a year."),
    (27.2, 32.0, "Now you only need $820 a month."),
    (32.2, 36.0, "That's $27 a day."),
    (36.2, 41.0, "And you only pay in $295,000. The rest is growth."),
    (41.2, 46.0, "Slow at first. Then fast."),
    (46.2, 50.0, "Start 10 years earlier? Just $12.50 a day."),
    (50.2, 56.0, "So don't ask how to make a million. Ask how to take today's step."),
    (56.2, 61.5, "Change the angle. Then go step by step."),
]
DUR = 62.0

def subtitle(d, t):
    f = MED(40)
    for a, b, s in SUBS:
        al = win(t, a, b, 0.35, 0.35)
        if al <= 0: continue
        lines = [""]
        for wd in s.split():
            if d.textlength(lines[-1] + " " + wd, font=f) > 900: lines.append(wd)
            else: lines[-1] = (lines[-1] + " " + wd).strip()
        for k, ln in enumerate(lines): tc(d, 1690 + k * 54, ln, f, sc((225, 225, 225), al))

def big(d, t, a, b, num, unit, col=(245, 245, 245), y=760, size=170, slide=True, fi=0.45):
    al = win(t, a, b, fi, 0.4)
    if al <= 0: return
    dy = 0 if not slide else int(40 * (1 - ease((t - a) / 0.45)))
    tc(d, y + dy, num, LIGHT(size), sc(col, al))
    if unit: tc(d, y + size + 30 + dy, unit, SEMI(38), sc((160, 160, 165), al))

DOTS = 1000
GX0, GY0, STEP = 252, 560, 24   # 25 x 40 grid
def grid(d, t, a):
    yr = 30 * float(ease((t - 36.6) / 8.6))
    m = int(yr * 12)
    val = VAL[m]; paid = PAID[m]
    nfill = int(DOTS * val / 1e6); npaid = int(DOTS * paid / 1e6)
    for i in range(DOTS):
        x = GX0 + (i % 25) * STEP; y = GY0 + (i // 25) * STEP
        y = GY0 + (39 - i // 25) * STEP          # fill from bottom
        if i < npaid: c = (235, 235, 235)
        elif i < nfill: c = GREEN
        else: c = (40, 40, 44)
        rr = 7
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=sc(c, a))
    tc(d, 330, f"YEAR {int(yr)}", SEMI(40), sc((170, 170, 175), a))
    tc(d, 400, f"${val:,.0f}", LIGHT(90), sc((245, 245, 245), a))
    # legend
    f = MED(30)
    d.ellipse([200, 1745 - 120, 222, 1767 - 120], fill=sc((235, 235, 235), a)); d.text((236, 1740 - 120), "PAID IN", font=f, fill=sc((200, 200, 200), a))
    d.ellipse([560, 1745 - 120, 582, 1767 - 120], fill=sc(GREEN, a)); d.text((596, 1740 - 120), "GROWTH", font=f, fill=sc(GREEN, a))

def stairs(d, t, a):
    n = 12; sw, sh = 62, 62; x0, y0 = 170, 1450
    for k in range(n):
        x = x0 + k * sw; y = y0 - k * sh
        d.line([x, y, x + sw, y], fill=sc((200, 200, 200), a), width=4)
        d.line([x + sw, y, x + sw, y - sh], fill=sc((200, 200, 200), a), width=4)
    p = float(ease((t - 56.6) / 3.8)) * (n - 1)
    k = int(p); f = p - k
    x = x0 + (k + 0.5 + f) * sw; y = y0 - k * sh - 18 - 30 * math.sin(math.pi * f)
    d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=sc(GREEN, a))
    tc(d, 330, "ONE STEP. TODAY.", SEMI(70), sc((245, 245, 245), win(t, 57.4, 62, 0.6, 0.6)))

def render(t):
    img = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    # hook
    big(d, t, 0.0, 4.6, "$1,000,000", None, size=150, slide=False, fi=0.01)
    ah = win(t, 0.0, 4.6, 0.01, 0.4)
    if ah > 0:
        tc(d, 330, "ONLY HARD IF YOU", SEMI(56), sc((245, 245, 245), ah))
        tc(d, 405, "LOOK AT IT WRONG.", SEMI(56), sc(GREEN, ah))
    # one giant number
    a = win(t, 4.7, 9.0)
    if a > 0:
        pill(d, 330, "1 × $1,000,000", a)
        cx, cy, R = 540, 960, 230
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=sc((220, 220, 220), a), width=4)
        tc(d, cy - 40, "$1M", LIGHT(90), sc((235, 235, 235), a))
        s = float(ease((t - 6.2) / 0.6))
        if s > 0:
            d.line([cx - 280, cy - 280, cx - 280 + 560 * s, cy - 280 + 560 * s], fill=sc(RED, a), width=8)
            d.line([cx + 280, cy - 280, cx + 280 - 560 * s, cy - 280 + 560 * s], fill=sc(RED, a), width=8)
    # breakdown
    for a_, b_, txt in ((9.2, 14.0, "30 YEARS"), (14.2, 18.0, "30 YEARS"), (18.2, 22.0, "30 YEARS")):
        al = win(t, a_, b_, 0.4, 0.3)
        if al > 0: pill(d, 330, txt, al)
    big(d, t, 9.4, 14.0, "$33,333", "PER YEAR")
    big(d, t, 14.2, 18.0, "$2,778", "PER MONTH")
    big(d, t, 18.2, 22.0, "$91", "PER DAY")
    # invest
    a = win(t, 22.2, 36.0)
    if a > 0: pill(d, 330, "30 YEARS  ·  INVESTED AT ~7%", a)
    a2 = win(t, 22.4, 27.0)
    if a2 > 0:  # small growth curve
        pts = [(220 + 640 * k / 60, 1180 - 420 * (VAL[k * 6] / 1e6)) for k in range(int(61 * min(1, (t - 22.4) / 3.5)))]
        if len(pts) > 1: d.line(pts, fill=sc(GREEN, a2), width=6)
        d.line([220, 1180, 860, 1180], fill=sc((90, 90, 95), a2), width=3)
    big(d, t, 27.2, 32.0, "$820", "PER MONTH", col=GREEN)
    big(d, t, 32.2, 36.0, "$27", "PER DAY", col=GREEN)
    # dots
    a = win(t, 36.2, 46.0, 0.6, 0.5)
    if a > 0: grid(d, t, a)
    # earlier start
    a = win(t, 46.2, 50.0)
    if a > 0: pill(d, 330, "START 10 YEARS EARLIER  ·  40 YEARS", a)
    big(d, t, 46.6, 50.0, "$12.50", "PER DAY", col=GREEN)
    # change the question
    if 50.2 < t < 56.1:
        a1 = win(t, 50.2, 56.0, 0.4, 0.4)
        pill(d, 820, "HOW DO I MAKE A MILLION?", a1 * (0.45 if t > 53.0 else 1), strike=float(ease((t - 52.3) / 0.6)), size=38)
        a2 = win(t, 53.2, 56.0, 0.4, 0.4)
        if a2 > 0: pill(d, 950, "HOW DO I SAVE $27 TODAY?", a2, filled=True, size=40)
    a = win(t, 56.2, 62.0, 0.5, 0.8)
    if a > 0: stairs(d, t, a)
    subtitle(d, t)
    return img

if __name__ == "__main__":
    if sys.argv[1] == "still":
        ims = [render(float(x)) for x in sys.argv[2:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((220 * len(ims), 391)).save("chk_million.png")
    else:
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(round(t0 * FPS), round(t1 * FPS)): p.stdin.write(render(n / FPS).tobytes())
        p.stdin.close(); sys.exit(p.wait())
