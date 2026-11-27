import sys
from engine import *
from videos import CAP, fv_series, spent_row, val_row, year_counter, STD_DISC

def make(M, years, rows, h1, h2, mid, fin1, fin2, disc=STD_DISC, counter=None, floors=None,
         h_size=62, fin_size=58, scale_min=6000):
    c = dict(
        M=M, years=years, rows=rows, scale_min=scale_min, dur=28.0, final_t=19.3, fade_in=False,
        counter=counter or (lambda m, t, M=M: year_counter(m, t, M=M)),
        events=[(k, 1.0 + (k - 1) * 0.42, 0.35) for k in range(1, 7)],
        keys=[(3.6, 6), (7.5, 60), (9.6, 60), (19.0, M)],
        captions=[
            CAP(0.0, 19.2, 165, h1, h_size, WHITE, "k"),
            CAP(0.0, 19.2, 245, h2, h_size, GREEN, "k"),
            CAP(7.6, 9.9, 325, mid, 40, RED, "s"),
            CAP(10.1, 19.2, 325, f"NOW WATCH {M // 12} YEARS...", 40, GREY, "s"),
            CAP(19.3, 99, 165, fin1, fin_size, GREEN, "k"),
            CAP(21.0, 99, 250, fin2, 44, WHITE, "s"),
        ],
        disclaimer=disc,
    )
    if floors: c["floors"] = floors
    return c

V2 = {}
M = 240
V2["eating_out"] = make(M, 20, [
    spent_row("EATS OUT A LOT", 400, "-$400", "-$4,800"),
    val_row("COOKS, KEEPS CASH", [400.0 * m for m in range(M + 1)], "white", "KEEPS $400/MONTH"),
    val_row("COOKS, INVESTS IT", fv_series(lambda m: 400, M), "green", "INDEX FUND  ~7%", accent=True, final="cheer")],
    "$400 TAKEOUT A MONTH", "VS. COOKING AT HOME", "5 YEARS: $24,000 EATEN.", "$400 = $209,586", "SAME FOOD. DIFFERENT FUTURE.",
    h_size=56)

V2["subscriptions"] = make(M, 20, [
    spent_row("FORGOTTEN SUBSCRIPTIONS", 60, "-$60", "-$720"),
    val_row("CANCELS & INVESTS", fv_series(lambda m: 60, M), "green", "$60/MONTH  ·  ~7%", accent=True, final="cheer")],
    "$60 IN SUBSCRIPTIONS", "YOU NEVER USE", "5 YEARS: $3,600 GONE.", "$60 = $31,438", "CHECK YOUR SUBSCRIPTIONS.",
    floors=[930, 1430], h_size=58)

V2["phone"] = make(M, 20, [
    spent_row("NEW PHONE EVERY YEAR", 100, "-$100", "-$1,200"),
    val_row("NEW PHONE EVERY 3 YEARS", fv_series(lambda m: 66.67, M), "green", "INVESTS THE $67 SAVED", accent=True, final="cheer")],
    "NEW PHONE EVERY YEAR", "VS. EVERY 3 YEARS", "5 YEARS: $6,000 ON PHONES.", "THE DIFFERENCE: $34,933", "YOUR OLD PHONE STILL WORKS.",
    floors=[930, 1430], h_size=56, fin_size=52)

M = 360
V2["lottery"] = make(M, 30, [
    spent_row("$20 LOTTERY EVERY WEEK", 87, "-$87", "-$1,044"),
    val_row("INVESTS THE $20 INSTEAD", fv_series(lambda m: 87, M), "green", "INDEX FUND  ~7%", accent=True, final="cheer")],
    "$20 LOTTERY EVERY WEEK", "VS. INVESTING IT", "5 YEARS: $5,220 SPENT. NO WIN.", "GUARANTEED: $106,757", "THE REAL JACKPOT WAS PATIENCE.",
    floors=[930, 1430], h_size=54, fin_size=54)

M = 240
V2["smoking"] = make(M, 20, [
    spent_row("SMOKES A PACK A DAY", 300, "-$300", "-$3,600"),
    val_row("QUITS & INVESTS IT", fv_series(lambda m: 300, M), "green", "$300/MONTH  ·  ~7%", accent=True, final="cheer")],
    "A PACK A DAY", "VS. QUITTING", "5 YEARS: $18,000 BURNED.", "QUITTING = $157,190", "PLUS YOUR HEALTH.",
    floors=[930, 1430])

M = 780
kid_vals = fv_series(lambda m: 50 if m <= 216 else 0, M)
V2["kid"] = make(M, 65, [
    dict(name="NO SAVINGS FOR THE KID", final="sad",
         num=lambda m, v, c: ("$0", with_alpha(WHITE, 0.55)), sub=lambda m, v: ("STARTS FROM ZERO", GREY)),
    val_row("$50/MONTH FROM BIRTH", kid_vals, "green",
            lambda m, v: ("PARENTS PAY $50/MONTH", GREY) if m <= 216 else ("STOPPED AT AGE 18", GREY),
            accent=True, final="cheer", mode=lambda k: "deposit")],
    "$50 A MONTH", "FROM THE DAY YOU'RE BORN", "AGE 5: JUST $3,000 PAID IN.", "AT 65: $575,930", "FROM $10,800 PAID IN.",
    counter=lambda m, t: f"AGE {int(m // 12)}", floors=[930, 1430], h_size=50, fin_size=56)
V2["kid"]["captions"][3] = CAP(10.1, 19.2, 325, "PAYMENTS STOP AT 18. THEN WAIT...", 38, GREY, "s")

if __name__ == "__main__":
    name, mode = sys.argv[1], sys.argv[2]
    v = Video(V2[name])
    if mode == "still":
        from PIL import Image
        ims = [v.render(float(t)) for t in sys.argv[3:]]
        s = Image.new("RGB", (1080 * len(ims), 1920))
        for i, im in enumerate(ims): s.paste(im, (i * 1080, 0))
        s.resize((300 * len(ims), 533)).save(f"chk_{name}.png")
    elif mode == "audio":
        v.audio(f"{name}.wav")
    else:
        sys.exit(v.encode(float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]))
