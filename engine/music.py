"""Royalty-free generated background music (ambient piano) for Stick Lessons.
usage: python3 music.py <duration_s> <out.wav> [seed]"""
import sys, wave
import numpy as np

SR = 44100

def piano(f, dur, vel=1.0):
    t = np.arange(int(SR * dur)) / SR
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 200))
    s = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)):
        s += a * np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k)) * np.exp(-t * (0.8 * k))
    return vel * s * env

def pad(freqs, dur):
    t = np.arange(int(SR * dur)) / SR
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2)
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    return 0.05 * s * env

def nf(n): return 440 * 2 ** ((n - 69) / 12)

def make(dur, seed=1):
    rng = np.random.default_rng(seed)
    n = int(SR * dur); out = np.zeros(n + SR * 4)
    bpm = 72; beat = 60 / bpm; bar = beat * 4
    # Am - F - C - G (midi roots)
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
    scale = [69, 71, 72, 74, 76, 79, 81]
    t = 0.0; i = 0
    while t < dur:
        root, chord = prog[i % 4]
        def add(t0, sig):
            a = int(t0 * SR); b = min(len(out), a + len(sig)); out[a:b] += sig[:b - a]
        add(t, pad([nf(m) for m in chord], bar + 0.5))
        add(t, piano(nf(root - 12), 3.5, 0.55))
        # arpeggio
        for k in range(8):
            m = chord[k % 3] + (12 if k >= 4 else 0)
            add(t + k * beat / 2, piano(nf(m), 1.6, 0.22 + 0.05 * rng.random()))
        # sparse melody
        for k in range(4):
            if rng.random() < 0.55:
                add(t + k * beat + (beat / 2 if rng.random() < 0.3 else 0), piano(nf(int(rng.choice(scale))), 2.0, 0.32))
        t += bar; i += 1
    out = out[:n]
    tt = np.arange(n) / SR
    out *= np.minimum(1, np.minimum(tt / 1.5, (dur - tt) / 2.0))
    # simple reverb
    rev = np.zeros_like(out)
    for d, g in ((0.031, 0.35), (0.047, 0.3), (0.071, 0.25), (0.113, 0.2), (0.167, 0.15)):
        k = int(d * SR); rev[k:] += g * out[:-k]
    out = out + 0.6 * rev
    return out / np.max(np.abs(out)) * 0.9

if __name__ == "__main__":
    dur, path = float(sys.argv[1]), sys.argv[2]
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    x = make(dur, seed)
    st = (np.stack([x, x], 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
