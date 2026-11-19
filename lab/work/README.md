# SCx61 Week 3 Lab — "One Call to Rule Them All"
### Collectives and a federated-averaging simulation

You replace hand-written `Send`/`Recv` loops with MPI **collectives** and use them to simulate **federated learning**: one server (rank 0, holds no data) and five clients (ranks 1–5, each with private, unequal data) train one model together by exchanging only weights.

```
PREDICT → BUILD → RUN → OBSERVE → BREAK → DEBUG → FIX → VERIFY
```

Write your prediction **before** each run. Steps 1–5 work on their own. Steps 6–8 use a small second zip (the Break Kit) and can be done at home.

---

## 0. Install the Week 3 files (before the session)

You need the Week 2 project folder (the folder that contains `lab/`). **Nothing is rebuilt: Week 3 uses the Week 2 image as it is.**

1. Put `SCx61_Week03_Student_Lab.zip` inside the Week 2 project folder (next to `lab/`).
2. Unzip it **there** (Windows: right-click → Extract All… into that same folder; allow overwriting `lab/.gitattributes`).
   ```bash
   unzip -o SCx61_Week03_Student_Lab.zip
   ```
3. Check that the files landed in the right place:
   ```bash
   ls lab/work/fl_common.py lab/work/fedavg_v2_collectives.py
   ```
   Both names must be printed. If you get "No such file", the zip went into the wrong folder (a `lab/lab/work/` folder means you unzipped one level too deep).

## 1. Start the cluster (no `--build`)

```bash
cd lab/config
docker compose up -d
docker compose ps          # node0, node1, node2: all  Up (healthy)
```

If Docker says the image does not exist, you have not done Week 2 on this machine — see **Offline path** below.

**Smoke tests** (copy–paste, from `lab/config`):
```bash
docker compose exec -u student node0 bash -lc 'mpirun --hostfile ~/work/hostfile -n 6 hostname'
```
→ six lines: `node0 node0 node1 node1 node2 node2` (in any order).
```bash
docker compose exec -u student node0 touch /home/student/work/test
docker compose exec node1 ls /home/student/work/test
docker compose exec -u student node0 rm /home/student/work/test
```
→ the second command prints the file's path.

Apple Silicon, Windows and macOS students: run both tests and tell your TA the result **before** the lab (not yet tested on those machines).

### Offline path / fallback
* **Offline:** use the Week 2 image tarball: `docker load -i scx61_week2_image.tar.gz` (SHA-256 `25d89bd4c2284867994c0b903626f1d93a6df7334c5b2c3ff215a2587588a708`), then `docker compose up -d` (still no `--build`).
* **Shared-folder permission problems on Windows/macOS:** the Week 2 named-volume + `docker compose cp` fallback applies unchanged (see your Week 2 README).

## 2. Enter the cluster

All MPI commands run inside `node0`, as `student`. From `lab/config`:
```bash
docker compose exec -u student -w /home/student/work node0 bash
```
Prompt: `student@node0:~/work$`. Edit the `.py` files on your own machine (`lab/work/`); the three nodes see changes instantly. The commands below are written for inside `node0`; in the slides they appear in the one-line `docker compose exec … bash -lc '…'` form.

## 3. The files

