# SCx61 Week 3 — Submission (individual)

Name: ______________________    Group/Section: ____________

> Grading: the **evidence trail and your verification notes weigh at least as much as the working fix**. Every claim needs the command you ran and the real output. A fix with no trail scores lower than an honest trail with a partly wrong fix.

## (a) Your final `fedavg_v2_collectives.py`
Attach the file (or paste it). Does `python3 compare_fl.py` print PASS? Paste the last 5 lines:
```
```

## (b) Predictions and what really happened

| Slide | My prediction (before running) | What I observed (command + output) |
|---|---|---|
| 2 – Send/Recv calls per round at the server (5 clients) | | |
| 4 – collective for: (a) send the model to everyone (b) sum the scores (c) everyone needs the average | | |
| 5 – ranks call `Bcast`,`Reduce` / `Bcast`,`Reduce` / `Reduce`,`Bcast` | | |
| 6 – a non-rank-0 buffer before / after `Bcast` | | |
| 9 – why pack `[n_k·w_k, n_k]` in one buffer | | |
| 10 – MPI equals serial exactly? max difference measured: | | |
| 11 – what each rank holds after `Allreduce` (cross-rank check printed): | | |

## (c) Screenshot of the stalled run — MANDATORY
Must show the stalled output **and** `docker compose ps` in the same screenshot. Insert/attach it here.

## (d) Evidence trail (steps 1–8 of `debugging.md`)
For each step: the command, then the real output, then one sentence on what it rules in or out.

1. Symptom + command:
2. `docker compose ps`:
3. Infrastructure checks:
4. `ps` on each node:
5. Last line per rank (from the log):
6. Last week's explanation vs the arithmetic:
7. The code path I read (file, line numbers):
8. Fix + re-run + unrelated check:

## (e) AI debugging

**Round 1 — my verbatim prompt:**
```
```
**Round 1 — the AI's verbatim answer:**
```
```
**Round 2 — verdict table** (from `ROUND2.md`):

| Claim | Verdict (`VERIFIED` / `REFUTED` / `HIDES THE SYMPTOM`) | Proving command | Real output |
|---|---|---|---|
| A | | | |
| B | | | |
| C | | | |

## (f) Fix and `verify_fix.sh`
What I changed (a diff or the changed lines):
```
```
Output of `bash verify_fix.sh`:
```
```

## (g) Knowledge check and Challenge
These are answered in the **website form**, after you finish Step 8. They are not in this file on purpose: finish the debugging with your own evidence first.
