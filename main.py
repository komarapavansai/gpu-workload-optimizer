import sys

from models.job import Job
from models.server import Server
from scheduler import Scheduler

sys.stdout = open("output.txt", "w")

def parse_bool(value):
    return value.strip().lower() == "true"


def load_input(file_path):
    enable_time = False
    servers = []
    jobs = []
    section = None

    with open(file_path, "r") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("ENABLE_TIME"):
                parts = line.split("=", 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid ENABLE_TIME line: {line}")
                enable_time = parse_bool(parts[1])

            elif line == "SERVERS":
                section = "SERVERS"

            elif line == "JOBS":
                section = "JOBS"

            else:
                parts = line.split()

                if section == "SERVERS":
                    if len(parts) != 3:
                        raise ValueError(f"Invalid server line: {line}")

                    sid, gpus, memory = parts
                    servers.append(Server(sid, int(gpus), int(memory)))

                elif section == "JOBS":
                    if len(parts) == 4:
                        jid, gpu_req, mem_req, exec_time = parts
                        execution_time = int(exec_time)
                    elif len(parts) == 3:
                        jid, gpu_req, mem_req = parts
                        execution_time = None
                    else:
                        raise ValueError(f"Invalid job line: {line}")

                    jobs.append(
                        Job(
                            jid,
                            int(gpu_req),
                            int(mem_req),
                            execution_time=execution_time,
                        )
                    )
                else:
                    raise ValueError(f"Line outside SERVERS/JOBS section: {line}")

    return enable_time, servers, jobs


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


def main():

    filename = sys.argv[1] if len(sys.argv) > 1 else "input1.txt"
    input_file = "inputs/" + filename

    enable_time, servers, jobs = load_input(input_file)

    print(f"ENABLE_TIME={enable_time}")

    scheduler = Scheduler(servers, enable_time=enable_time)

    result1 = scheduler.schedule_jobs(jobs)
    print_result("Initial Scheduling", result1)

    if enable_time:
        print("\n=== Running time-based simulation until completion ===")
        scheduler.run_until_complete()
    else:
        print("\n=== Manual completion flow ===")

        # Example manual completions (optional, safe to remove if not needed)
        for job_id in list(scheduler.get_allocations().keys())[:2]:
            try:
                result = scheduler.complete_job(job_id)
                print_result(f"After Completing {job_id}", result)
            except Exception as exc:
                print(f"Could not complete {job_id}: {exc}")


if __name__ == "__main__":
    main()