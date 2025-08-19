from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OSInfo(BaseModel):
    system: str = Field(..., description="예: Windows")
    release: str = Field(..., description="예: 10")
    version: Optional[str] = Field(None, description="예: 10.0.26100")
    architecture: Optional[str] = Field(None, description="예: 64bit")
    hostname: str
    descriptions: str

class CPUInfo(BaseModel):
    processor: str
    physical_cores: Optional[int] = None
    logical_cores: Optional[int] = None
    usage_percent: Optional[float] = None

class MemoryInfo(BaseModel):
    total_gb: float
    used_gb: float
    available_gb: float
    used_percent: float

class DiskInfo(BaseModel):
    device: str = "C:\\"
    total_gb: float
    used_gb: float
    free_gb: float
    used_percent: float

class NetworkInfo(BaseModel):
    ip: str
    mac: str

class SystemStats(BaseModel):
    boot_time: datetime
    uptime_seconds: int
    uptime_human: str

class SystemSummary(BaseModel):
    os: OSInfo
    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo
    network: NetworkInfo
    stats: SystemStats
