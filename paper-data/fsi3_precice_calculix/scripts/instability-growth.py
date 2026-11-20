#!/usr/bin/env python3
"""Growth per step of the 2-dt (odd-even) oscillation in the point-A force.

    instability-growth.py WATCHPOINT_LOG [WATCHPOINT_LOG ...]

s_n = |F_x(n+1) - 2 F_x(n) + F_x(n-1)| at the preCICE watch-point A;
growth per step = (s_last / s_last-10)^(1/10), i.e. over the last 10 windows,
and its range over all 10-window spans after the first 10 windows.
"""
import sys
for f in sys.argv[1:]:
    rows = [l.split() for l in open(f) if l.split() and l.split()[0] != "Time"]
    fx = [float(r[3]) for r in rows]
    s = [abs(fx[i + 1] - 2 * fx[i] + fx[i - 1]) for i in range(1, len(fx) - 1)]
    g = (s[-1] / s[-11]) ** 0.1 if len(s) > 11 and s[-11] > 0 else float("nan")
    span = [(s[i] / s[i - 10]) ** 0.1 for i in range(20, len(s)) if s[i - 10] > 0]
    rng = f"{min(span):.3f}-{max(span):.3f}" if span else "n/a"
    print(f"{f}: windows {len(rows)}, |d2 Fx| last {s[-1]:.3g}, growth/step last 10 {g:.3f}, range {rng}")
