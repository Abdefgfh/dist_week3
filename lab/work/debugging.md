# Debugging guide — Week 3 (evidence first)

> **Who sent that line?** Before you interpret a log line, find out who sent it.
> The healthcheck's own `ssh-keyscan` lines (`Unable to negotiate with 127.0.0.1 … sk-…`, every ~20 s) come from a probe inside the container, **not from your program**. They have nothing to do with MPI.

## The eight steps

Do them in order. For every step write down **the exact command** and **the exact output** in `SUBMISSION.md`.

1. **State the symptom and the exact command that produced it.** (What did you run? What did you expect? What happened instead?)
2. **`docker compose ps`** (from `lab/config`). Is a container dead, restarting, unhealthy? Rule "a container died" in or out.
3. **Rule out the infrastructure** with the Week 1–2 checks: SSH by name (`docker compose exec -u student node0 ssh node1 hostname`) and name lookup (`docker compose exec node0 getent hosts node1`).
4. **`ps` on each node.** Is every rank process alive? How many are there, and where?
   `docker compose exec node1 ps -eo pid,pcpu,stat,args | grep fedavg_sampling`
5. **Read the tagged log.** For *each* rank, what is the last line it printed? Which ranks are *missing* from the last round?
6. **Test last week's explanation with arithmetic** before believing it. (Last week's hang depended on message size. How big is a message today? Look up Open MPI's eager limit and compare.)
   `python3 -c "print((20+1)*8, 'bytes')"`
   `docker compose exec -u student node0 bash -lc 'ompi_info --param btl vader --level 9 | grep btl_vader_eager_limit'`
7. **Read the code path that decides whether a rank calls the collective.** (`grep -n "selected" fedavg_sampling.py` is a good start.)
8. **Fix the smallest thing**, re-run the exact failing command, and re-run one unrelated check (the Step 3 oracle).

## Toolbox (commands, not answers)

| I want to know… | Command (host, from `lab/config` unless noted) |
|---|---|
| are the containers healthy? | `docker compose ps` |
| are the rank processes alive? what are they doing? | `docker compose exec node1 ps -eo pid,pcpu,stat,args \| grep fedavg_sampling` (state `R` = running on CPU, `S` = sleeping) |
| which line is each Python rank executing right now? | `docker compose exec node1 pkill -USR1 -f '^python3 .*fedavg_sampling'` — repeat for `node0`, `node2` — then `docker compose exec -u student node0 bash -lc 'cat ~/work/results/stack_rank*.txt'`. **Do this LAST:** the signal also reaches ranks that are no longer inside your Python code; they die, and `mpirun` stops the whole job (you will see `exited on signal 10` and exit code 138). Collect everything else first. |
| what was the last thing each rank said? | read `lab/work/incident_output.log` (the output of `run_incident.sh`) |
| which rank is which process? | the first lines of the log: `rank 3: pid … on node1` |
| how big is one message, and what is the eager limit? | `python3 -c "print((20+1)*8, 'bytes')"` and `docker compose exec -u student node0 bash -lc 'ompi_info --param btl vader --level 9 \| grep btl_vader_eager_limit'` |
| clean up after a stall | `bash cleanup_ranks.sh` |

The stack-dump file for a rank is **empty** if that rank is not inside your Python code any more (for example when it has already left the program).

## The AI step (Step 7)

**Principle: AI proposes. Engineer verifies.**

**Round 1 — you write the prompt.** Paste your *real* evidence into this template and give it to an AI assistant. Keep the **verbatim** prompt and the **verbatim** answer for `SUBMISSION.md`.

```
I'm running a 6-rank MPI job (Open MPI 4.1.4, mpi4py) on a 3-container Docker Compose cluster
(node0–node2, 2 ranks per node). All containers show Up (healthy). Federated-averaging training
(rank 0 = server, ranks 1–5 = clients) stalls at round [N]. No error is printed and no process
has died.

Evidence:
- docker compose ps output: [paste]
- Tagged per-rank log (last 30 lines): [paste]
- ps on each node: [paste]
- The round loop of the program (about 40 lines): [paste]

Expected: 10 rounds complete. Actual: [describe].

Give me:
1) your top 2–3 hypotheses ranked by likelihood;
2) for each, one command I can run to confirm or rule it out;
3) the exact output that would confirm vs reject each;
4) the smallest possible fix;
5) one command to prove it worked.
Do not tell me to "check my MPI setup".
```

**Round 2** — in the Break Kit (`ROUND2.md`): a pre-written AI answer with three claims. You decide, with a command and its real output for each claim, whether it is `VERIFIED`, `REFUTED`, or `HIDES THE SYMPTOM`.

An AI answer that sounds like "it's the same as last week" is a **hypothesis, not evidence**.

---

## Reference — read this only AFTER you finished Round 1

<details>
<summary>Round 1 reference: an <b>instructor-written model answer</b> (this is NOT the output of a live AI run)</summary>

*What a strong answer to the template above looks like, given evidence like yours.*

1. **Most likely: one rank is not taking part in the collective calls.** The log shows rank 3's last line is `round 4: done` while ranks 0 and 1 wait in `round 5: entering Reduce` and ranks 2, 4, 5 are in the round-6 `Bcast`. A collective needs every rank of the communicator to call it. Confirm: stack dumps (`pkill -USR1 …` then `cat stack_rank*.txt`) show the waiting ranks inside `comm.Reduce` / `comm.Bcast` lines; read the loop that decides which rounds rank 3 runs (`grep -n selected fedavg_sampling.py`). Reject if: all six ranks print `entering …` for the same round.
2. **Message too large for the eager limit (last week's cause).** Confirm/reject: `python3 -c "print((20+1)*8,'bytes')"` → 168 bytes, far below the eager limit that `ompi_info` reports (4096 bytes by default in Open MPI 4.1.x). Rejected.
3. **A container or the network failed.** Confirm/reject: `docker compose ps` (all healthy), `ssh node1 hostname`, `ps` shows all six rank processes alive. Rejected.

Smallest fix: make every rank call `Bcast` and `Reduce` in every round; a client that is not selected skips the local training and contributes `[0·w, 0]`. Proof: `bash verify_fix.sh`.

*Optional, for the instructor:* paste the transcript of the same prompt run in a fresh AI session here: `[instructor transcript: ________________ ]`
</details>
