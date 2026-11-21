# Environment for the 3dTube level-3 rerun on corrected meshes (paper-fsi-verification #57, 17 Nov)
# solids4foam development 206437983, built into its own platforms directory so the
# b200718f4 build (#64) and the preCICE adapter in the default user platforms dir stay untouched.
# Usage:  source ~/OpenFOAM/balis-v2512/env-tube-l3.sh
source /opt/openfoam/OpenFOAM-v2512/etc/bashrc
export PETSC_DIR=/opt/openfoam/ThirdParty-v2512/platforms/linux64GccDPInt32/petsc-3.21.2
export PETSC_ARCH=
OLDLIB=$FOAM_USER_LIBBIN; OLDAPP=$FOAM_USER_APPBIN
S4F_PLAT=$HOME/OpenFOAM/balis-v2512/platforms-s4f-206437983/$WM_OPTIONS
export FOAM_USER_LIBBIN=$S4F_PLAT/lib FOAM_USER_APPBIN=$S4F_PLAT/bin
export FOAM_MODULE_LIBBIN=$FOAM_USER_LIBBIN FOAM_MODULE_APPBIN=$FOAM_USER_APPBIN
strip() { echo "$1" | tr : '\n' | grep -vxF "$2" | paste -sd:; }
export PATH=$FOAM_USER_APPBIN:$(strip "$PATH" "$OLDAPP")
export LD_LIBRARY_PATH=$PETSC_DIR/lib:$FOAM_USER_LIBBIN:$(strip "$LD_LIBRARY_PATH" "$OLDLIB")
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