| File | What it is |
|---|---|
| `fl_common.py` | data generator, model, helper functions (complete — read it, don't edit) |
| `fedavg_serial.py` | the **serial oracle**: same algorithm, one process, no MPI (complete) |
| `fedavg_v1_manual.py` | FedAvg with Week 2-style `Send`/`Recv` (complete, for contrast) |
| `fedavg_v2_collectives.py` | **you fill 3 TODOs:** `Scatterv`, `Bcast`, `Reduce` |
| `fedavg_v3_allreduce.py` | **you fill 2 TODOs:** `Allreduce`, `Gather` |
| `compare_fl.py` | compares an MPI run with the oracle round by round → PASS / FAIL |
| `verify_fix.sh` | used in Step 8 |
| `SUBMISSION.md` | your answers and evidence — fill as you go |
| `debugging.md` | how to debug with evidence (read before Step 6) |

Dataset: synthetic, seed 42. Rank 0 = server (shard size **0**). Clients 1–5 hold 800, 600, 400, 200, 100 rows. The model has 21 weights (20 features + bias) = **168 bytes**.

---

## Step 1 — Hand out unequal homework (`Scatterv`)
**Predict:** how many rows will each rank print? What happens on rank 0?

Open `fedavg_v2_collectives.py`, fill **TODO 1**, then run only that far (the other TODOs will stop the program with a clear message — that is expected):
```bash
mpirun --hostfile hostfile -n 6 --tag-output python3 fedavg_v2_collectives.py
```
Expected: `rank 0: shard rows = 0`, then 800, 600, 400, 200, 100 on ranks 1–5. A zero-row shard is legal.

## Step 2 — One round: three calls
Fill **TODO 2** (`Bcast`) and **TODO 3** (`Reduce`) and run again. Rank 0 prints one line per round: `round 1: test acc=… loss=…`.
**Predict first:** why do we send `[n_k·w_k, n_k]` in one buffer instead of just `w_k`?

## Step 3 — Prove it: the oracle
**Predict:** will the MPI result equal the serial result *exactly* (`==`)? Then:
```bash
python3 fedavg_serial.py
python3 compare_fl.py
```
`compare_fl.py` prints the largest weight difference per round and **PASS** or **FAIL**. MPI adds numbers in an order the library chooses, so we compare with a tolerance (`1e-12`; the real differences measured over repeated runs were below `1e-15`). *TA check-point: show your PASS.*

## Step 4 — Everyone gets the average: `Allreduce`
Fill both TODOs in `fedavg_v3_allreduce.py`, run it, then `python3 compare_fl.py --mpi mpi_v3.npz`.
**Predict:** after `Allreduce`, what does each rank hold? The program ends with a cross-rank check — write down what it printed.

## Step 5 — Observe a healthy run
Run `fedavg_v2_collectives.py` with `--tag-output` and keep the output. Then, from a second terminal in `lab/config`:
```bash
docker compose ps
```
Annotate your own output (in `SUBMISSION.md`): which rank printed `entering Bcast` first? Find rank 4's line for round 7. *TA check-point.*

> **Take-home boundary.** Steps 1–5 are the "Build/Observe" half. Steps 6–8 below use the Break Kit and work at home too.

---

## Step 6 — The incident (BREAK)
> **Steps 6 and 8 run on your host with a `bash` shell that can also run `docker`** (a WSL2 terminal, Git Bash, macOS/Linux Terminal). Check first: `bash --version && docker ps`. If you only have PowerShell, tell your TA **before** the lab.

Unzip the Break Kit **from the Week 2 project folder** and check:
```bash
unzip -o SCx61_Week03_BreakKit.zip -d lab/work
ls lab/work/run_incident.sh lab/work/fedavg_sampling.py
```
Then, from `lab/work` on your host, **first keep an untouched copy** (Round 2 needs it), then run:
```bash
cp fedavg_sampling.py fedavg_sampling_original.py
bash run_incident.sh
```
It prints a one-line ticket and runs the job with a 60-second limit. **Do not touch anything for the first minute — watch.** In a second terminal collect evidence (see `debugging.md`). Take a **screenshot of the stalled run with `docker compose ps` visible** (mandatory for `SUBMISSION.md`).

## Step 7 — Debug (evidence first, then AI)
Follow `debugging.md`, then the AI Round 1 / Round 2 activity in the Break Kit (`ROUND2.md`).

## Step 8 — Fix and verify
Make the smallest change to `fedavg_sampling.py`, then:
```bash
bash verify_fix.sh
```
All three checks must pass. Paste the output into `SUBMISSION.md`.

**Challenge** (optional): see the end of `SUBMISSION.md`.

---

## Troubleshooting
* *"No such file" for `fl_common.py`* → wrong unzip folder (Step 0).
* *`mpirun` complains about the hostfile or script path* → you are not inside `node0:~/work`.
* *Left-over processes after Ctrl-C* → `bash cleanup_ranks.sh` (Break Kit) kills them by exact name on all 3 nodes.
* *`docker compose ps` shows `Up (healthy)` while the job looks stuck* → that is normal; health only says that SSH is up. See `debugging.md`.

## Software versions (unchanged from Week 2)
Open MPI 4.1.4 · mpi4py 3.1.4 · NumPy 1.24.2 · Python 3.11.2 (Debian bookworm). No performance claims are made anywhere in this lab — the test machine had only 2 CPU cores.
