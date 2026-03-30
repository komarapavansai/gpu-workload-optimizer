from typing import List, Optional
from models.job import Job
from models.allocation import Allocation
from models.exceptions import AllocationError

class Server:
    def __init__(self, server_id: str, num_gpus: int, memory_per_gpu: int):
        if not server_id:
            raise ValueError("server_id must be non-empty")
        if num_gpus <= 0:
            raise ValueError(f"Server {server_id}: num_gpus must be > 0")
        if memory_per_gpu <= 0:
            raise ValueError(f"Server {server_id}: memory_per_gpu must be > 0")

        self.server_id = server_id
        self.num_gpus = num_gpus
        self.memory_per_gpu = memory_per_gpu
        self.gpu_free_memory = [memory_per_gpu] * num_gpus

    def can_fit(self, job: Job):
        eligible = [
            (free_mem, idx)
            for idx, free_mem in enumerate(self.gpu_free_memory)
            if free_mem >= job.memory_per_gpu
        ]

        if len(eligible) < job.gpu_count:
            return None

        eligible.sort()
        chosen = [idx for _, idx in eligible[:job.gpu_count]]
        return chosen

    def allocate(self, job: Job, gpu_indices: List[int]):
        for idx in gpu_indices:
            if self.gpu_free_memory[idx] < job.memory_per_gpu:
                raise AllocationError(
                    f"Server {self.server_id}: GPU {idx} does not have enough memory"
                )

        for idx in gpu_indices:
            self.gpu_free_memory[idx] -= job.memory_per_gpu

        return Allocation(
            job_id=job.job_id,
            server_id=self.server_id,
            gpu_indices=gpu_indices,
            memory_per_gpu=job.memory_per_gpu,
        )

    def free(self, allocation: Allocation):
        for idx in allocation.gpu_indices:
            new_value = self.gpu_free_memory[idx] + allocation.memory_per_gpu

            if new_value > self.memory_per_gpu:
                raise AllocationError(
                    f"Server {self.server_id}: freeing exceeds GPU capacity on GPU {idx}"
                )

            self.gpu_free_memory[idx] = new_value

    def score_after_allocation(self, job: Job, gpu_indices: List[int]):
        remaining = self.gpu_free_memory[:]
        for idx in gpu_indices:
            remaining[idx] -= job.memory_per_gpu
        return sum(mem * mem for mem in remaining)

    def __repr__(self):
        return f"{self.server_id}: {self.gpu_free_memory}"