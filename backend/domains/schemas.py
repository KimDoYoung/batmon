# Response Schema
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    name: str
    description: str
    status: str  # "OK", "ERROR", "WARNING"
    message: str
    last_log: Optional[str] = None
    last_updated: Optional[datetime] = None
    base_dir: str
    scheduler: str
    run_time: List[str]

class HealthCheckResponse(BaseModel):
    timestamp: datetime
    overall_status: str  # "OK", "WARNING", "ERROR"
    services: List[ServiceStatus]
    summary: str
    total_services: int
    ok_count: int
    error_count: int
