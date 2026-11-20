# solids4foam learnings register

The verification campaign keeps finding subtle choices in solids4foam, each one a fix, an option or a set-up detail, that change results. This register records each finding while it is fresh.

**Why it exists.** After the papers are submitted, each entry has to reach solids4foam in a robust form, so that a user who has not read the papers cannot pick the wrong option by accident. That means one of:

- a corrected default;
- a warning or a fatal error on the unsafe combination;
- a fixed tutorial;
- as a last resort, documentation.

The solver paper (paper-monolithic-fsi) keeps a matching register for the quasi-monolithic coupling. Entries that affect both couplings are cross-referenced.

**How to add an entry.** Give it the next free number, and never renumber entries. Fill in every field, citing evidence by issue, PR or paper-data path. Update the *State* field when solids4foam changes.

**Status values:**

- **Open:** nothing in solids4foam yet.
- **Tutorial only:** fixed in the affected tutorials; an uninformed user can still hit it in a new case.
- **Issue filed:** a solids4foam issue exists.
- **Robust:** a default, check or error in the code prevents it.
- **Done:** robust and documented.

## Summary

| # | Topic | Area | Effect if wrong | Status |
|---:|---|---|---|---|
| 1 | Continuity-flux interpolation in `pimpleFluid` | partitioned fluid | 0.05% F_y bias, slowly converging (cavity) | Open |
| 2 | `fixedFluxPressure` on a moving FSI wall | partitioned fluid | silently zeroGradient | Open |
| 3 | Interface pressure condition | partitioned fluid | O(h) wall pressure; transients | Issue filed (#721) |
| 4 | Interface viscous traction form | both couplings | O(1) on a deforming wall | Open |
| 5 | Wall-normal velocity gradient at moving walls | partitioned fluid | 1.5–3.8% in FSI3 | Robust (#671) |
| 6 | Default coupling convergence test | coupling | accepts unconverged steps | Issue filed (#552) |
| 7 | Strict test at a true steady state | coupling | runs to nOuterCorr, false warning | Issue filed (#710) |
| 8 | First coupling iterate without a predictor | coupling | late added-mass crashes | Robust (#492) |
| 9 | Unrelaxed PIMPLE outer loop at large νΔt/h² | partitioned fluid | divergence (Mok 128²) | Open (#700) |
| 10 | Mesh families with cell-size jumps | meshing | spoils convergence studies | Open |
| 11 | Wall arcs on curved two-region meshes | meshing | ~1 µm AMI wall mismatch | Tutorial only |
| 12 | cfMesh octree aligned with interface faces | meshing | bulged flap, bad cells | Open |
| 13 | `#codeStream` static cache on macOS | tutorials | NaN or FPE, non-deterministic | Issue filed (#711) |
| 14 | Units of the interface-displacement log line | output | misread as metres | Open |
| 15 | Benchmark definitions in tutorials | tutorials | wrong reference comparison | Open |

## Entries

### 1. Continuity-flux interpolation in `pimpleFluid`

- **Found:** 2026-11-20, cavityFlexibleBottom. Dylan Armfield's SU2 + CalculiX comparison (pfv#102) showed our partitioned F_y limit 0.054% from SU2, FEniCSx and the quasi-monolithic solution, outside every GCI.
- **What goes wrong:** `pimpleFluid` builds the continuity flux from `fvc::flux(HbyA)`. That looks up `flux(HbyA)` in `interpolationSchemes` and falls back to `default linear`, without skew correction.
  - The `interpolate(U) skewCorrected linear` entry in the tutorials reaches only `Uf`, not the continuity flux.
  - On a strongly deformed mesh, here the plate ends of the cavity, the error converges slowly (about 1.5× per halving at the finest levels). Four levels then give a falsely tight GCI.
  - The quasi-monolithic solver has interpolated its continuity flux with skew correction since #597.
- **Evidence:** /Users/philipc/claude-runs/cavgap, build 206437983, strict Aitken.
  - Adding only `flux(HbyA) skewCorrected linear;` moves the levels 1–3 F_y limit from −5.26050 (+0.052% from SU2) to −5.25695 (−0.016%; GCI 0.14%).
  - The quasi-monolithic levels 1–3 limit is −5.25742.
  - Agent B's catalogue (paper-monolithic-fsi `paper-data/a2_discretisation_differences.md`, D4) shows the quasi-monolithic and partitioned results agree to below 0.001% when both use linear.
  - The level-4 confirmation is running.
- **Right choice:** skew-corrected interpolation of the continuity flux on any mesh that moves or deforms.
- **State:** Open. The cavity tutorial change is planned as a solids4foam PR.
- **Robust fix to consider:** make `pimpleFluid` use the `interpolate(U)` scheme for `flux(HbyA)` when no explicit entry exists, or warn when a moving mesh runs on the `default linear` fallback. Check the other moving-mesh tutorials, such as FSI3 and the 3-D tube.

### 2. `fixedFluxPressure` on a moving FSI wall

- **Found:** 2026-11-20, Seevani Bali's preCICE FSI3 (pfv#104).
- **What goes wrong:**
  - On a wall where velocity is fixed, `constrainHbyA` sets HbyA_b = U_b, and the ddt correction is zero there. `constrainPressure` therefore receives a zero numerator, and `fixedFluxPressure` gives dp/dn = 0.
  - A user expecting the normal-momentum gradient −ρ n·a gets zeroGradient without being told. Her "base" and "zerograd" runs agree to 2e-5.
  - This applies to `pimpleFoam` and to `pimpleFluid`, which calls `constrainPressure`.
- **Right choice:** `movingWallPressure` for the acceleration term (see entry 3), or an explicit zeroGradient where that is the intent.
- **State:** Open.
- **Robust fix to consider:** a warning from the FSI interface set-up when the fluid interface pressure is `fixedFluxPressure`; documentation in the FSI tutorials' README.

### 3. Interface pressure condition

- **Found:** October–November 2026, ringAddedMass, Hessenthaler, womersleyTube and the solver-paper comparison.
- **What goes wrong:**
  - `zeroGradient` gives an O(h) wall-pressure error, d·dp/dn. On a moving wall it misses −ρ n·a, and on any wall the viscous part μ ∂²u_n/∂n².
  - `movingWallPressure` adds the acceleration only.
  - The quasi-monolithic solver uses the full normal-momentum gradient, which includes the viscous terms.
  - `movingWallPressure` fails in enclosed fluid domains (ringAddedMass with IQN-ILS: "Continuity error cannot be removed"). Under IQN-ILS it can also stall temporal convergence at small Δt.
- **Right choice:** Philip's standard since 2026-11-17 is `movingWallPressure` for every partitioned run, with the omitted viscous term stated in the text.
- **State:** Issue filed: solids4foam#721 (viscous term, enclosed domains, removal of the hard `refCast`).
- **Robust fix to consider:** the #721 proposal, then make it the FSI tutorials' default.

### 4. Interface viscous traction form

- **Found:** solver-paper comparison of the couplings (paper-monolithic-fsi `a2_discretisation_differences.md`, D6), womersleyTube.
- **What goes wrong:**
  - Partitioned passes `n & (-devReff)`; quasi-monolithic passes `rho*nuEff*snGrad(U)`.
  - On a deforming wall they differ by μ grad(u·n), a physical term that does not vanish under refinement. In the Womersley tube it is about 3e-4 relative.
  - At a stationary wall the difference is O(h).
  - A related rule (#583, rejected): the traction must be the fluid's own discrete wall flux. Quadratic wall-shear corrections degrade the partitioned convergence.
- **Right choice:** not settled; the two couplings should use the same, correct, conservative form.
- **State:** Open. Owned by the solver paper.
- **Robust fix to consider:** a shared traction routine for both couplings, tested on the Womersley tube.

### 5. Wall-normal velocity gradient at moving walls

- **Found:** November 2026, FSI3. The corrected sequence moved by 1.5–3.8% (u_x −3.1%, u_y amplitude −1.5%, drag amplitude −3.8%, lift amplitude −2.2% at 2x′).
- **What goes wrong:** before #671, `newMovingWallVelocity` and `elasticWallVelocity` set the wall-normal gradient of u_n inconsistently with continuity.
- **State:** Robust. #671 made the continuity-based gradient the default. Every paper result computed with these conditions before #671 is superseded or caveated (pfv#93, pfv#97).
- **Remaining:** none, except checking that no tutorial pins the old behaviour.

### 6. Default coupling convergence test

- **Found:** October 2026, IQN-ILS steady and quasi-steady phases.
- **What goes wrong:** the default test accepts a step when min(r1, r2) is below the tolerance. Near steady state, r2 is tiny from the first iteration, so a one-iteration step is accepted and the solution creeps.
- **Right choice:** `requireAllResidualMeasures yes`, the strict test.
- **State:** Issue filed: solids4foam#552.
- **Robust fix to consider:** make the strict test the default, once entry 7 is fixed.

### 7. Strict test at a true steady state

- **Found:** 2026-11-14, partitioned Hessenthaler rF2.
- **What goes wrong:** at round-off steadiness, r1 (relative to the step's largest residual) cannot fall below 1e-4. Every step then runs to `nOuterCorr` and prints "The resulting solution may be invalid", although it is converged. This costs 4–6× the coupling iterations.
- **State:** Issue filed: solids4foam#710, which proposes an absolute floor for r1.
- **Robust fix to consider:** the #710 floor; needed before entry 6's default can change.

### 8. First coupling iterate without a predictor

- **Found:** October 2026, HronTurekFsi3 late crashes (#383, #489).
- **What goes wrong:** the relaxed first iterate without a predictor causes an added-mass spike.
- **State:** Robust. `predictor` defaults to `yes` since #492.

### 9. Unrelaxed PIMPLE outer loop at large νΔt/h²

- **Found:** 2026-11-10, Mok lid-driven cavity at 128².
- **What goes wrong:** with no PIMPLE relaxation, the fluid outer loop diverges inside a frozen-interface coupling iteration (νΔt/h² = 4.1 at 128², against 2.3 at 96²). It looks like a coupling failure, but it is not one.
- **Right choice:** p 0.3 / U 0.7 relaxation with residual control, as in run `m128_relax2`. It reaches t = 70 within 0.5% of Kratos.
- **State:** Open. Documented in solids4foam#700, but the tutorial `fvSolution` is unchanged until it is tested on the coarse levels.
- **Robust fix to consider:** relaxed defaults in the tutorial, and a log hint when the p residual grows across outer correctors.

### 10. Mesh families with cell-size jumps

- **Found:** October 2026, the Hron–Turek ring+box family.
- **What goes wrong:**
  - Ring+box: neighbour size ratios of 2–2.8:1 through the wake on every level, so refining does not remove the jump error and the observed order is unreliable.
  - FSI3 on the old family also showed a first-order issue.
- **Right choice:** audit the neighbour size ratios before any convergence study. FSI3 now uses agent B's Gmsh family.
- **State:** Open (practice, not code).
- **Robust fix to consider:** a small utility, or a `checkMesh` function object, that reports the distribution of neighbour size ratios, used in the verification drivers.

### 11. Wall arcs on curved two-region meshes

- **Found:** November 2026, 3-D pressure-pulse tube.
- **What goes wrong:** blockMeshDict arc points written to too few digits put the fluid and solid walls about 1 µm apart, so the AMI interface sees a gap.
- **State:** Tutorial only. solids4foam 9b52c2303 writes the arcs at full precision, and the paper uses the corrected meshes.
- **Robust fix to consider:** a check in the FSI interface set-up that reports the largest fluid–solid interface face-centre gap at start-up.

### 12. cfMesh octree aligned with interface faces

- **Found:** 2026-11-10, Hessenthaler feF1.
- **What goes wrong:** cfMesh centres its octree on the surface bounding box. When the flap faces land on octree planes, they bulge by 0.02 mm, and the strict `checkMesh` finds concave cells and bad tets.
- **Right choice:** shift the octree phase by adding one unused point to the `.fms`, then check with `checkMesh -allGeometry -allTopology`.
- **State:** Open (meshing practice).

### 13. `#codeStream` static cache on macOS

- **Found:** 2026-11-14, womersleyTube.
- **What goes wrong:** a function-local static inside an inline function is shared across `#codeStream` libraries. The result is NaN or an FPE with identical inputs, varying from run to run.
- **State:** Issue filed: solids4foam#711.

### 14. Units of the interface-displacement log line

- **What goes wrong:** "Maximal accumulated displacement" is normal motion × deltaCoeffs, in cell widths, not metres. Values of 3–6 are normal; it was misread once (#687, retracted).
- **State:** Open.
- **Robust fix to consider:** state the unit in the log line.

### 15. Benchmark definitions in tutorials

Set-up details that cost time because the tutorial or its reference did not say them:

- **Cavity force depth:** the published forces are for a 0.05 m depth, and the tutorial is 1 m deep.
- **Cavity plate law:** the Tuković et al. plate law is not confirmed; it may be neo-Hookean rather than StVK.
- **collapsibleChannel:** needs the Poiseuille initial flow (`setPoiseuilleFlow`). The oomph-lib reference is first order in `--refine`.
- **FSI3:** ring+box meshes as in entry 10. `linearUpwind grad(U)` convection and the coupling tolerances of the shared set-up.

**State:** Open. Each tutorial README should state these.
