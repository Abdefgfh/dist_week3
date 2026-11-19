# SCx61 Week 3 — Break Kit

These files are for Steps 6–8 of the lab (`README.md`). They unzip straight into `lab/work/` (the zip has no folder of its own).

```bash
# from the Week 2 project folder (the one that contains lab/)
unzip -o SCx61_Week03_BreakKit.zip -d lab/work
ls lab/work/run_incident.sh lab/work/fedavg_sampling.py lab/work/ROUND2.md
```
All three names must be printed.

| File | What it is |
|---|---|
| `fedavg_sampling.py` | the team's training job, now with client sampling (which clients take part in each round comes from a schedule file) |
| `sampling_schedule.json` | the schedule the team enabled |
| `sampling_schedule_b.json` | a second schedule, for the Challenge |
| `sampling_schedule_full.json` | every client in every round (used by `verify_fix.sh`) |
| `run_incident.sh` | runs the job exactly as the team ran it (60-second limit) |
| `cleanup_ranks.sh` | stops leftover job processes on all 3 nodes (runs automatically at the end of `run_incident.sh`) |
| `ROUND2.md` | the AI Round 2 sheet |

## Before you edit anything
Keep an untouched copy — Round 2 needs it:
```bash
cp fedavg_sampling.py fedavg_sampling_original.py
```

## Run it
From `lab/work` on your **host** (not inside a container), in a terminal where both `bash` and `docker` work (WSL2, Git Bash, macOS/Linux Terminal):
```bash
bash run_incident.sh
```
Open a second terminal and follow `debugging.md`. When you are done looking, the script stops the job and cleans up by itself. If you pressed Ctrl-C and something is left over: `bash cleanup_ranks.sh`.

Everything the scripts change is listed at the top of each script.
