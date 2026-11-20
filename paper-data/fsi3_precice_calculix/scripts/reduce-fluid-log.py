#!/usr/bin/env python3
"""Reduce the coupled pimpleFoam log (one solve per coupling iteration) for the repository.

    reduce-fluid-log.py LOG OUT_CONVERGED OUT_ITERATIONS

OUT_CONVERGED:  the header, then for each time step only the block of its last (converged)
                coupling iteration, every line kept; then the log's tail.
OUT_ITERATIONS: one line per coupling iteration: time, time window, coupling iteration,
                Courant mean/max, initial residual of the last p solve, ExecutionTime, ClockTime.
A block (one coupling iteration) starts at the preCICE 'it N ... time-window W' line that
precedes it and runs through its 'Time = ' line, the PIMPLE solve and the mapping lines after it.
"""
import re, sys

src, out_conv, out_it = sys.argv[1:4]
header, blocks, cur = [], [], None
for line in open(src, errors="replace"):
    if re.search(r"\]\s+it \d+ ", line) and "time-window" in line:
        if cur is not None:
            blocks.append(cur)
        cur = [line]
    elif cur is None:
        header.append(line)
    else:
        cur.append(line)
if cur is not None:
    blocks.append(cur)


def btime(b):
    return next((l.split("=", 1)[1].strip() for l in b if l.startswith("Time = ")), "n/a")


with open(out_it, "w") as fi:
    fi.write("time window iteration Co_mean Co_max last_p_initial_residual ExecutionTime_s ClockTime_s\n")
    for b in blocks:
        num = lambda l: re.findall(r"[-+]?\d[\d.eE+-]*", l)
        co = num(next((l for l in b if l.startswith("Courant Number")), ""))
        p = [l for l in b if "Solving for p," in l]
        pres = re.search(r"Initial residual = ([^,]+)", p[-1]).group(1) if p else "nan"
        it = re.search(r"it (\d+) .*time-window (\d+)", next(l for l in b if "time-window" in l))
        ex = num(next((l for l in b if l.startswith("ExecutionTime")), ""))
        fi.write(f"{btime(b)} {it.group(2)} {it.group(1)} {co[0] if co else 'nan'} {co[1] if len(co) > 1 else 'nan'} "
                 f"{pres} {ex[0] if ex else 'nan'} {ex[1] if len(ex) > 1 else 'nan'}\n")

with open(out_conv, "w") as fc:
    fc.writelines(header)
    fc.write("// reduce-fluid-log.py: only the last (converged) coupling iteration of each time step is kept\n")
    for i, b in enumerate(blocks):
        if i + 1 == len(blocks) or btime(blocks[i + 1]) != btime(b):
            fc.writelines(b)
print(f"{len(blocks)} blocks, {len({btime(b) for b in blocks})} time steps")
