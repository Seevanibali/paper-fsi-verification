#!/bin/bash
# 3dTube level 3 on the corrected meshes (paper-fsi-verification #57, request of 17 Nov):
# solids4foam development 206437983 + blockMeshDicts from 9b52c2303, Robin-Neumann, BDF2, 32 cores.
source ~/OpenFOAM/balis-v2512/env-tube-l3.sh
cd ~/OpenFOAM/balis-v2512/solids4foam-206437983/tutorials/fluidSolidInteraction/3dTube/verification
{ date; hostname; lscpu | grep -E 'Model name|^CPU\(s\)'; free -g | head -2;
  echo "solids4foam $(git -C ../../../.. rev-parse --short HEAD) + meshes from 9b52c2303"; git -C ../../../.. status --short;
  echo "OpenFOAM $WM_PROJECT_VERSION, $(mpirun --version | head -1), $(gcc --version | head -1)";
  echo "PETSC_DIR $PETSC_DIR"; which solids4Foam; env | grep -E '^(OMP|OPENBLAS)_NUM_THREADS';
  echo "load at start: $(uptime)"; } > log.environment 2>&1
echo "Started: $(date)" | tee log.Allverify
./Allverify --study mesh --levels 3 --cores 32 2>&1 | tee -a log.Allverify
echo "Finished: $(date) (exit ${PIPESTATUS[0]})" | tee -a log.Allverify
echo "load at end: $(uptime)" >> log.environment
