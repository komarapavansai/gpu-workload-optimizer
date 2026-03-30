# GPU Workload Optimizer

---

## How to Run

### 1. Run in default mode

python main.py

To execute with the particular input file under /inputs directory
python main.py <filename>

### 2. Run with time-aware scheduling

ENABLE_TIME=true python main.py

### 3. Store output to a file

As of now, all console output will be stored in output.txt. To disable it, comment this line (1st line after import statements) in main.py

sys.stdout = open("output.txt", "w")

---

## Code Structure

.
├── main.py               # Entry point
├── scheduler.py          # Core scheduling logic
├── models/
│   ├── job.py            # Job definition
│   ├── server.py         # Server logic
│   ├── allocation.py     # Allocation metadata
│   └── exceptions.py     # Custom exceptions

---

### Flow

1. Jobs sorted by size (largest first)
2. Initial allocation happens
3. Some jobs go to pending queue
4. Time progresses (if enabled)
5. Completed jobs free resources
6. Pending jobs are retried

---

## Example Scenario

This example is based on the following input:

### Servers

- **S1**: 8 GPUs, 80 GB per GPU
- **S2**: 8 GPUs, 80 GB per GPU
- **S3**: 4 GPUs, 48 GB per GPU

### Jobs

- **J1**: 6 GPUs, 60 GB, execution time = 12
- **J2**: 4 GPUs, 40 GB, execution time = 7
- **J3**: 2 GPUs, 20 GB, execution time = 3
- **J4**: 10 GPUs, 20 GB, execution time = 5
- **J5**: 8 GPUs, 80 GB, execution time = 15
- **J6**: 4 GPUs, 48 GB, execution time = 6
- **J7**: 1 GPU, 10 GB, default execution time = 10
- **J8**: 8 GPUs, 80 GB, execution time = 4

---

## Initial Job Order

The jobs are sorted by size:

1. **J5** = 8 × 80 = 640
2. **J8** = 8 × 80 = 640
3. **J1** = 6 × 60 = 360
4. **J4** = 10 × 20 = 200
5. **J6** = 4 × 48 = 192
6. **J2** = 4 × 40 = 160
7. **J3** = 2 × 20 = 40
8. **J7** = 1 × 10 = 10

---

## Time = 0 : Initial Scheduling

### Step 1: Schedule J5 (8 GPUs × 80 GB)

Feasible servers:
- **S1** → score = 0
- **S2** → score = 0
- **S3** → Not possible

Tie is broken by server ID, so **J5 is placed on S1**.

**Allocation**
- `J5 -> S1, GPUs [0,1,2,3,4,5,6,7], start=0, end=15`

**State**
- `S1 = [0,0,0,0,0,0,0,0]`
- `S2 = [80,80,80,80,80,80,80,80]`
- `S3 = [48,48,48,48]`

---

### Step 2: Schedule J8 (8 GPUs × 80 GB)

Feasible servers:
- **S1** → Not possible
- **S2** → score = 0
- **S3** → Not possible

So **J8 is placed on S2**.

**Allocation**
- `J8 -> S2, GPUs [0,1,2,3,4,5,6,7], start=0, end=4`

**State**
- `S1 = [0,0,0,0,0,0,0,0]`
- `S2 = [0,0,0,0,0,0,0,0]`
- `S3 = [48,48,48,48]`

---

### Step 3: Try J1 (6 GPUs × 60 GB)

- **S1** → Not possible
- **S2** → Not possible
- **S3** → Not possible

However, J1 **can fit** on an empty 8×80 server, so it is marked **temporarily unschedulable** and moved to the pending queue.

---

### Step 4: Try J4 (10 GPUs × 20 GB)

No server has 10 GPUs, so J4 is **permanently unschedulable**.

---

### Step 5: Schedule J6 (4 GPUs × 48 GB)

Feasible servers:
- **S1** → Not possible
- **S2** → Not possible
- **S3** → score = 0

So **J6 is placed on S3**.

**Allocation**
- `J6 -> S3, GPUs [0,1,2,3], start=0, end=6`

**State**
- `S1 = [0,0,0,0,0,0,0,0]`
- `S2 = [0,0,0,0,0,0,0,0]`
- `S3 = [0,0,0,0]`

---

