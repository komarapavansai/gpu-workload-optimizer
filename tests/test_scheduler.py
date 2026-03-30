from models.job import Job
from models.server import Server
from scheduler import Scheduler

def test_basic_allocation():
    servers = [Server("S1", 8, 80)]
    scheduler = Scheduler(servers)

    jobs = [Job("A", 2, 40)]

    result = scheduler.schedule_jobs(jobs)

    assert "A" in result.allocations

def test_basic_allocation():
    servers = [Server("S1", 8, 80)]
    scheduler = Scheduler(servers)

    jobs = [Job("A", 2, 40)]

    result = scheduler.schedule_jobs(jobs)

    assert "A" in result.allocations

def test_temporary_failure():
    servers = [Server("S1", 4, 80)]
    scheduler = Scheduler(servers)

    scheduler.schedule_jobs([Job("A", 4, 60)])
    result = scheduler.schedule_jobs([Job("B", 4, 40)])

    assert "B" in result.temporarily_unschedulable

def test_retry_after_completion():
    servers = [Server("S1", 4, 80)]
    scheduler = Scheduler(servers)

    scheduler.schedule_jobs([
        Job("A", 4, 60),
        Job("B", 4, 30)
    ])

    retry_result = scheduler.complete_job("A")

    assert "B" in retry_result.allocations