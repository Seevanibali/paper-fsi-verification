#!/usr/bin/env python3
"""Figure for the FSI3 level-1 run and the instability tests (run from this folder).

    python3 scripts/plot-fsi3.py   ->  fsi3_precice_level1.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6})

h = np.genfromtxt("histories/level1-dt1e-3.csv", delimiter=",", names=True)
res = {r[0]: r for r in np.genfromtxt("fsi3_precice_level1_results.csv", delimiter=",", dtype=None,
                                     encoding=None, skip_header=1)}
t0, t1 = float(res["window_start"][2]), float(res["window_end"][2])
c = h["time_s"] >= 2.0

fig, ax = plt.subplots(2, 2, figsize=(12, 7.5), layout="constrained")
fig.suptitle("Hron–Turek FSI3, OpenFOAM + CalculiX (preCICE): level 1′, Δt = 1e-3 s, HHT α = −1/3",
             color=INK, fontsize=11)
panels = [(ax[0, 0], 1e3 * h["uy_m"], "u_y(A) (mm)", 1.47, 34.99),
          (ax[0, 1], h["lift_N_per_m"], "lift (N/m)", 2.50, 153.91),
          (ax[1, 0], h["drag_N_per_m"], "drag (N/m)", 460.5, 27.74)]
for a, y, lab, m, amp in panels:
    a.axvspan(t0, t1, color=GRID, alpha=0.6, lw=0)
    a.plot(h["time_s"][c], y[c], color=C[0], lw=1.2)
    for v in (m - amp, m + amp):
        a.axhline(v, color=INK, lw=1, ls="--")
    a.set_xlim(2, 6); a.set_xlabel("t (s)"); a.set_ylabel(lab)
ax[0, 0].text(t0 + 0.02, ax[0, 0].get_ylim()[1] * 0.97, "evaluation window\n(5 periods)",
              va="top", color=MUTED, fontsize=9)
ax[0, 0].text(2.05, 1.47 + 34.99 + 2, "Featflow mean ± amplitude", color=INK, fontsize=9)

# instability tests: |second difference of F_x(A)| per coupling window
a = ax[1, 1]
cases = [("base-PointA.log", "Δt 5e-4, α −0.05 (set-up as specified)"),
         ("alpha0333-PointA.log", "Δt 5e-4, α −1/3"),
         ("dt1e-3-PointA.log", "Δt 1e-3, α −0.05"),
         ("dt1e-3-alpha0333-PointA.log", "Δt 1e-3, α −1/3 (used)")]
for (f, lab), col in zip(cases, C):
    rows = [l.split() for l in open("instability/" + f) if l.split() and l.split()[0] != "Time"]
    fx = np.array([float(r[3]) for r in rows])
    s = np.abs(fx[2:] - 2 * fx[1:-1] + fx[:-2])
    a.semilogy(np.arange(1, len(s) + 1), s, color=col, lw=1.6, label=lab)
a.set_xlabel("coupling window after t = 2 s"); a.set_ylabel("|F_x(n+1) − 2F_x(n) + F_x(n−1)| at A (N)")
a.set_title("2Δt oscillation in the interface force (restarts from t = 2 s)", fontsize=10, color=INK)
a.legend(frameon=False, fontsize=9, loc="upper right")
fig.savefig("fsi3_precice_level1.png", dpi=130)
