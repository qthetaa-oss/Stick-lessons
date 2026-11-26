import sys
from engine import *
from videos import V, CAP, fv_series, spent_row, val_row, year_counter

M = 360
coffee = dict(V["coffee"])
coffee.update(
    dur=28.0, final_t=19.3, fade_in=False,
    events=[(k, 1.0 + (k - 1) * 0.42, 0.35) for k in range(1, 7)],
    keys=[(3.6, 6), (7.5, 60), (9.6, 60), (19.0, 360)],
    captions=[
        CAP(0.0, 19.2, 165, "$5 COFFEE EVERY DAY", 62, WHITE, "k"),
        CAP(0.0, 19.2, 245, "VS. INVESTING IT", 62, GREEN, "k"),
        CAP(7.6, 9.9, 325, "5 YEARS: $9,000 GONE.", 40, RED, "s"),
        CAP(10.1, 19.2, 325, "NOW WATCH 30 YEARS...", 40, GREY, "s"),
        CAP(19.3, 99, 165, "$5 A DAY = $184,063", 58, GREEN, "k"),
        CAP(21.0, 99, 250, "IT WAS NEVER JUST COFFEE.", 44, WHITE, "s"),
    ],
)
VIDS = {"coffee_tt": coffee}

if __name__ == "__main__":
    name, mode = sys.argv[1], sys.argv[2]
    v = Video(VIDS[name])
    if mode == "still":
        from PIL import Image
        ims = [v.render(float(t)) for t in sys.argv[3:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((360 * len(ims), 640)).save(f"chk_{name}.png")
    elif mode == "audio":
        v.audio(f"{name}.wav")
    else:
        sys.exit(v.encode(float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]))
