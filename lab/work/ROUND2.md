# AI Round 2 — "Verify the answer"

> Needs `fedavg_sampling_original.py`, the untouched copy of the job. If `ls fedavg_sampling_original.py` fails, you skipped the `cp` in `README.md` Step 6 (and `KIT_README.md`): run it **before** you edit `fedavg_sampling.py`.

An AI assistant was given the evidence from this lab's stalled run and answered with the text below. **It is a pre-written answer.** It contains three claims. **None of the three is the correct fix.** For each claim you decide:

* `VERIFIED` — the claim is true **and** its advice would solve the problem
* `REFUTED` — your evidence shows the claim is false
* `HIDES THE SYMPTOM` — the advice makes the job finish, but the result is wrong

Use only lab commands, run each one for real, and paste the output into the table in `SUBMISSION.md`. *AI proposes. Engineer verifies.*

---

## The AI's answer

> The job stalls at round 5 with every container healthy, so I would look at three things.
>
> **Claim A — the network between the containers is broken.** Docker's internal DNS on `clusternet` is probably not resolving `node1`/`node2` any more, so one rank cannot be reached. Restart the Docker daemon and run the job again.
>
> **Claim B — same as last week.** The message is probably larger than the eager limit, so the send blocks until the receiver posts a matching receive. Raise the limit and run again:
> `mpirun --mca btl_vader_eager_limit 65536 --mca btl_tcp_eager_limit 65536 …`
>
> **Claim C — give the missing client something to send.** When a client is not selected, let it send its *previous* local weights instead of dropping out. Every client then takes part in every round and the job completes. In a copy of the program, replace the loop header and the contribution lines like this:
>
> ```python
> last_local = np.zeros(fl.W_LEN)                 # add before the loop
> for rnd in range(1, fl.ROUNDS + 1):             # every rank runs every round
>     selected = schedule[rnd]
>     ...
>     if rank == 0:
>         contrib = np.zeros(fl.W_LEN + 1)
>     else:
>         if rank in selected:
>             last_local = fl.local_train(w, shard)      # selected: train as usual
>         n = shard.shape[0]
>         contrib = np.append(n * last_local, n)         # not selected: re-send last weights
> ```

---

## Toolbox (commands only — you decide what the output means)

Run from `lab/config` unless it says otherwise. Start the stalled job first with `bash run_incident.sh` (from `lab/work`) when a command needs a stalled job.

**For claim A**
```bash
docker compose ps
docker compose exec -u student node0 ssh node1 hostname
docker compose exec -u student node0 ssh node2 hostname
docker compose exec node0 getent hosts node1 node2
docker compose exec node1 ps -eo pid,pcpu,stat,args | grep fedavg_sampling
```

**For claim B**
```bash
python3 -c "print((20+1)*8, 'bytes')"
docker compose exec -u student node0 bash -lc 'ompi_info --param btl vader --level 9 | grep -E "btl_vader_eager_limit"'
docker compose exec -u student node0 bash -lc 'cd ~/work && timeout 30 mpirun --hostfile hostfile -n 6 --tag-output --mca btl_vader_eager_limit 65536 --mca btl_tcp_eager_limit 65536 python3 fedavg_sampling_original.py'
bash ../work/cleanup_ranks.sh
```

**For claim C** (in `lab/work`, on a copy)
```bash
cp fedavg_sampling_original.py claim_c.py        # edit claim_c.py as claim C says
cd ../config
docker compose exec -u student node0 bash -lc 'cd ~/work && timeout 60 mpirun --hostfile hostfile -n 6 python3 claim_c.py --out mpi_claim_c.npz'
docker compose exec -u student node0 bash -lc 'cd ~/work && python3 fedavg_serial.py --mask sampling_schedule.json --out serial_masked.npz && python3 compare_fl.py --mpi mpi_claim_c.npz --serial serial_masked.npz'
```
Questions to ask yourself: does the job finish? Does the result match the **masked** oracle (the clients that really took part)? What does `compare_fl.py` say?
