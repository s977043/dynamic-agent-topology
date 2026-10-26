"""Reproduce the power table and false-reject rate in HARD_TASK_T0_FAIL_T1_PREREGISTRATION.md section 2.3.

No model is launched. Usage: python scripts/hard_task_power_sim.py [table|false-reject|all]
"""

import random
import sys
from collections import defaultdict

N = 12
REPS = 3
THRESHOLD = 0.30
ALPHA = 0.05


def flip_table(a):
    # a: d_i * 3 as integers. Returns {(sum of s_i * a_i, number of +1 signs): count} over all 2^N sign vectors.
    t = {(0, 0): 1}
    for x in a:
        nt = defaultdict(int)
        for (s, p), c in t.items():
            nt[(s + x, p + 1)] += c
            nt[(s - x, p)] += c
        t = nt
    return t


def pval(t, total):
    return sum(c for (s, _), c in t.items() if s >= total) / 2**N


def upper(t, total):
    # For e_i = a_i - c (c = 3 * delta), sum of s_i * e_i = s - c * (2p - N); the observed value is total - c * N.
    d = total / (REPS * N)
    k = 0
    while True:
        delta = round(d + 0.001 * k, 3)
        if delta >= 1:
            return 1.0
        c = REPS * delta
        obs = total - c * N + 1e-9
        p_low = sum(cnt for (s, p), cnt in t.items() if s - c * (2 * p - N) <= obs) / 2**N
        if p_low < ALPHA:
            return delta
        k += 1


def draw(rng, pi, p1_hi, p1_lo, p0):
    a = []
    for _ in range(N):
        p1 = p1_hi if rng.random() < pi else p1_lo
        t1 = sum(rng.random() < p1 for _ in range(REPS))
        t0 = sum(rng.random() < p0 for _ in range(REPS))
        a.append(t1 - t0)
    return a


def power_table():
    r, seed = 4000, 20261026
    rng = random.Random(seed)
    print(f"power table: R={r} seed={seed}")
    for pi in (0.0, 3 / 14, 3 / 7, 4 / 7, 9 / 14, 5 / 7):
        sup = rej = cov = 0
        for _ in range(r):
            a = draw(rng, pi, 0.8, 0.1, 0.1)
            total = sum(a)
            t = flip_table(a)
            if total / (REPS * N) >= THRESHOLD and pval(t, total) < ALPHA:
                sup += 1
            u = upper(t, total)
            if u < THRESHOLD:
                rej += 1
            if u >= 0.7 * pi - 1e-9:
                cov += 1
        print(f"Dtrue={0.7 * pi:.2f} pi={pi:.3f} support={sup / r:.3f} reject={rej / r:.3f} coverage={cov / r:.3f}")
    for name, a in (("4x(+1),8x0", [3] * 4 + [0] * 8), ("6x(+2/3),6x0", [2] * 6 + [0] * 6)):
        print(f"{name} D={sum(a) / 36:.3f} p={pval(flip_table(a), sum(a)):.4f}")


def false_reject():
    # The three distributions share one random stream in this order; the 1.0/0/0 row is the value cited in section 2.3.
    r, seed = 2000, 1
    rng = random.Random(seed)
    print(f"false reject: R={r} seed={seed}")
    for name, hi, lo, p0 in (("0.8/0.1/0.1", 0.8, 0.1, 0.1), ("1.0/0/0", 1.0, 0.0, 0.0), ("0.5/0.1/0.1", 0.5, 0.1, 0.1)):
        for dt in (0.30, 0.33):
            pi = dt / (hi - lo)
            if pi > 1:
                continue
            rej = sum(upper(flip_table(a), sum(a)) < THRESHOLD for a in (draw(rng, pi, hi, lo, p0) for _ in range(r)))
            print(f"{name} Dtrue={dt:.2f} pi={pi:.3f} false_reject={rej / r:.3f}")


def main(argv):
    mode = argv[1] if len(argv) > 1 else "all"
    if mode not in ("table", "false-reject", "all"):
        print(__doc__)
        return 2
    if mode in ("table", "all"):
        power_table()
    if mode in ("false-reject", "all"):
        false_reject()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
