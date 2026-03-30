# models/job.py
from dataclasses import dataclass
from typing import Optional
from models.exceptions import ValidationError


@dataclass
class Job:
    job_id: str
    gpu_count: int
    memory_per_gpu: int
    execution_time: Optional[int] = None

    def validate(self):
        if not self.job_id:
            raise ValidationError("job_id must be non-empty")
        if self.gpu_count <= 0:
            raise ValidationError(f"{self.job_id}: gpu_count must be > 0")
        if self.memory_per_gpu <= 0:
            raise ValidationError(f"{self.job_id}: memory_per_gpu must be > 0")

        # Only validate execution_time is enabled
        if self.execution_time is not None and self.execution_time <= 0:
            raise ValidationError(f"{self.job_id}: execution_time must be > 0")