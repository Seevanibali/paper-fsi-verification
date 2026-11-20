#!/usr/bin/env python3
"""Numerical damping of the HHT-alpha scheme (CalculiX *DYNAMIC) for one undamped mode.

    hht-damping.py [FREQ_HZ] [DT ...]

HHT with gamma = 1/2 - alpha, beta = (1 - alpha)^2 / 4 applied to u'' + w^2 u = 0.
The amplification matrix of (u, v, a) is built numerically; its principal eigenvalue pair
gives the algorithmic damping ratio xi = -ln|lambda| / arg(lambda) and the amplitude loss
per period, exp(-2 pi xi) applied once per period; rho_inf is the spectral radius as w dt -> inf.
"""
import sys
import numpy as np

f = float(sys.argv[1]) if len(sys.argv) > 1 else 5.46
dts = [float(x) for x in sys.argv[2:]] or [5e-4, 1e-3]


def amp(alpha, W):
    """Amplification matrix of HHT for u'' + W^2 u = 0 with unit time step (W = w dt)."""
    g, b = 0.5 - alpha, (1 - alpha) ** 2 / 4
    # unknowns at n+1: u1, v1, a1
    # a1 + (1+alpha) W^2 u1 - alpha W^2 u0 = 0
    # u1 = u0 + v0 + (0.5-b) a0 + b a1
    # v1 = v0 + (1-g) a0 + g a1
    L = np.array([[(1 + alpha) * W**2, 0, 1], [1, 0, -b], [0, 1, -g]])
    R = np.array([[alpha * W**2, 0, 0], [1, 1, 0.5 - b], [0, 1, 1 - g]])
    return np.linalg.solve(L, R)


for alpha in (-0.05, -0.3, -1 / 3):
    lam_inf = max(abs(np.linalg.eigvals(amp(alpha, 1e6))))
    for dt in dts:
        W = 2 * np.pi * f * dt
        ev = np.linalg.eigvals(amp(alpha, W))
        lam = ev[np.argmax(np.abs(ev.imag))]
        xi = -np.log(abs(lam)) / abs(np.angle(lam))
        print(f"alpha {alpha:+.4f}  dt {dt:.0e}  W = w dt {W:.4f}  damping ratio {xi:.3g}  "
              f"amplitude loss per period {1 - np.exp(-2 * np.pi * xi):.3g}  "
              f"period error {abs(np.angle(lam)) and (W / abs(np.angle(lam)) - 1):+.2e}  rho_inf {lam_inf:.3f}")
