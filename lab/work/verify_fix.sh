#!/usr/bin/env bash
# verify_fix.sh - prove your fix to fedavg_sampling.py is correct.
#
# Usage (on your HOST, from lab/work/):   bash verify_fix.sh
# What it changes: writes result files under results/ and verify_fix_output.log
# here. It runs your CURRENT fedavg_sampling.py three ways:
#   (a) the schedule the team enabled           -> must finish all 10 rounds
#   (b) ...and match the MASKED serial oracle   -> compare_fl.py must PASS
#   (c) every client in every round             -> must match the FULL oracle (PASS)
# Each run has a 60 s time limit; leftover rank processes are cleaned up.
set -uo pipefail
command -v docker >/dev/null 2>&1 || { echo "ERROR: 'docker' not found in this shell. Use WSL2, Git Bash or a macOS/Linux terminal where 'docker ps' works (see README, Step 6)."; exit 1; }
cd "$(dirname "$0")"
fail=0
run_in_node0() { docker exec -u student node0 bash -lc "$1"; }
mpi() {  # mpi <schedule> <out-name>
  run_in_node0 "mkdir -p ~/work/results && rm -f ~/work/results/$2 && cd ~/work && timeout 60 mpirun --hostfile ~/work/hostfile -n 6 python3 ~/work/fedavg_sampling.py --schedule ~/work/$1 --out $2"
}
{
echo "=== (a) run with the enabled schedule ==="
mpi sampling_schedule.json mpi_sampling_fix.npz | grep -E "^round "
rc=${PIPESTATUS[0]}
if [ "$rc" -ne 0 ]; then echo "(a) FAIL: the job did not finish (exit code $rc)"; fail=1; bash cleanup_ranks.sh; else echo "(a) OK: the job finished all rounds"; fi

echo; echo "=== (b) masked serial oracle vs your run ==="
run_in_node0 "cd ~/work && python3 fedavg_serial.py --mask sampling_schedule.json --out serial_masked.npz > /dev/null && python3 compare_fl.py --mpi mpi_sampling_fix.npz --serial serial_masked.npz" || fail=1

echo; echo "=== (c) full participation vs the full serial oracle ==="
mpi sampling_schedule_full.json mpi_sampling_full.npz > /dev/null || { echo "(c) FAIL: the job did not finish"; fail=1; bash cleanup_ranks.sh; }
run_in_node0 "cd ~/work && python3 fedavg_serial.py > /dev/null && python3 compare_fl.py --mpi mpi_sampling_full.npz --serial serial.npz" || fail=1

echo
if [ "$fail" -eq 0 ]; then echo "VERIFY: ALL CHECKS PASSED"; else echo "VERIFY: SOMETHING FAILED - read the lines above"; fi
[ "$fail" -eq 0 ]   # exit status of this group = the verdict
} 2>&1 | tee verify_fix_output.log
exit "${PIPESTATUS[0]}"
