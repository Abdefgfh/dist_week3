"""FedAvg with MPI collectives - STARTER (fill in the 3 TODOs).

Run:  mpirun --hostfile ~/work/hostfile -n 6 --tag-output python3 ~/work/fedavg_v2_collectives.py
"""
import numpy as np
from mpi4py import MPI

import fl_common as fl

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
fl.enable_stack_dump(rank)
out_name = fl.parse_arg("--out", "mpi_v2.npz")

# ---- Step 1: hand out unequal shards with Scatterv -------------------
counts_rows = np.array(fl.COUNTS)                 # rows per rank (rank 0 -> 0)
counts = counts_rows * (fl.D + 1)                 # Scatterv counts are in ELEMENTS
displs = np.concatenate(([0], np.cumsum(counts)[:-1]))
if rank == 0:
    shards, test = fl.make_data()
    sendbuf = np.vstack(shards)                   # rank 0's block is empty
else:
    sendbuf = None
shard = np.empty((counts_rows[rank], fl.D + 1))   # rank 0: shape (0, 21) - legal
# TODO 1 - Scatterv: hand every rank its own block of rows.
#   * send side: [sendbuf, counts, displs, MPI.DOUBLE] (counts/displs are in ELEMENTS, already computed above)
#   * receive   : the `shard` buffer;   root=0
#   * rank 0 receives 0 rows: that is legal. `shard` already has shape (0, 21) there - leave it as is.
#   * `sendbuf` is None on every rank except 0 - that is fine, only the root's send side is read.
comm.Scatterv([sendbuf, counts, displs, MPI.DOUBLE], shard, root=0)
print(f"rank {rank}: shard rows = {shard.shape[0]}", flush=True)

# ---- Steps 2: FedAvg rounds -------------------------------------------
w = fl.initial_weights() if rank == 0 else np.zeros(fl.W_LEN)   # only the server knows w0
total = np.zeros(fl.W_LEN + 1)
W, ACC, LOSS = [], [], []
for rnd in range(1, fl.ROUNDS + 1):
    fl.log(rank, rnd, "entering Bcast")
    # TODO 2 - Bcast: copy the root's `w` into every rank's `w` (in place, same call on ALL ranks).
    #   Hint: comm.Bcast(buffer, root=...)
    comm.Bcast(w, root=0)

    if rank == 0:
        contrib = np.zeros(fl.W_LEN + 1)          # server contributes nothing
    else:
        wk = fl.local_train(w, shard)
        n = shard.shape[0]
        contrib = np.append(n * wk, n)            # [n_k * w_k , n_k]

    fl.log(rank, rnd, "entering Reduce")
    # TODO 3 - Reduce: element-wise SUM of every rank's `contrib` into `total` on rank 0.
    #   Hint: comm.Reduce(sendbuf, recvbuf, op=..., root=...)   (recvbuf is only used on the root)
    comm.Reduce(contrib, total, op=MPI.SUM, root=0)

    if rank == 0:
        w[:] = total[:-1] / total[-1]
        W.append(w.copy())
        ACC.append(fl.accuracy(w, test))
        LOSS.append(fl.loss(w, test))
        print(f"round {rnd}: test acc={ACC[-1]:.3f} loss={LOSS[-1]:.4f}", flush=True)
        np.savez(fl.results_path(out_name), W=np.array(W), acc=np.array(ACC), loss=np.array(LOSS))
    fl.log(rank, rnd, "done")
