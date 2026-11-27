import sys, wave, numpy as np
dur = float(sys.argv[1]); bpm = float(sys.argv[2]); cuts = [float(x) for x in sys.argv[3].split()]; out = sys.argv[4]
SR = 44100; n = int(SR * dur); o = np.zeros(n); rng = np.random.default_rng(1); beat = 60 / bpm
def add(t0, s, g=1.0):
    i = int(t0 * SR); j = min(n, i + len(s))
    if i < n: o[i:j] += g * s[:j - i]
x = np.arange(int(SR * .45)) / SR
kick = np.sin(2 * np.pi * (48 + 110 * np.exp(-x * 32)) * x) * np.exp(-x * 8)
xs = np.arange(int(SR * .2)) / SR
snare = rng.normal(0, 1, len(xs)) * np.exp(-xs * 20) * .35 + np.sin(2 * np.pi * 200 * xs) * np.exp(-xs * 24) * .25
xh = np.arange(int(SR * .04)) / SR
hat = np.diff(np.concatenate([[0], rng.normal(0, 1, len(xh)) * np.exp(-xh * 140)])) * 2.2
xw = np.arange(int(SR * .35)) / SR
noise = rng.normal(0, 1, len(xw))
whoosh = np.convolve(noise, np.ones(30) / 30, 'same') * np.sin(np.pi * xw / xw[-1]) ** 2 * .9
# chords (A minor: Am F C G), plucked
def pluck(f, d=1.2, a=.12):
    t = np.arange(int(SR * d)) / SR
    return a * (np.sin(2 * np.pi * f * t) + .4 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 3.5)
prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
nb = int(dur / beat)
for b in range(nb):
    t0 = b * beat
    add(t0, kick, .9)
    if b % 2 == 1: add(t0, snare)
    add(t0 + beat / 2, hat, .5); add(t0, hat, .3)
    ch = prog[(b // 4) % 4]
    f = 440 * 2 ** ((ch[b % 3] + 12 - 69) / 12)
    add(t0, pluck(f)); add(t0 + beat / 2, pluck(f * 1.5, a=.06))
    if b % 4 == 0:
        fb = 440 * 2 ** ((ch[0] - 12 - 69) / 12); tb = np.arange(int(SR * beat * 4)) / SR
        add(t0, .25 * np.sin(2 * np.pi * fb * tb) * np.exp(-tb * .8))
for c in cuts: add(c - .17, whoosh, .5)
o *= np.minimum(1, (dur - np.arange(n) / SR) / 1.0)
o = np.tanh(o * 1.3); o = o / np.max(np.abs(o)) * .9
w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.stack([o, o], 1) * 32767).astype(np.int16).tobytes()); w.close()
