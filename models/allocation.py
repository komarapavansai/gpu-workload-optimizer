# models/allocation.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Allocation:
    job_id: str
    server_id: str
    gpu_indices: List[int]
    memory_per_gpu: int

    start_time: Optional[int] = None
    end_time: Optional[int] = None