"""FedAvg with client sampling ("partial participation") - production run.

    mpirun --hostfile ~/work/hostfile -n 6 --tag-output python3 ~/work/fedavg_sampling.py
    ... fedavg_sampling.py --schedule sampling_schedule_b.json --out NAME.npz

Which clients are selected each round comes from a schedule file.
Rank 0 is the server and is always present.
"""
import os

import numpy as np
from mpi4py import MPI

import fl_common as fl

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
fl.enable_stack_dump(rank)

here = os.path.dirname(os.path.abspath(__file__))
schedule = fl.load_schedule(fl.parse_arg("--schedule", os.path.join(here, "sampling_schedule.json")))
out_name = fl.parse_arg("--out", "mpi_sampling.npz")

counts_rows = np.array(fl.COUNTS)
counts = counts_rows * (fl.D + 1)
displs = np.concatenate(([0], np.cumsum(counts)[:-1]))
if rank == 0:
    shards, test = fl.make_data()
    sendbuf = np.vstack(shards)
else:
    sendbuf = None
shard = np.empty((counts_rows[rank], fl.D + 1))
comm.Scatterv([sendbuf, counts, displs, MPI.DOUBLE], shard, root=0)

w = fl.initial_weights() if rank == 0 else np.zeros(fl.W_LEN)
total = np.zeros(fl.W_LEN + 1)
W, ACC, LOSS = [], [], []
# the rounds this rank takes part in (rank 0: all of them)
my_rounds = [r for r in range(1, fl.ROUNDS + 1) if rank == 0 or rank in schedule[r]]
for rnd in range(1, fl.ROUNDS + 1):
    selected = schedule[rnd]

    fl.log(rank, rnd, "entering Bcast")
    comm.Bcast(w, root=0)

    if rank == 0:
        contrib = np.zeros(fl.W_LEN + 1)
    elif rank in selected:
        wk = fl.local_train(w, shard)
        n = shard.shape[0]
        contrib = np.append(n * wk, n)
    else:
        contrib = np.zeros(fl.W_LEN + 1)

    fl.log(rank, rnd, "entering Reduce")
    comm.Reduce(contrib, total, op=MPI.SUM, root=0)

    if rank == 0:
        w[:] = total[:-1] / total[-1]
        W.append(w.copy())
        ACC.append(fl.accuracy(w, test))
        LOSS.append(fl.loss(w, test))
        print(f"round {rnd}: selected={selected} test acc={ACC[-1]:.3f} loss={LOSS[-1]:.4f}", flush=True)
        np.savez(fl.results_path(out_name), W=np.array(W), acc=np.array(ACC), loss=np.array(LOSS))
    fl.log(rank, rnd, "done")
