class SchedulerError(Exception):
    pass


class ValidationError(SchedulerError):
    pass


class AllocationError(SchedulerError):
    pass


class JobNotFoundError(SchedulerError):
    pass


class DuplicateJobError(SchedulerError):
    pass