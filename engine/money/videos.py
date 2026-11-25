import sys
from engine import *

R7 = 0.07 / 12

def fv_series(pm_fn, M, r=R7):
    v = [0.0]; x = 0.0
    for m in range(1, M + 1):
        x = (x + pm_fn(m)) * (1 + r); v.append(x)
    return v

def year_counter(m, t, early=15.0, prefix="YEAR", base=1, M=240):
    y = min(M // 12, int(m // 12) + 1)
    s = f"{prefix} {y + base - 1}"
    if t < early and m < 24: s += f"   ·   MONTH {int(m % 12) + 1}"
    return s

def spent_row(name, per, amt, flt, final="sad"):
    return dict(name=name, mode=lambda k: "spend", amt=amt, float=flt, final=final,
                num=lambda m, v, c: ("$0", with_alpha(WHITE, 0.55)),
                sub=lambda m, v: ("SPENT " + money(per * m), RED if m > 0 else GREY))

def val_row(name, values, stack, sub, accent=False, final=None, mode="deposit", numcol=None):
    return dict(name=name, value=values, stack=stack, accent=accent, final=final,
                mode=(lambda k: mode) if isinstance(mode, str) or mode is None else mode,
                num=lambda m, v, c: (money(v), RED if c else (numcol(m, v) if numcol else (GREEN if stack == "green" else WHITE))),
                sub=(lambda m, v: (sub, GREY)) if isinstance(sub, str) else sub)

STD_DISC = ["ILLUSTRATION ONLY. ASSUMES ~7% AVG. ANNUAL RETURN.", "NOT FINANCIAL ADVICE."]
def CAP(t0, t1, y, text, size=42, col=WHITE, wt="s"): return (t0, t1, y, text, size, col, wt)

V = {}

# 2 ---- early vs late starter
M = 480
V["early_vs_late"] = dict(
    M=M, years=40, scale_min=6000,
    counter=lambda m, t: f"AGE {25 + int(m // 12)}" + (f"   ·   MONTH {int(m % 12) + 1}" if t < 15 and m < 24 else ""),
    keys=[(15, 24), (18, 96), (19.5, 120), (22.5, 120), (25.0, 240), (27.8, 240), (33.5, 480)],
    rows=[
        val_row("STARTS AT 25", fv_series(lambda m: 200, M), "green", "$200/MONTH  ·  ~7%", accent=True, final="cheer"),
        val_row("STARTS AT 35", fv_series(lambda m: 200 if m > 120 else 0, M), "white",
                lambda m, v: ("$200/MONTH  ·  ~7%", GREY) if m >= 120 else ("\"I'LL START LATER.\"", DIM), mode=None),
        val_row("STARTS AT 45", fv_series(lambda m: 200 if m > 240 else 0, M), "white",
                lambda m, v: ("$200/MONTH  ·  ~7%", GREY) if m >= 240 else ("\"I'LL START LATER.\"", DIM), mode=None, final="sad"),
    ],
    captions=[CAP(0.3, 19.3, 180, "THREE FRIENDS."), CAP(1.1, 19.3, 238, "SAME $200 A MONTH."),
              CAP(2.4, 19.3, 300, "DIFFERENT START DATES.", 34, GREY),
              CAP(19.6, 24.9, 180, "AGE 35: THE SECOND ONE STARTS.", 38),
              CAP(25.1, 30.2, 180, "AGE 45: THE LAST ONE STARTS.", 38),
              CAP(30.4, 33.8, 180, "THEN COMPOUNDING TAKES OVER.", 42, GREEN),
              CAP(34.2, 99, 160, "HE PUT IN $24,000 MORE."), CAP(36.8, 99, 218, "AND ENDED WITH $282,608 MORE.", 40),
              CAP(39.8, 99, 285, "TIME BEATS AMOUNT.", 64, GREEN, "k")],
    disclaimer=STD_DISC)

# 3 ---- coffee
M = 360
V["coffee"] = dict(
    M=M, years=30, scale_min=6000,
    counter=lambda m, t, M=M: year_counter(m, t, M=M),
    keys=[(15, 24), (19, 60), (22, 60), (33.5, 360)],
    rows=[spent_row("BUYS COFFEE DAILY", 150, "-$150", "-$1,800"),
          val_row("MAKES IT AT HOME", [150.0 * m for m in range(M + 1)], "white", "KEEPS $150 CASH"),
          val_row("INVESTS THE $150", fv_series(lambda m: 150, M), "green", "INDEX FUND  ~7%", accent=True, final="cheer")],
    captions=[CAP(0.3, 19.0, 180, "$5 A DAY ON COFFEE."), CAP(1.1, 19.0, 238, "THAT'S NOTHING... RIGHT?"),
              CAP(19.2, 25.0, 180, "AFTER 5 YEARS: $9,000 IN COFFEE.", 38),
              CAP(25.3, 33.8, 180, "NOW GIVE IT 30 YEARS.", 42),
              CAP(34.2, 99, 160, "$5 A DAY."), CAP(36.8, 99, 218, "OR $184,063."),
              CAP(39.8, 99, 285, "IT WAS NEVER JUST COFFEE.", 46, GREEN, "k")],
    disclaimer=["ILLUSTRATION ONLY. $5/DAY = ~$150/MONTH, ~7% AVG. RETURN.", "NOT FINANCIAL ADVICE."])

# 4 ---- credit card
M = 240
def debt(pay):
    b = 5000.0; out = [b]; paid = None; intr_tot = 0; it = [0.0]
    for m in range(1, M + 1):
        if b > 0.005:
            i = b * 0.22 / 12; intr_tot += i; b += i
            p = min(pay(b, i), b); b -= p
            if b <= 0.005 and paid is None: paid = m; b = 0
        out.append(b); it.append(intr_tot)
    return out, it, paid
def debt_row(name, pay, accent=False):
    vals, it, paid = debt(pay)
    return dict(name=name, value=vals, stack="red", accent=accent, cheer_at=paid,
                mode=lambda k, v=vals: "pay" if v[k - 1] > 0.005 else None,
                num=lambda m, v, c: (money(v), RED) if v > 0.5 else ("$0", GREEN),
                sub=lambda m, v, it=it: ("INTEREST PAID " + money(interp(it, m)), RED if v > 0.5 else GREY))
V["credit_card"] = dict(
    M=M, years=20, scale_min=5000,
    counter=lambda m, t, M=M: year_counter(m, t, M=M),
    keys=[(15, 24), (18, 52), (21.0, 52), (23.5, 120), (26.5, 120), (32.5, 231), (33.5, 240)],
    rows=[debt_row("PAYS THE MINIMUM", lambda b, i: max(25, i + 0.01 * (b - i))),
          debt_row("PAYS $150/MONTH", lambda b, i: 150),
          debt_row("PAYS $500/MONTH", lambda b, i: 500, accent=True)],
    captions=[CAP(0.3, 19.3, 180, "$5,000 CREDIT CARD DEBT."), CAP(1.1, 19.3, 238, "22% INTEREST. THREE WAYS TO PAY.", 38),
              CAP(11.9, 19.3, 300, "YEAR 1: ONE IS DEBT FREE.", 34, GREEN),
              CAP(19.6, 26.3, 180, "YEAR 5: THE SECOND ONE IS FREE.", 38),
              CAP(26.6, 33.8, 180, "THE MINIMUM PAYER? STILL PAYING.", 38, RED),
              CAP(34.2, 99, 160, "SAME $5,000 DEBT."), CAP(36.8, 99, 218, "$574 VS. $8,100 IN INTEREST.", 40),
              CAP(39.8, 99, 285, "PAY MORE THAN THE MINIMUM.", 44, GREEN, "k")],
    disclaimer=["ILLUSTRATION. 22% APR, MINIMUM = INTEREST + 1% OF BALANCE.", "NOT FINANCIAL ADVICE."])

# 5 ---- mattress / inflation
M = 240
def real(rate): return [0.0] + [10000 * ((1 + rate) / 1.025) ** ((m - 1) / 12) for m in range(1, M + 2)]
redbelow = lambda good: (lambda m, v: (GREEN if good else WHITE) if (v >= 10000 - 0.5 or v < 1) else RED)
V["mattress"] = dict(
    M=M, years=20, scale_min=10000,
    counter=lambda m, t: year_counter(max(0, m - 1), t, early=0, M=M) if m > 0 else "YEAR 1",
    events=[(1, 2.6, 0.7)],
    keys=[(3.4, 1), (6.0, 1), (16, 121), (19.5, 121), (33.5, 241)],
    rows=[val_row("UNDER THE MATTRESS", real(0), "white", "0%  ·  TODAY'S DOLLARS", final="sad", numcol=redbelow(False)),
          val_row("SAVINGS ACCOUNT", real(0.02), "white", "2%  ·  TODAY'S DOLLARS", numcol=redbelow(False)),
          val_row("INDEX FUND", real(0.07), "green", "~7%  ·  TODAY'S DOLLARS", accent=True, final="cheer", numcol=redbelow(True))],
    captions=[CAP(0.3, 16.0, 180, "$10,000. THREE PLACES TO KEEP IT.", 38), CAP(3.6, 16.0, 238, "INFLATION: 2.5% A YEAR.", 38, RED),
              CAP(16.2, 22.0, 180, "AFTER 10 YEARS: 22% LESS BUYING POWER.", 34, WHITE),
              CAP(22.3, 33.8, 180, "INFLATION NEVER TAKES A DAY OFF.", 38, RED),
              CAP(34.2, 99, 160, "THE MATTRESS LOST $3,897."), CAP(36.8, 99, 218, "THE SAVINGS ACCOUNT LOST $932.", 40),
              CAP(39.8, 99, 285, "INVESTING BEAT INFLATION.", 46, GREEN, "k")],
    disclaimer=["ILLUSTRATION. TODAY'S DOLLARS, 2.5% INFLATION, ~7% AVG. RETURN.", "NOT FINANCIAL ADVICE."])

# 6 ---- car
M = 360
car_mode = lambda k: "spend" if ((k - 1) // 60) % 2 == 0 else "deposit"
car_vals = fv_series(lambda m: 600 if car_mode(m) == "deposit" else 0, M)
V["car"] = dict(
    M=M, years=30, scale_min=6000, floors=[930, 1430],
    counter=lambda m, t, M=M: year_counter(m, t, M=M),
    keys=[(15, 24), (19, 60), (25.0, 60), (33.5, 360)],
    rows=[spent_row("NEW CAR EVERY 5 YEARS", 600, "-$600", "-$7,200"),
          dict(name="DRIVES IT 10 YEARS", value=car_vals, stack="green", accent=True, final="cheer",
               mode=car_mode, amt="-$600", float="-$7,200",
               num=lambda m, v, c: (money(v), GREEN),
               sub=lambda m, v: ("PAYING OFF THE CAR", RED) if car_mode(int(m) + 1) == "spend" and m < 359 else ("INVESTS $600  ·  ~7%", GREY))],
    captions=[CAP(0.3, 19.0, 180, "TWO PEOPLE. TWO CAR LOANS."), CAP(1.1, 19.0, 238, "$600 A MONTH."),
              CAP(19.2, 24.8, 180, "YEAR 5: BOTH CARS ARE PAID OFF.", 38),
              CAP(20.6, 24.8, 238, "ONE BUYS A NEW ONE. AGAIN.", 38, RED),
              CAP(25.1, 33.8, 180, "THE OTHER INVESTS THE $600.", 42, GREEN),
              CAP(34.2, 99, 160, "SAME $600 A MONTH."), CAP(36.8, 99, 218, "$0 VS. $304,535."),
              CAP(39.8, 99, 285, "DRIVE IT LONGER.", 64, GREEN, "k")],
    disclaimer=["ILLUSTRATION. NEW CAR EVERY 5 VS. 10 YEARS, ~7% AVG. RETURN.", "NOT FINANCIAL ADVICE."])

# 7 ---- raise
M = 240
V["raise"] = dict(
    M=M, years=20, scale_min=6000,
    counter=lambda m, t, M=M: year_counter(m, t, M=M),
    keys=[(15, 24), (19, 60), (22, 60), (33.5, 240)],
    rows=[spent_row("SPENDS THE RAISE", 500, "-$500", "-$6,000"),
          val_row("INVESTS HALF", fv_series(lambda m: 250, M), "white", "$250/MONTH  ·  ~7%"),
          val_row("INVESTS ALL OF IT", fv_series(lambda m: 500, M), "green", "$500/MONTH  ·  ~7%", accent=True, final="cheer")],
    captions=[CAP(0.3, 19.0, 180, "THREE COWORKERS."), CAP(1.1, 19.0, 238, "ALL GET A $500 RAISE."),
              CAP(19.2, 25.0, 180, "5 YEARS: NEW PHONE. NEW CAR. NEW CLOTHES.", 32, GREY),
              CAP(25.3, 33.8, 180, "SAME RAISE. DIFFERENT FUTURES.", 40),
              CAP(34.2, 99, 160, "SAME RAISE. 20 YEARS."), CAP(36.8, 99, 218, "$0 VS. $261,983."),
              CAP(39.8, 99, 285, "INVEST YOUR NEXT RAISE.", 50, GREEN, "k")],
    disclaimer=STD_DISC)

if __name__ == "__main__":
    name, mode = sys.argv[1], sys.argv[2]
    v = Video(V[name])
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