### Step 6: Try J2, J3, J7

At time 0:
- no server has enough free GPUs/memory for these jobs right now
- each of them is **temporarily unschedulable**
- they are added to the pending queue

### Summary at time 0

**Running**
- J5 on S1
- J8 on S2
- J6 on S3

**Pending**
- J1, J2, J3, J7

**Permanent failure**
- J4

---

## Time = 4 : J8 Completes

When time advances from 0 to 4:
- **J8** completes on S2
- S2 becomes free again

**New S2 state**
- `[80,80,80,80,80,80,80,80]`

Now the scheduler retries pending jobs in size order: **J1, J2, J3, J7**

---

### Retry J1 (6 GPUs × 60 GB)

Feasible servers:
- **S1** → Not possible
- **S2** → score = 15200
- **S3** → Not possible

\[
6 \cdot 20^2 + 2 \cdot 80^2 = 15200
\]

So **J1 is placed on S2**.

**Allocation**
- `J1 -> S2, GPUs [0,1,2,3,4,5], start=4, end=16`

**State**
- `S2 = [20,20,20,20,20,20,80,80]`

---

### Retry J2 (4 GPUs × 40 GB)

- **S2** → only 2 GPUs have at least 40 GB
- **S3** → still occupied
- **S1** → occupied

So **J2 remains pending**.

---

### Retry J3 (2 GPUs × 20 GB)

Feasible servers:
- **S2** → score = 14400
- **S1** and **S3** → Not possible

If J3 is placed on the two smallest feasible GPUs on S2:

`[20,20,20,20,20,20,80,80] -> [0,0,20,20,20,20,80,80]`

\[
4 \cdot 20^2 + 2 \cdot 80^2 = 14400
\]

So **J3 is placed on S2**.

**Allocation**
- `J3 -> S2, GPUs [0,1], start=4, end=7`

---

### Retry J7 (1 GPU × 10 GB)

Feasible servers:
- **S2** → score = 14100
- **S1** and **S3** → Not possible

J7 uses the smallest feasible GPU on S2:

`[0,0,20,20,20,20,80,80] -> [0,0,10,20,20,20,80,80]`

\[
10^2 + 3 \cdot 20^2 + 2 \cdot 80^2 = 14100
\]

So **J7 is placed on S2**.

**Allocation**
- `J7 -> S2, GPU [2], start=4, end=14`
- Since execution time is missing, it uses the default value **10**

---

## Time = 6 : J6 Completes

At time 6:
- **J6** completes on S3
- S3 becomes `[48,48,48,48]`

Pending jobs:
- **J2**

### Retry J2

Feasible servers:
- **S3** → score = 256
- **S2** → Not possible
- **S1** → Not possible

After placement on S3:

`[48,48,48,48] -> [8,8,8,8]`

\[
4 \cdot 8^2 = 256
\]

So **J2 is placed on S3**.

**Allocation**
- `J2 -> S3, GPUs [0,1,2,3], start=6, end=13`

---

## Time = 7 : J3 Completes

At time 7:
- **J3** completes
- resources on S2 are partially freed

**S2 changes**
- from `[0,0,10,20,20,20,80,80]`
- to   `[20,20,10,20,20,20,80,80]`

No pending jobs remain.

---

## Time = 13 : J2 Completes

At time 13:
- **J2** completes
- S3 is fully restored to `[48,48,48,48]`

---

## Time = 14 : J7 Completes

At time 14:
- **J7** completes
- S2 becomes:

`[20,20,20,20,20,20,80,80]`

---

## Time = 15 : J5 Completes

At time 15:
- **J5** completes
- S1 becomes fully free again

`S1 = [80,80,80,80,80,80,80,80]`

---

## Time = 16 : J1 Completes

At time 16:
- **J1** completes
- S2 becomes fully free again

`S2 = [80,80,80,80,80,80,80,80]`

The simulation ends because:
- no active jobs remain
- no pending jobs remain

---

## Final Outcome

### Successfully executed
- J5
- J8
- J6
- J1
- J2
- J3
- J7

### Permanently unschedulable
- J4

### Final cluster state
- `S1 = [80,80,80,80,80,80,80,80]`
- `S2 = [80,80,80,80,80,80,80,80]`
- `S3 = [48,48,48,48]`

---


