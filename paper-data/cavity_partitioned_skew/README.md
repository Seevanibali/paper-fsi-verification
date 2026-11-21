# cavityFlexibleBottom: partitioned sequence with a skew-corrected continuity flux

The partitioned solids4foam four-level sequence of Section 5 (flexible-bottom
cavity) is the `skew_corrected` variant here. It replaces the earlier
sequence (`linear` variant), which differed only in the interpolation of the
continuity flux.

## Why

Dylan Armfield's independent SU2 + CalculiX solution (pfv#102) put the
F_y Richardson limit of the earlier sequence, −5.260619 N/m (from the
four-decimal levels), 0.054 % from SU2 (−5.257784), FEniCSx (−5.257801)
and the solids4foam quasi-monolithic solution #618 (−5.257741). Its GCI was
0.019 %.

- **Cause:** `pimpleFluid` builds the continuity flux with `fvc::flux(HbyA)`,
  which used the default `linear` interpolation without skew correction.
  The momentum interpolation, `interpolate(U)`, was already
  `skewCorrected linear` in the tutorial. On the strongly deformed fluid mesh
  at the plate ends, the uncorrected flux error converges slowly. As a
  result the four levels gave a falsely tight GCI.
- **Fix:** add `flux(HbyA) skewCorrected linear;` to `system/fluid/fvSchemes`
  (solids4foam PR #743, tutorial only; open on 20 Nov 2026). Nothing else
  differs between the two variants (checked by `diff -r` of `system/` and
  `constant/` of the level-3 cases).

## Files

- `levels.csv`: the four levels of both variants (u_y at point A on the top
  surface, F_y per unit depth).
- `mesh_convergence_rows.csv`: every row of the `mesh_convergence.csv` files
  of the runs, with the run directory, the flux scheme and whether the row is
  part of the sequence (`in_sequence`). Each run directory also holds a
  level-1 run at the same Δt; those rows are kept as a Δt check (see below).
- `analyse.py`: reads `levels.csv`, writes `richardson.csv` (observed order,
  limit and GCI, Fs = 1.25, for levels 1–3 and 2–4, and the p = 2 limit) and
  `comparison.csv` (differences of the levels 2–4 limits from the other
  solutions). Run `python analyse.py`.

## Results (levels 2–4)

| | linear | skew-corrected |
|---|---:|---:|
| u_y: observed order, limit (m), GCI | 2.02, −0.240671, 0.29 % | 1.98, −0.240583, 0.31 % |
| u_y limit with p = 2 (m) | −0.240680 | −0.240573 |
| F_y: observed order, limit (N/m), GCI | 2.36, −5.260588, 0.019 % | 1.86, −5.257947, 0.045 % |
| F_y limit with p = 2 (N/m) | −5.260884 | −5.257712 |
| levels 1–3 orders (u_y, F_y) | 1.96, 2.38 | 1.93, 2.03 |

The linear F_y limit here uses the six-digit levels 2 and 3. With the
four-decimal levels it is −5.260619.

The skew-corrected limit minus each other solution's limit, relative to that
solution (negative: solids4foam magnitude larger). The SU2 limits are from
`paper-data/cavity_su2_calculix/comparison/reference_limits.csv` on the
branch `DylanArmfield:evidence/cavity-su2-calculix` of pfv#102, which is not
yet merged:

| Solution | u_y | F_y |
|---|---:|---:|
| SU2 + CalculiX (pfv#102) | −0.010 % | −0.003 % |
| FEniCSx, M1 (supplement) | −0.016 % | −0.003 % |
| solids4foam quasi-monolithic #618 | −0.001 % | −0.004 % |
| Tuković et al. (2018) | +4.16 % | −0.023 % |
| ANSYS | +5.15 % | +0.26 % |
| COMSOL (plateau) | +1.04 % | +0.71 % |

The skew correction moves the levels 2–4 limits by +0.036 % (u_y) and
+0.050 % (F_y), i.e. to smaller magnitudes.

## Provenance

- **Build:** solids4foam `206437983` (after #671), OpenFOAM v2512
  (`87ed40d256-20251219`), `darwin64ClangDPInt32Opt`, an isolated user build
  (`/Users/philipc/OpenFOAM/fsi3ho-v2512`, environment
  `/Users/philipc/claude-runs/fsi3ho/env-mac.sh`), serial, on a Mac Studio
  (Mac13,2), macOS.
- **Driver:** the tutorial's `verification/Allverify --variants aitken
  --levels 1,<L> --delta-t <Δt> --keep-going`, through
  `/Users/philipc/claude-runs/cavgap/run_one.sh <dir> <L> <Δt>`.
- **Runs:** `/Users/philipc/claude-runs/cavgap/`
  - skew-corrected: `skew_L{1,2,3,4}/verification/work/aitken/mesh{1,2,3,4}`
    and `skew_L*/verification/postProcessing/mesh_convergence.csv`;
    logs `log.skew_L*`. Completed on 20 Nov 2026 (level 4 at 23:27 GMT).
  - linear: `lin_L{1,2,3}/...`, the same layout.
  - `skew_L1` holds level 1 at Δt = 0.5 s in `mesh1` and level 2 at the same
    Δt in `mesh2`. Only its `mesh1` is in the sequence; level 2 is from
    `skew_L2` at Δt = 0.25 s. The same applies to `lin_L1`.
- **Settings (all levels):**
  - Aitken coupling, relaxation factor 0.1, `outerCorrTolerance 1e-5`, and
    `requireAllResidualMeasures yes` (the strict test).
  - Coupling starts at t = 10 s, and the end time is 200 s.
  - Δt = 0.5, 0.25, 0.125 and 0.0625 s on levels 1–4, halved with Δx.
  - Fluid: `nOuterCorrectors 1` per coupling iteration, and fluid
    linear-solver tolerances of 1e-6 (relTol 0).
  - Values are the steady values of the driver at t = 200 s. Its steady
    spread is at most 5.4e-5 m (u_y) and 1.6e-5 N/m (F_y).
- **Level 4 only:** `nOuterCorr 40` (20 on levels 1–3) and fluid
  linear-solver tolerances of 1e-8. The earlier level-4 run needed the
  same settings, because with the defaults the strict coupling test fails
  at t ≈ 56 s.
- **Linear level 4:** u_y −0.240111 m, F_y −5.2598 N/m. These are from the
  earlier strict run on the same build and set-up, as recorded with
  solids4foam PR #743 and in the reply on pfv#102. F_y was recorded to four
  decimals only, and the run directory is not in `cavgap`.

## Δt check (resolved 2026-11-21)

The steady state depends on the pseudo-time step, through the Δt-dependent
coefficient of the pressure–velocity coupling term. It does not depend on
the solver tolerances. The dependence vanishes rapidly under refinement.

Skew-corrected runs:

| Level | Δt (s) | settings | u_y (m) | F_y (N/m) |
|---:|---:|---|---:|---:|
| 1 | 0.5 | default | −0.204831 | −5.160695 |
| 1 | 0.5 | 1e-8, nOuterCorr 40 | −0.204791 | −5.159491 |
| 1 | 0.25 | default | −0.204842 | −5.160978 |
| 1 | 0.125 | default | −0.204884 | −5.162218 |
| 1 | 0.0625 | default | −0.205141 | −5.170031 |
| 1 | 0.0625 | 1e-8, nOuterCorr 40 | −0.205135 | −5.169844 |
| 2 | 0.5 | default | −0.231281 | −5.233737 |
| 2 | 0.25 | default (sequence) | −0.231268 | −5.233332 |
| 2 | 0.125 | default | −0.231209 | −5.231570 |
| 2 | 0.0625 | default | −0.231216 | −5.231802 |
| 3 | 0.125 | default (sequence) | −0.238225 | −5.251155 |
| 3 | 0.0625 | default | −0.238223 | −5.251101 |

Linear runs:

| Level | Δt (s) | settings | u_y (m) | F_y (N/m) |
|---:|---:|---|---:|---:|
| 1 | 0.5 | default | −0.204573 | −5.152815 |
| 1 | 0.0625 | 1e-8, nOuterCorr 40 | −0.204687 | −5.156283 |
| 3 | 0.125 | default | −0.238403 | −5.256547 |
| 3 | 0.0625 | default | −0.238409 | −5.256743 |

Findings:

- **Tolerances:** with Δt fixed, they change the result by at most 0.02 %.
- **Δt:** reducing it to 0.0625 s changes F_y by 0.18 % on level 1,
  0.03 % on level 2 and 0.001 % on level 3. The change is larger with skew
  correction (linear level 1: 0.07 %).
- **Fixed Δt 0.0625 s on levels 2–4:**
  - u_y: p 1.99, limit −0.240579;
  - F_y: p 1.96, limit −5.257798, 0.0003 % from SU2.
  - The scaled-Δt sequence (p 1.98 / 1.86; −0.240583 / −5.257947) agrees to
    within 0.003 %.

The diagnostic runs are in `/Users/philipc/claude-runs/cavgap/`:

- `tolA`, `tolB`: level 1 at Δt 0.5 with the 1e-8 settings, and at Δt 0.0625
  with the default settings;
- `tolC`: linear level 1 at Δt 0.0625 with the 1e-8 settings;
- `dtL2a`, `dtL2b`: level 2 at Δt 0.125 and 0.0625;
- `dtL3a`, `dtL3lin`: level 3 at Δt 0.0625, skew-corrected and linear.

Each was run with `solids4Foam` directly, in a copy of the corresponding
driver `meshN` case, with only `deltaT` (and, where stated, the tolerances)
changed. The values are the last `force.dat` and `solidPointDisplacement`
rows, at t = 200 s.

## Earlier values kept elsewhere

Until this change, `../cavity_plate_material_law/reference_levels.csv`
held the pre-#671 strict sequence:

- u_y: −0.204568, −0.231445, −0.238404, −0.240113;
- F_y: −5.1528, −5.2388, −5.2566, −5.2599;
- limits: −0.240669 / −5.26065.

The FEniCSx supplement and its package
(`../fenicsx_cavityflexiblebottom/`) still compare against those values.
