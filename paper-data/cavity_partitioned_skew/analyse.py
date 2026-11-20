"""cavityFlexibleBottom, partitioned solids4foam sequence: Richardson
extrapolation of the linear and skew-corrected continuity-flux variants, and
the differences of the skew-corrected limit from the other solutions.

Reads levels.csv; writes richardson.csv and comparison.csv.
Run: python analyse.py
"""
import csv
import math
import os

R = 2.0
FS = 1.25

# Other solutions: limit of the finest triple of each sequence (u_y at A on
# the top surface, m; F_y per unit depth, N/m).
OTHERS = [
    ("SU2 + CalculiX (D. Armfield, pfv#102)", -0.2405588, -5.257784,
     "paper-data/cavity_su2_calculix/comparison/reference_limits.csv (pfv#102)"),
    ("FEniCSx monolithic, M1", -0.2405441802, -5.257801491,
     "paper-data/fenicsx_cavityflexiblebottom/data/coupled_orders.csv"),
    ("solids4foam quasi-monolithic #618", -0.24058, -5.257741,
     "computed from paper-data/cavity_monolithic_618/quasi_monolithic_618.csv"),
    ("Tukovic2018", -0.25103, -5.25674,
     "paper-data/cavity_plate_material_law/reference_richardson.csv"),
    ("Ansys", -0.25364, -5.27189,
     "paper-data/cavity_plate_material_law/reference_richardson.csv"),
    ("COMSOL (plateau, finest two levels)", -0.2431, -5.2954,
     "paper-data/cavity_plate_material_law_findings.md"),
]


def richardson(c, m, f):
    """Coarse c, medium m, fine f. Observed order, limit, GCI of the fine
    level (percent), and the limit and GCI with p = 2."""
    p = math.log((c - m) / (m - f)) / math.log(R)
    lim = f + (f - m) / (R**p - 1)
    gci = FS * abs((f - m) / f) / (R**p - 1) * 100
    lim2 = f + (f - m) / (R**2 - 1)
    gci2 = FS * abs((f - m) / f) / (R**2 - 1) * 100
    return p, lim, gci, lim2, gci2


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    seq = {}
    with open(os.path.join(here, "levels.csv")) as fh:
        for row in csv.DictReader(fh):
            seq.setdefault(row["variant"], []).append(
                (float(row["uy_A_m"]), float(row["Fy_N_per_m"])))
    limits = {}
    with open(os.path.join(here, "richardson.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["variant", "quantity", "levels", "observed_order",
                    "limit", "GCI_fine_percent", "limit_p2", "GCI_fine_p2_percent"])
        for var, vals in seq.items():
            for qi, q in enumerate(("uy_A_m", "Fy_N_per_m")):
                v = [x[qi] for x in vals]
                for i, lev in ((0, "1-3"), (1, "2-4")):
                    p, lim, gci, lim2, gci2 = richardson(*v[i:i + 3])
                    w.writerow([var, q, lev, f"{p:.4f}", f"{lim:.6f}",
                                f"{gci:.4f}", f"{lim2:.6f}", f"{gci2:.4f}"])
                    print(f"{var:15s} {q:11s} L{lev}: p={p:.3f} "
                          f"limit={lim:.6f} GCI={gci:.3f}% (p=2: {lim2:.6f})")
                    if lev == "2-4":
                        limits[(var, q)] = lim
    u = limits[("skew_corrected", "uy_A_m")]
    f = limits[("skew_corrected", "Fy_N_per_m")]
    u0 = limits[("linear", "uy_A_m")]
    f0 = limits[("linear", "Fy_N_per_m")]
    with open(os.path.join(here, "comparison.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["solution", "uy_limit_m", "Fy_limit_N_per_m",
                    "skew_minus_solution_uy_percent",
                    "skew_minus_solution_Fy_percent",
                    "linear_minus_solution_uy_percent",
                    "linear_minus_solution_Fy_percent", "source"])
        for name, ru, rf, src in OTHERS:
            # (s4f - other)/|other|; positive: s4f |value| smaller
            row = [name, ru, rf,
                   f"{(u - ru) / abs(ru) * 100:+.4f}",
                   f"{(f - rf) / abs(rf) * 100:+.4f}",
                   f"{(u0 - ru) / abs(ru) * 100:+.4f}",
                   f"{(f0 - rf) / abs(rf) * 100:+.4f}", src]
            w.writerow(row)
            print(f"{name:40s} uy {row[3]}% Fy {row[4]}% "
                  f"(linear: {row[5]}%, {row[6]}%)")
    print(f"linear minus skew-corrected limit: uy "
          f"{(u0 - u) / abs(u) * 100:+.4f}%, Fy {(f0 - f) / abs(f) * 100:+.4f}%")


if __name__ == "__main__":
    main()
