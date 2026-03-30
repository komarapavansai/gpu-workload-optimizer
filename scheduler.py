from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

from models.job import Job
from models.server import Server
from models.allocation import Allocation
from models.exceptions import DuplicateJobError

@dataclass
class ScheduleResult:
    allocations: Dict[str, Allocation] = field(default_factory=dict)
    permanently_unschedulable: Dict[str, str] = field(default_factory=dict)
    temporarily_unschedulable: Dict[str, str] = field(default_factory=dict)

DEFAULT_EXECUTION_TIME = 10

class Scheduler:
    def __init__(self, servers, enable_time: bool = False):
        if not servers:
            raise ValueError("servers list cannot be empty")

        self.servers = servers
        self.allocations_by_job = {}
        self.pending_jobs = {}

        self.enable_time = enable_time
        self.current_time = 0

    def can_ever_fit(self, job: Job):
        for server in self.servers:
            if server.num_gpus >= job.gpu_count and server.memory_per_gpu >= job.memory_per_gpu:
                return True, ""
        return (
            False,
            f"requires {job.gpu_count} GPUs with {job.memory_per_gpu}GB each, "
            "but no server can provide that"
        )

    def _find_best_server(self, job: Job):
        best_server = None
        best_gpu_indices = None
        best_score = float("inf")

        for server in self.servers:
            gpu_indices = server.can_fit(job)
            if gpu_indices is None:
                continue

            score = server.score_after_allocation(job, gpu_indices)
            if score < best_score or (score == best_score and server.server_id < best_server.server_id):
                best_score = score
                best_server = server
                best_gpu_indices = gpu_indices

        return best_server, best_gpu_indices

    def schedule_jobs(self, jobs: List[Job]):
        for job in jobs:
            if job.job_id in self.allocations_by_job or job.job_id in self.pending_jobs:
                raise DuplicateJobError(f"Duplicate job_id: {job.job_id}")
            job.validate()

        ordered_jobs = sorted(
            jobs,
            key=lambda j: (j.gpu_count * j.memory_per_gpu, j.memory_per_gpu, j.gpu_count),
            reverse=True
        )

        result = ScheduleResult()

        for job in ordered_jobs:
            if job.job_id in self.allocations_by_job or job.job_id in self.pending_jobs:
                raise ValueError(f"Duplicate job_id detected: {job.job_id}")

            fits_ever, reason = self.can_ever_fit(job)
            if not fits_ever:
                result.permanently_unschedulable[job.job_id] = reason
                continue

            best_server, best_gpu_indices = self._find_best_server(job)

            if best_server is None:
                self.pending_jobs[job.job_id] = job
                result.temporarily_unschedulable[job.job_id] = (
                    "job could fit on the cluster in theory, but not with current free resources"
                )
            else:
                allocation = best_server.allocate(job, best_gpu_indices)

                if self.enable_time:
                    exec_time = job.execution_time if job.execution_time is not None else DEFAULT_EXECUTION_TIME

                    allocation.start_time = self.current_time
                    allocation.end_time = self.current_time + exec_time

                self.allocations_by_job[job.job_id] = allocation
                result.allocations[job.job_id] = allocation

        return result

    def complete_job(self, job_id: str):
        if job_id not in self.allocations_by_job:
            raise ValueError(f"Job {job_id} is not currently allocated")

        self._complete_job_internal(job_id)
        return self._retry_pending_jobs()

    def get_cluster_state(self):
        return {server.server_id: server.gpu_free_memory[:] for server in self.servers}

    def get_allocations(self):
        return dict(self.allocations_by_job)

    def get_pending_jobs(self):
        return dict(self.pending_jobs)
    
    def advance_time(self, delta: int):
        if not self.enable_time:
            raise RuntimeError("Time simulation is disabled")

        if delta < 0:
            raise ValueError("delta must be non-negative")

        previous_time = self.current_time
        self.current_time += delta

        finished_jobs = []

        # Finding the jobs that should finish
        for job_id, alloc in self.allocations_by_job.items():
            if alloc.end_time is not None and alloc.end_time <= self.current_time:
                finished_jobs.append(job_id)

        for job_id in finished_jobs:
            self._complete_job_internal(job_id)

        # Re-try pending jobs
        if finished_jobs:
            self._retry_pending_jobs()
        
        self.print_status(title="Scheduler Status", previous_time=previous_time, finished_jobs=finished_jobs)

    def _complete_job_internal(self, job_id: str):
        allocation = self.allocations_by_job.pop(job_id)

        target_server = None
        for server in self.servers:
            if server.server_id == allocation.server_id:
                target_server = server
                break

        if target_server is None:
            raise ValueError(f"Server {allocation.server_id} not found")

        target_server.free(allocation)

    def _retry_pending_jobs(self):
        pending_jobs_to_retry = list(self.pending_jobs.values())
        self.pending_jobs.clear()
        return self.schedule_jobs(pending_jobs_to_retry)

    def run_until_complete(self):
        if not self.enable_time:
            raise RuntimeError("Time simulation is disabled")

        self.print_status(title="Initial Status")

        while True:
            if not self.allocations_by_job and not self.pending_jobs:
                print("\n=== Simulation Complete ===")
                self.print_status()
                break

            # Find next completion time
            future_end_times = [
                alloc.end_time
                for alloc in self.allocations_by_job.values()
                if alloc.end_time is not None
            ]

            if not future_end_times:
                print("No further progress possible (no timed jobs)")
                self.print_status(title="Stuck State")
                break

            next_time = min(future_end_times)

            delta = next_time - self.current_time
            self.advance_time(delta)

    def get_current_time(self):
        return self.current_time

    def print_status(
        self,
        title: str = "",
        previous_time: int | None = None,
        finished_jobs: list[str] | None = None):
        if title:
            print(f"\n=== {title} ===")

        if previous_time is not None:
            print(f"Time advanced from {previous_time} to {self.current_time} (delta={self.current_time - previous_time})")
        else:
            print(f"Current time: {self.current_time}")

        if finished_jobs:
            print("Finished jobs:")
            for job_id in finished_jobs:
                print(f"  {job_id}")
        else:
            print("Finished jobs: None")

        print("\nActive allocations:")
        if self.allocations_by_job:
            for job_id in sorted(self.allocations_by_job):
                alloc = self.allocations_by_job[job_id]
                timing = ""
                if alloc.start_time is not None or alloc.end_time is not None:
                    timing = f", start={alloc.start_time}, end={alloc.end_time}"
                print(
                    f"  {job_id} -> {alloc.server_id}, GPUs {alloc.gpu_indices}, "
                    f"mem/GPU={alloc.memory_per_gpu}{timing}"
                )
        else:
            print("  None")

        print("\nPending jobs:")
        if self.pending_jobs:
            for job_id in sorted(self.pending_jobs):
                job = self.pending_jobs[job_id]
                exec_info = (
                    f", execution_time={job.execution_time}"
                    if job.execution_time is not None
                    else ""
                )
                print(
                    f"  {job.job_id}: GPUs={job.gpu_count}, "
                    f"mem/GPU={job.memory_per_gpu}{exec_info}"
                )
        else:
            print("  None")

        print("\nCluster state:")
        for server in self.servers:
            print(f"  {server.server_id}: {server.gpu_free_memory}")