#!/usr/bin/env bash
# run_incident.sh - run the production training job exactly as the team ran it.
#
# Usage (from lab/work/, on your HOST):
#     bash run_incident.sh                        # the schedule the team enabled
#     bash run_incident.sh sampling_schedule_b.json   # Challenge schedule
#
# What it changes: writes incident_output.log next to this script and result
# files under results/. It runs the job on node0..node2 with a 60 s time limit
# and cleans up any leftover rank processes afterwards. Nothing else is touched.
set -uo pipefail
command -v docker >/dev/null 2>&1 || { echo "ERROR: 'docker' not found in this shell. Use WSL2, Git Bash or a macOS/Linux terminal where 'docker ps' works (see README, Step 6)."; exit 1; }
cd "$(dirname "$0")"
SCHED="${1:-sampling_schedule.json}"

echo "TICKET: Training stopped progressing after we enabled partial participation. Containers look fine."
echo "Starting the job (time limit 60 s). Open a second terminal now and collect your evidence."
echo "-----------------------------------------------------------------------------------------"

docker exec -u student node0 bash -lc \
  "mkdir -p ~/work/results && timeout 60 mpirun --hostfile ~/work/hostfile -n 6 --tag-output python3 ~/work/fedavg_sampling.py --schedule ~/work/$SCHED" \
  2>&1 | tee incident_output.log
rc=${PIPESTATUS[0]}

echo "-----------------------------------------------------------------------------------------"
if [ "$rc" -eq 124 ]; then
  echo "The 60 s time limit expired (exit code 124) and the job was stopped."
else
  echo "The job ended by itself (exit code $rc)."
fi
echo "Cleaning up leftover processes..."
bash cleanup_ranks.sh
