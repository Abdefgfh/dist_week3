# SCx61 Week 3 — Pre-class checklist (one page)

Do these before the session. Total: about 5 minutes.

- [ ] **1. Files in place.** `SCx61_Week03_Student_Lab.zip` unzipped in the Week 2 project folder.
      `ls lab/work/fl_common.py lab/work/fedavg_v2_collectives.py` prints both names.
- [ ] **2. Cluster up — no rebuild.**
      `cd lab/config && docker compose up -d && docker compose ps`
      → `node0`, `node1`, `node2` all **Up (healthy)**.
- [ ] **3. Week 2 smoke test.**
      `docker compose exec -u student node0 bash -lc 'mpirun --hostfile ~/work/hostfile -n 6 hostname'`
      → six hostnames, 2 per node.
- [ ] **4. Shared-folder check.**
      `docker compose exec -u student node0 touch /home/student/work/test`
      `docker compose exec node1 ls /home/student/work/test`
      then remove that one file: `docker compose exec -u student node0 rm /home/student/work/test`
- [ ] **5. Host shell for Steps 6 and 8.** `bash --version && docker ps` both work in the terminal you will use (WSL2, Git Bash, or macOS/Linux Terminal). PowerShell only? Tell your TA before the lab.
- [ ] **6. Apple Silicon / Windows / macOS only:** send your TA the result of items 3 and 4 before the lab.

If anything fails: do not change files — write down the exact command and the exact message, and tell your TA.
