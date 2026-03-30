from models.job import Job
from models.server import Server
from scheduler import Scheduler


# def print_result(title, result):
#     print(f"\n=== {title} ===")

#     print("\nAllocations:")
#     if result.allocations:
#         for job_id, alloc in result.allocations.items():
#             print(f"  {job_id} -> {alloc.server_id}, GPUs {alloc.gpu_indices}")
#     else:
#         print("  None")

#     print("\nPermanently unschedulable:")
#     if result.permanently_unschedulable:
#         for job_id, reason in result.permanently_unschedulable.items():
#             print(f"  {job_id}: {reason}")
#     else:
#         print("  None")

#     print("\nTemporarily unschedulable:")
#     if result.temporarily_unschedulable:
#         for job_id, reason in result.temporarily_unschedulable.items():
#             print(f"  {job_id}: {reason}")
#     else:
#         print("  None")


# def print_cluster_state(scheduler):
#     print("\nCluster state:")
#     for server_id, gpu_state in scheduler.get_cluster_state().items():
#         print(f"  {server_id}: {gpu_state}")


# def print_active_allocations(scheduler):
#     print("\nActive allocations:")
#     allocations = scheduler.get_allocations()
#     if allocations:
#         for job_id, alloc in allocations.items():
#             print(f"  {job_id} -> {alloc.server_id}, GPUs {alloc.gpu_indices}, mem/GPU={alloc.memory_per_gpu}")
#     else:
#         print("  None")

# def get_pending_jobs(self):
#     return dict(self.pending_jobs)


# def main():
#     servers = [
#         Server("S1", 8, 80),
#         Server("S2", 8, 80),
#         Server("S3", 4, 48),
#     ]

#     scheduler = Scheduler(servers)

#     jobs = [
#         Job("J1_large_training", 6, 60),
#         Job("J2_medium_training", 4, 40),
#         Job("J3_small_inference", 2, 20),
#         Job("J4_huge_job", 10, 20),      # permanently unschedulable
#         Job("J5_full_server", 8, 80),    # likely temporarily unschedulable after other jobs get placed
#         Job("J6_edge_fit", 4, 48),       # should fit only on S3 or untouched 80GB GPUs
#         Job("J7_tiny_job", 1, 10),
#     ]

#     result1 = scheduler.schedule_jobs(jobs)
#     print_result("Initial Scheduling", result1)
#     print_active_allocations(scheduler)
#     print_cluster_state(scheduler)

#     print("\n\n=== Completing J1_large_training ===")
#     result2 = scheduler.complete_job("J1_large_training")
#     print_result("After Completing J1_large_training", result2)
#     print_active_allocations(scheduler)
#     print_cluster_state(scheduler)

#     print("\n\n=== Completing J2_medium_training ===")
#     result3 = scheduler.complete_job("J2_medium_training")
#     print_result("After Completing J2_medium_training", result3)
#     print_active_allocations(scheduler)
#     print_cluster_state(scheduler)


# if __name__ == "__main__":
#     main()

import os

from models.job import Job
from models.server import Server
from scheduler import Scheduler


def is_time_enabled() -> bool:
    print(os.getenv("ENABLE_TIME"))
    return os.getenv("ENABLE_TIME", "false").strip().lower() == "true"


def print_result(title, result):
    print(f"\n=== {title} ===")

    print("\nAllocations:")
    if result.allocations:
        for job_id in sorted(result.allocations):
            alloc = result.allocations[job_id]
            timing = ""
            if alloc.start_time is not None or alloc.end_time is not None:
                timing = f", start={alloc.start_time}, end={alloc.end_time}"
            print(
                f"  {job_id} -> {alloc.server_id}, GPUs {alloc.gpu_indices}, "
                f"mem/GPU={alloc.memory_per_gpu}{timing}"
            )
    else:
        print("  None")

    print("\nPermanently unschedulable:")
    if result.permanently_unschedulable:
        for job_id in sorted(result.permanently_unschedulable):
            print(f"  {job_id}: {result.permanently_unschedulable[job_id]}")
    else:
        print("  None")

    print("\nTemporarily unschedulable:")
    if result.temporarily_unschedulable:
        for job_id in sorted(result.temporarily_unschedulable):
            print(f"  {job_id}: {result.temporarily_unschedulable[job_id]}")
    else:
        print("  None")


def print_cluster_state(scheduler: Scheduler):
    print("\nCluster state:")
    for server_id, gpu_state in sorted(scheduler.get_cluster_state().items()):
        print(f"  {server_id}: {gpu_state}")


def print_active_allocations(scheduler: Scheduler):
    print("\nActive allocations:")
    allocations = scheduler.get_allocations()
    if allocations:
        for job_id in sorted(allocations):
            alloc = allocations[job_id]
            timing = ""
            if alloc.start_time is not None or alloc.end_time is not None:
                timing = f", start={alloc.start_time}, end={alloc.end_time}"
            print(
                f"  {job_id} -> {alloc.server_id}, GPUs {alloc.gpu_indices}, "
                f"mem/GPU={alloc.memory_per_gpu}{timing}"
            )
    else:
        print("  None")


def print_pending_jobs(scheduler: Scheduler):
    print("\nPending jobs:")
    pending = scheduler.get_pending_jobs()
    if pending:
        for job_id in sorted(pending):
            job = pending[job_id]
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


def print_current_time(scheduler: Scheduler):
    if hasattr(scheduler, "get_current_time"):
        print(f"\nCurrent time: {scheduler.get_current_time()}")


def main():
    enable_time = is_time_enabled()
    print(f"ENABLE_TIME={enable_time}")

    servers = [
        Server("S1", 8, 80),
        Server("S2", 8, 80),
        Server("S3", 4, 48),
    ]

    scheduler = Scheduler(servers, enable_time=enable_time)

    jobs = [
        Job("J1_large_training", 6, 60, execution_time=12),
        Job("J2_medium_training", 4, 40, execution_time=7),
        Job("J3_small_inference", 2, 20, execution_time=3),
        Job("J4_huge_job", 10, 20, execution_time=5),   # permanently unschedulable
        Job("J5_full_server", 8, 80, execution_time=15),
        Job("J6_edge_fit", 4, 48, execution_time=6),
        Job("J7_tiny_job", 1, 10),                      # default execution time if time is enabled
        Job("J8_waiting_job", 8, 80, execution_time=4), # likely temporarily unschedulable initially
    ]

    result1 = scheduler.schedule_jobs(jobs)
    print_result("Initial Scheduling", result1)
    print_current_time(scheduler)
    print_active_allocations(scheduler)
    print_pending_jobs(scheduler)
    print_cluster_state(scheduler)

    if enable_time:
        print("\n=== Running time-based simulation until completion ===")
        scheduler.run_until_complete()

        print_current_time(scheduler)
        print_active_allocations(scheduler)
        print_pending_jobs(scheduler)
        print_cluster_state(scheduler)

    else:
        print("\n=== Manual completion flow ===")

        try:
            result2 = scheduler.complete_job("J5_full_server")
            print_result("After Completing J5_full_server", result2)
        except Exception as exc:
            print(f"Could not complete J5_full_server: {exc}")

        print_active_allocations(scheduler)
        print_pending_jobs(scheduler)
        print_cluster_state(scheduler)

        # Complete another job and retry again
        try:
            result3 = scheduler.complete_job("J1_large_training")
            print_result("After Completing J1_large_training", result3)
        except Exception as exc:
            print(f"Could not complete J1_large_training: {exc}")

        print_active_allocations(scheduler)
        print_pending_jobs(scheduler)
        print_cluster_state(scheduler)


if __name__ == "__main__":
    main()