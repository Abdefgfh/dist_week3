#!/usr/bin/env bash
# cleanup_ranks.sh - stop any leftover MPI job processes on node0, node1, node2.
#
# Usage (on your HOST, from anywhere):   bash cleanup_ranks.sh
# What it changes: sends SIGTERM to processes named exactly 'mpirun' / 'orted',
# and to python3 processes whose command line starts with 'python3' and names a
# fedavg_ program, inside the three containers. Then prints what is left.
set -uo pipefail
command -v docker >/dev/null 2>&1 || { echo "ERROR: 'docker' not found in this shell. Use WSL2, Git Bash or a macOS/Linux terminal where 'docker ps' works (see README, Step 6)."; exit 1; }
for n in node0 node1 node2; do
  docker exec "$n" pkill -x mpirun 2>/dev/null
  docker exec "$n" pkill -x orted 2>/dev/null
  docker exec "$n" pkill -f '^python3 .*fedavg_' 2>/dev/null
done
sleep 2
left=0
for n in node0 node1 node2; do
  out=$(docker exec "$n" bash -c 'ps -eo pid,pcpu,stat,args | grep -E "[f]edavg_|[o]rted|[m]pirun"')
  if [ -n "$out" ]; then echo "[$n] still running:"; echo "$out"; left=1; fi
done
[ "$left" -eq 0 ] && echo "clean: no mpirun/orted/fedavg process left on node0, node1, node2"
