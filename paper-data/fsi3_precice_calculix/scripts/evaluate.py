#!/usr/bin/env python3
"""Periodic FSI3 values of one case against the Featflow FSI3 table (level 4).

    evaluate.py CASEDIR [T_END_WINDOW] [OUT_PREFIX]

With OUT_PREFIX, also writes OUT_PREFIX-results.csv (one row per quantity) and
OUT_PREFIX-history.csv (converged value per time step: u_x, u_y in m, drag, lift in N/m).

Histories:
  forces  last (converged) line per time of postProcessing/forces/*/force.dat
          (plate + cylinder), divided by the 0.015 m depth;
  point A preCICE watch-point (0.6, 0.2) on the solid mesh (time relative to the
          coupling start at t = 2 s).
Window: the five full u_y periods (maximum to maximum) that end before
T_END_WINDOW (default 6.0 s), as in the solids4foam corrected FSI3 sequence.
Per period: mean = (max + min)/2, amplitude = (max - min)/2 (benchmark definitions);
the table gives the average over the five periods and the last period alone.
Frequency: 1 / mean u_y period over the window. Extrema refined by a parabola.
"""
import glob, sys
from pathlib import Path

case = Path(sys.argv[1]); tw = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
out = sys.argv[3] if len(sys.argv) > 3 else None
depth, t0, nper = 0.015, 2.0, 5
# Featflow FSI3 table, level 4 (mm, N/m, Hz): mean, amplitude
ref = {"ux": (-2.88, 2.72), "uy": (1.47, 34.99), "drag": (460.5, 27.74), "lift": (2.50, 153.91)}
fref = 5.46

forces = {}
for f in sorted(glob.glob(str(case / "fluid-openfoam/postProcessing/forces/*/force.dat"))):
    for line in open(f):
        if line.startswith("#") or not line.strip():
            continue
        c = line.replace("(", " ").replace(")", " ").split()
        forces[round(float(c[0]), 8)] = (float(c[1]) / depth, float(c[2]) / depth)
disp = {}
for line in open(case / "solid-calculix/precice-Solid-watchpoint-PointA.log"):
    c = line.split()
    if not c or c[0] == "Time":
        continue
    disp[round(float(c[0]) + t0, 8)] = (1e3 * float(c[5]), 1e3 * float(c[6]))   # mm

hist = {"ux": sorted((t, v[0]) for t, v in disp.items()), "uy": sorted((t, v[1]) for t, v in disp.items()),
        "drag": sorted((t, v[0]) for t, v in forces.items()), "lift": sorted((t, v[1]) for t, v in forces.items())}


def extremum(h, i):
    """Parabola through h[i-1], h[i], h[i+1]: (time, value) of the vertex."""
    (ta, a), (tb, b), (tc, c) = h[i - 1], h[i], h[i + 1]
    d = a - 2 * b + c
    if d == 0:
        return tb, b
    s = 0.5 * (a - c) / d                      # offset in steps from tb
    return tb + s * (tc - tb), b - 0.25 * (a - c) * s


def in_range(h, ta, tb):
    """Max and min of h on [ta, tb], parabola-refined."""
    idx = [i for i in range(1, len(h) - 1) if ta <= h[i][0] <= tb]
    imax = max(idx, key=lambda i: h[i][1]); imin = min(idx, key=lambda i: h[i][1])
    return extremum(h, imax)[1], extremum(h, imin)[1]


uy = hist["uy"]
maxima = [extremum(uy, i)[0] for i in range(1, len(uy) - 1)
          if uy[i][1] > uy[i - 1][1] and uy[i][1] >= uy[i + 1][1] and uy[i][1] > 0]
maxima = [t for t in maxima if t <= tw]
if len(maxima) < nper + 1:
    sys.exit(f"only {len(maxima)} u_y maxima before t = {tw}")
edges = maxima[-(nper + 1):]
periods = [(edges[k], edges[k + 1]) for k in range(nper)]
freq = nper / (edges[-1] - edges[0])

print(f"case {case}, last time: fluid {max(forces)}, solid {max(disp)}")
print(f"window: {nper} u_y periods, t = {edges[0]:.4f}-{edges[-1]:.4f} s")
print(f"{'qty':5} {'mean':>9} {'amp':>9} {'Featflow':>16} {'err mean':>9} {'err amp':>8}"
      f" {'last-period mean':>16} {'amp':>9} {'period-to-period amp range':>27}")
res = []
for q, h in hist.items():
    per = []
    for ta, tb in periods:
        mx, mn = in_range(h, ta, tb)
        per.append(((mx + mn) / 2, (mx - mn) / 2))
    m = sum(p[0] for p in per) / nper; a = sum(p[1] for p in per) / nper
    rm, ra = ref[q]
    res.append((q, m, a, per[-1][0], per[-1][1], max(p[1] for p in per) - min(p[1] for p in per), rm, ra))
    em = f"{100 * (m - rm) / abs(rm):8.2f}%"
    print(f"{q:5} {m:9.5g} {a:9.5g} {rm:7.4g} ± {ra:6.4g} {em:>9} {100 * (a - ra) / ra:7.2f}%"
          f" {per[-1][0]:16.5g} {per[-1][1]:9.5g} {max(p[1] for p in per) - min(p[1] for p in per):27.3g}")
print(f"u_y frequency {freq:.4f} Hz (Featflow {fref}, {100 * (freq - fref) / fref:+.2f}%)")

rows = [l.split() for l in open(case / "solid-calculix/precice-Solid-iterations.log")]
its = [int(r[2]) for r in rows if r and r[0].isdigit()]
conv = [int(r[3]) for r in rows if r and r[0].isdigit() and len(r) > 3]
print(f"coupled windows {len(its)}, coupling iterations mean {sum(its) / len(its):.2f}, max {max(its)}, "
      f"unconverged windows {conv.count(0) if conv else 'n/a'}")

if out:
    with open(f"{out}-results.csv", "w") as fh:
        fh.write("quantity,unit,mean_maxmin,amplitude,last_period_mean,last_period_amplitude,"
                 "amplitude_range_over_periods,featflow_mean,featflow_amplitude\n")
        for q, m, a, lm, la, rg, rm, ra in res:
            u = "mm" if q in ("ux", "uy") else "N/m"
            fh.write(f"{q},{u},{m:.6g},{a:.6g},{lm:.6g},{la:.6g},{rg:.3g},{rm},{ra}\n")
        fh.write(f"frequency,Hz,{freq:.6g},,,,,{fref},\n")
        fh.write(f"window_start,s,{edges[0]:.6g},,,,,,\nwindow_end,s,{edges[-1]:.6g},,,,,,\n")
    with open(f"{out}-history.csv", "w") as fh:
        fh.write("time_s,ux_m,uy_m,drag_N_per_m,lift_N_per_m\n")
        for t in sorted(forces):
            ux, uy = disp.get(t, (0.0, 0.0))
            fh.write(f"{t:.4f},{ux * 1e-3:.9e},{uy * 1e-3:.9e},{forces[t][0]:.9e},{forces[t][1]:.9e}\n")
