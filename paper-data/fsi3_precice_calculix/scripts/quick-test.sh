#!/usr/bin/env bash
# quick-test.sh SRC DEST NWIN NP : restart the coupled stage of SRC from its t = 2 s state for NWIN windows
# (diagnostic runs only; DEST is modified by the caller before running with RUN=1)
source "$(dirname "$(readlink -f "$0")")/env-precice.sh"
SRC=$(readlink -f "$1"); DEST=$2; NWIN=$3; NP=${4:-4}
if [ -z "$RUN" ]; then
  mkdir -p "$DEST"; cp -r "$SRC/precice-config.xml" "$SRC/solid-calculix" "$DEST/"
  rm -f "$DEST"/solid-calculix/{precice-*,log.ccx,plate.{frd,dat,sta,cvg,12d}} ; rm -rf "$DEST/solid-calculix/precice-profiling"
  mkdir -p "$DEST/fluid-openfoam"; cp -r "$SRC"/fluid-openfoam/{0,constant,system} "$DEST/fluid-openfoam/"
  for p in "$SRC"/fluid-openfoam/processor*; do b=$(basename $p); mkdir -p "$DEST/fluid-openfoam/$b"; cp -r $p/constant $p/2 "$DEST/fluid-openfoam/$b/"; done
  exit 0
fi
cd "$DEST"; C=$PWD; dt=$(foamDictionary -entry deltaT -value fluid-openfoam/system/controlDict)
tend=$(python3 -c "print(round(2+$NWIN*$dt,8))"); tmax=$(python3 -c "print(round($NWIN*$dt,8))")
sed -i "s|<max-time value=\"[^\"]*\" />|<max-time value=\"$tmax\" />|" precice-config.xml
sed -i "s|^ \([0-9.e-]*\), 4\.$| \1, $tmax|" solid-calculix/plate.inp
cd fluid-openfoam
foamDictionary system/controlDict -entry endTime -set $tend >/dev/null
foamDictionary system/controlDict -entry functions/preCICE_Adapter/enabled -set true >/dev/null
rm -rf $C/precice-run
mpirun -np $NP --bind-to none pimpleFoam -parallel > log.pimpleFoam.coupled 2>&1 &
pf=$!
( cd $C/solid-calculix && timeout 1800 ccx_preCICE -i plate -precice-participant Solid > log.ccx 2>&1 ) &
pc=$!
wait $pf; rf=$?; wait $pc; rc=$?
echo "fluid rc $rf, solid rc $rc"
