#!/usr/bin/env python3
"""Create one Hron-Turek FSI3 preCICE case (OpenFOAM + CalculiX), corrected set-up.

    setup-case.py LEVEL OUTDIR [SOLID_LEVEL] [DT] [TOL]
        LEVEL       ring+box fluid level 1, 2 or 4 (1x' 11 764, 2x' 47 056, 4x' 188 224 cells)
        SOLID_LEVEL solid refinement factor (default 2*LEVEL, as in the solids4foam
                    corrected sequence: 1x'/s2x, 2x'/s4x, 4x'/s8x)
        DT          time step (default 1e-3 s, the value used here; solids4foam uses 5e-4, see README)
        TOL         preCICE relative convergence limit (default 1e-5, the solids4foam value)

Fluid: the solids4foam TurekHron2006 blockMesh refined as the ring+box family
(ht_mesh_family.py --ring-n 22 --rows-n 16 --tip-n 4 --aft-n 60 --wake-n 70, then
every in-plane division times LEVEL), as in verification/hronturek-production.
Solid: (105*SOLID_LEVEL) x (6*SOLID_LEVEL) x 1 C3D8I elements, 0.015 m deep.
"""
import re, shutil, subprocess, sys
from pathlib import Path

level = int(sys.argv[1]); out = Path(sys.argv[2])
slevel = int(sys.argv[3]) if len(sys.argv) > 3 else 2 * level
dt = float(sys.argv[4]) if len(sys.argv) > 4 else 1e-3
tol = float(sys.argv[5]) if len(sys.argv) > 5 else 1e-5
here = Path(__file__).resolve().parent
tpl = here.parent / "case"
if not tpl.is_dir():
    tpl = here.parent / "template"
if out.exists():
    sys.exit(f"{out} exists")
shutil.copytree(tpl, out)

# coupling / solid / fluid time step and coupling tolerance
for f in (out / "precice-config.xml", out / "solid-calculix/plate.inp"):
    f.write_text(f.read_text().replace("@DT@", repr(dt)).replace("@TOL@", f"{tol:g}"))
cd = out / "fluid-openfoam/system/controlDict"
cd.write_text(re.sub(r"(?m)^deltaT\s+[^;]+;.*$", f"deltaT          {dt!r};", cd.read_text()))

# fluid mesh: ring+box family
bm = out / "fluid-openfoam/system/blockMeshDict"
subprocess.run([sys.executable, str(here / "ht_mesh_family.py"), "--base", str(bm), "--level", str(level),
                "--ring-n", "22", "--rows-n", "16", "--tip-n", "4", "--aft-n", "60", "--wake-n", "70",
                "--out", str(bm) + ".ringbox"], check=True)
Path(str(bm) + ".ringbox").replace(bm)

# solid mesh
x0, x1, y0, y1, depth = 0.2489898, 0.6, 0.19, 0.21, 0.015
nx, ny = 105 * slevel, 6 * slevel
nid = lambda i, j, k: 1 + i + (nx + 1) * (j + (ny + 1) * k)
lines = ["*NODE, NSET=Nall"]
fix, surf = [], []
for k in range(2):
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            lines.append(f"{nid(i,j,k)}, {x:.12e}, {y:.12e}, {depth*k:.12e}")
            if i == 0:
                fix.append(nid(i, j, k))
            if j == 0 or j == ny or i == nx:
                surf.append(nid(i, j, k))
lines.append("*ELEMENT, TYPE=C3D8I, ELSET=Eall")
e = 0
for j in range(ny):
    for i in range(nx):
        e += 1
        n = [nid(i,j,0), nid(i+1,j,0), nid(i+1,j+1,0), nid(i,j+1,0),
             nid(i,j,1), nid(i+1,j,1), nid(i+1,j+1,1), nid(i,j+1,1)]
        lines.append(f"{e}, " + ", ".join(map(str, n)))
def nset(name, ids):
    lines.append(f"*NSET, NSET={name}")
    for a in range(0, len(ids), 10):
        lines.append(", ".join(map(str, ids[a:a+10])) + ",")
nset("Nfix", fix)
nset("Nsurface", surf)   # top, bottom and tip faces (the fluid 'plate' patch)
(out / "solid-calculix/mesh.inp").write_text("\n".join(lines) + "\n")
print(f"FSI3 fluid ring+box level {level}, solid level {slevel}: dt {dt}, tol {tol:g}, "
      f"solid {nx}x{ny} C3D8I ({e} elements, {len(surf)//2} interface points), case in {out}")
