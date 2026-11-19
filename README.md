# Distributed Federated Learning with MPI

A distributed implementation of **Federated Averaging (FedAvg)** using **MPI**, **Python**, and **Docker**. This project explores distributed model training, client sampling, collective communication, and debugging synchronization issues in a multi-node environment.

---

## Overview

Federated Learning (FL) is a distributed machine learning approach in which multiple clients collaboratively train a global model without sharing their local training data.

This project implements a simplified Federated Averaging workflow using MPI, where:

- A central server coordinates the training process.
- Multiple clients perform local model training on their own data shards.
- Clients send their weighted model updates to the server.
- The server aggregates the updates to produce a new global model.
- The updated global model is broadcast to the participating clients.

The environment consists of **3 Docker containers running 6 MPI processes**: one server process and five client processes.

## Architecture

### Distributed Environment

| Component | Description |
|---|---|
| `node0` | MPI server and client processes |
| `node1` | Distributed client processes |
| `node2` | Distributed client processes |
| Rank 0 | Central aggregation server |
| Ranks 1–5 | Federated learning clients |
| MPI | Inter-process communication |
| Docker Compose | Container orchestration |

Each container runs two MPI processes, giving a total of six ranks.

### Federated Averaging

The server aggregates client models using a sample-weighted average:

\[
w_{global} =
\frac{\sum_{k=1}^{K} n_k w_k}
{\sum_{k=1}^{K} n_k}
\]

Where:

- \(w_k\) is the model update from client \(k\).
- \(n_k\) is the number of local training samples on client \(k\).
- \(K\) is the number of participating clients.

This ensures that clients with larger datasets contribute proportionally to the global model.

## Technologies Used

- **Python** – Core implementation.
- **MPI / mpi4py** – Distributed communication between processes.
- **Open MPI** – MPI runtime.
- **Docker** – Containerized execution environment.
- **Docker Compose** – Multi-container orchestration.
- **NumPy** – Numerical computations and model aggregation.
- **Git & GitHub** – Version control and project hosting.

---

## Project Structure

```text
dist_week3/
│
├── lab/
│   ├── config/
│   │   └── compose.yaml
│   │
│   ├── source_code/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   │
│   └── work/
│       ├── README.md
│       ├── KIT_README.md
│       ├── ROUND2.md
│       ├── SUBMISSION.md
│       ├── debugging.md
│       ├── fedavg_sampling.py
│       ├── fedavg_serial.py
│       ├── fedavg_v1_manual.py
│       ├── fedavg_v2_collectives.py
│       ├── fedavg_v3_allreduce.py
│       ├── compare_fl.py
│       ├── verify_fix.sh
│       ├── run_incident.sh
│       ├── sampling_schedule.json
│       ├── sampling_schedule_b.json
│       ├── sampling_schedule_rotating.json
│       └── results/
│
└── README.md
```

---

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Docker Desktop
- Docker Compose
- Git

Python, NumPy, and MPI dependencies are provided by the container environment.

### 1. Clone the Repository

```bash
git clone https://github.com/Abdefgfh/dist_week3.git
cd dist_week3/lab
```

### 2. Start the Docker Environment

```bash
docker compose -f config/compose.yaml up -d --build
```

Check that the containers are running:

```bash
docker compose -f config/compose.yaml ps
```

### 3. Access the MPI Environment

Open a shell inside the `node0` container:

```bash
docker compose -f config/compose.yaml exec node0 bash
```

Navigate to the working directory:

```bash
cd ~/work
```

### 4. Run the Distributed Implementation

The main sampling-based implementation can be executed using:

```bash
mpirun --hostfile hostfile -n 6 \
python3 fedavg_sampling.py \
--schedule sampling_schedule.json \
--out mpi_sampling.npz
```

The exact schedule determines which clients participate in each training round.

---

## Implementations

The project contains multiple implementations exploring different MPI communication strategies.

| File | Description |
|---|---|
| `fedavg_v1_manual.py` | Initial manual communication implementation |
| `fedavg_v2_collectives.py` | Uses MPI collective communication |
| `fedavg_v3_allreduce.py` | Uses MPI Allreduce for aggregation |
| `fedavg_sampling.py` | Federated learning with client sampling |
| `fedavg_serial.py` | Serial reference implementation |
| `compare_fl.py` | Compares distributed and serial model results |

## Key Experiment: MPI Collective Synchronization

One of the most important challenges was debugging a deadlock caused by inconsistent collective communication.

### The Problem

The original implementation allowed only selected clients to enter the training loop.

However, MPI collective operations such as:

- `MPI.Bcast`
- `MPI.Reduce`
- `MPI.Allreduce`

require all processes in the communicator to participate in the same collective sequence.

When an unselected client skipped a round, the remaining processes could become blocked while waiting for that client.

### The Solution

The training loop was modified so that **every MPI rank participates in every communication round**.

- Rank 0 performs server-side aggregation.
- Selected clients perform local training and contribute weighted updates.
- Unselected clients skip local training and contribute zero-valued vectors.
- Every rank still executes the required collective operations.

This prevents the collective mismatch while preserving the intended client-sampling behavior.

### Why Zero Contributions?

An unselected client must not contribute an old model update or previous sample count.

Instead, it contributes:

\[
contribution_k = 0
\]

This ensures that only selected clients affect the global aggregation.

---

## Bonus Experiments

### 1. Sampling Schedule B

A deliberately modified schedule excluded client 3 from round 5.

The experiment demonstrated how a client skipping a collective operation can cause a deadlock that may only become visible several rounds later.

The MPI execution timed out, and the comparison against the serial reference showed that only 9 out of 10 rounds were produced.

### 2. Rotating Client Sampling

A rotating schedule was created to select three clients per round:

| Round | Selected Clients |
|---:|---|
| 1 | 1, 2, 3 |
| 2 | 2, 3, 4 |
| 3 | 3, 4, 5 |
| 4 | 4, 5, 1 |
| 5 | 5, 1, 2 |
| 6 | 1, 2, 3 |
| 7 | 2, 3, 4 |
| 8 | 3, 4, 5 |
| 9 | 4, 5, 1 |
| 10 | 5, 1, 2 |

The distributed implementation completed all 10 rounds successfully.

### 3. Correctness Verification

The MPI implementation was compared against a serial masked reference implementation using:

```bash
python3 fedavg_serial.py \
--mask sampling_schedule_rotating.json \
--out serial_rotating.npz
```

Then the results were compared:

```bash
python3 compare_fl.py \
--mpi mpi_rotating.npz \
--serial serial_rotating.npz
```

**Verified result: PASS**

| Metric | Result |
|---|---:|
| MPI training rounds | 10 |
| Serial training rounds | 10 |
| Comparison tolerance | \(10^{-12}\) |
| Maximum observed weight difference | \(4.441 \times 10^{-16}\) |
| Final comparison | PASS |

The extremely small numerical differences are consistent with floating-point rounding.

---

## Key Learnings

Through this project, I learned:

1. **Distributed Computing:** How to run multiple MPI processes across Docker containers.
2. **MPI Communication:** How to use collective operations such as Broadcast, Reduce, and Allreduce.
3. **Federated Learning:** How to implement sample-weighted model aggregation.
4. **Client Sampling:** How to select different clients across training rounds.
5. **Debugging Distributed Systems:** How collective mismatches can cause deadlocks and how to investigate them using process states and logs.
6. **Correctness Testing:** How to validate distributed results against a serial reference implementation.

## Author

**Abdefgfh**

GitHub: [@Abdefgfh](https://github.com/Abdefgfh)

---

*This project was developed as part of a Distributed Systems university assignment.*
