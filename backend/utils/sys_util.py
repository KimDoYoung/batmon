import os
from backend.core.logger import get_logger
import platform, socket, uuid, psutil, datetime
from typing import Iterable
from datetime import datetime, timedelta, timezone

from backend.domains.system_schema import CPUInfo, DiskInfo, MemoryInfo, NetworkInfo, OSInfo, SystemStats, SystemSummary

logger = get_logger(__name__)

# 앞서 정의한 모델이 같은 모듈/패키지에 있다고 가정
# from .models import OSInfo, CPUInfo, MemoryInfo, DiskInfo, NetworkInfo, SystemStats, SystemSummary

try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except Exception:
    KST = timezone(timedelta(hours=9))

def _bytes_to_gb(n: int) -> float:
    return round(n / (1024 ** 3), 2)

def _humanize_tdelta(seconds: int) -> str:
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return (f"{d} day, {h}:{m:02d}:{s:02d}" if d == 1
            else f"{d} days, {h}:{m:02d}:{s:02d}" if d > 1
            else f"{h}:{m:02d}:{s:02d}")

def _get_primary_ip() -> str:
    # 더 안정적인 로컬 IP 취득 (게이트웨이로 UDP connect)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "0.0.0.0"

def _get_mac() -> str:
    node = uuid.getnode()
    return ":".join(f"{(node >> i) & 0xff:02x}" for i in range(40, -1, -8))

def get_system_info() -> "SystemSummary":
    # ---- OS / Host ----
    system = platform.system()                      # e.g., 'Windows'
    release = platform.release()                    # e.g., '10' or '11'
    version = platform.version()                    # e.g., '10.0.26100'
    architecture = platform.architecture()[0]       # e.g., '64bit'
    hostname = socket.gethostname()

    os_info = OSInfo(
        system=system,
        release=release,
        version=version,
        architecture=architecture,
        hostname=hostname,
        descriptions = f"{system} {release} {version} ({architecture})",
    )

    # ---- Network ----
    ip = _get_primary_ip()
    mac = _get_mac()
    net_info = NetworkInfo(ip=ip, mac=mac)

    # ---- CPU ----
    cpu_info = CPUInfo(
        processor=platform.processor(),
        physical_cores=psutil.cpu_count(logical=False) or None,
        logical_cores=psutil.cpu_count(logical=True) or None,
        usage_percent=float(psutil.cpu_percent(interval=1)),
    )

    # ---- Memory ----
    mem = psutil.virtual_memory()
    mem_total_gb = _bytes_to_gb(mem.total)
    mem_used_gb = _bytes_to_gb(mem.used)
    mem_avail_gb = _bytes_to_gb(mem.available)
    mem_used_pct = round((mem.used / mem.total) * 100, 1) if mem.total else 0.0

    mem_info = MemoryInfo(
        total_gb=mem_total_gb,
        used_gb=mem_used_gb,
        available_gb=mem_avail_gb,
        used_percent=mem_used_pct,
    )

    # ---- Disk (시스템 드라이브 기준) ----
    system_drive = os.getenv("SystemDrive", "C:") + "\\"
    d = psutil.disk_usage(system_drive)
    disk_total_gb = _bytes_to_gb(d.total)
    disk_free_gb = _bytes_to_gb(d.free)
    disk_used_gb = _bytes_to_gb(d.used)
    disk_used_pct = round(d.percent, 1)

    disk_info = DiskInfo(
        device=system_drive,
        total_gb=disk_total_gb,
        used_gb=disk_used_gb,
        free_gb=disk_free_gb,
        used_percent=disk_used_pct,
    )

    # ---- Stats (부팅/업타임) ----
    boot_dt1 = datetime.fromtimestamp(psutil.boot_time(), tz=KST)
    now = datetime.now(KST)
    uptime_seconds = max(0, int((now - boot_dt1).total_seconds()))
    # boot_dt = boot_dt1.strftime("%Y-%m-%d %H:%M:%S %Z")

    stats = SystemStats(
        boot_time=boot_dt1,
        uptime_seconds=uptime_seconds,
        uptime_human=_humanize_tdelta(uptime_seconds),
    )

    # ---- Summary ----
    summary = SystemSummary(
        os=os_info,
        cpu=cpu_info,
        memory=mem_info,
        disk=disk_info,
        network=net_info,
        stats=stats,
    )

    return summary


def format_bytes(n: int) -> str:
    # 사람이 읽기 쉬운 단위
    for unit in ['B','KB','MB','GB','TB','PB']:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} EB"
    
def dir_size(path: str,
             exclude_globs: Iterable[str] = (),
             follow_symlinks: bool = False,
             skip_reparse: bool = True) -> int:
    """
    path 아래 모든 파일 용량(st_size)을 합산.
    - exclude_globs: ['*.tmp','*.log'] 같이 제외 패턴
    - follow_symlinks: 심볼릭 링크/정션 따라갈지 여부
    - skip_reparse: 윈도우 reparse point(정션) 건너뛰기
    """
    import fnmatch
    total = 0

    try:
        with os.scandir(path) as it:
            for entry in it:
                # 제외 패턴
                if any(fnmatch.fnmatch(entry.name, pat) for pat in exclude_globs):
                    continue

                try:
                    if entry.is_symlink():
                        if not follow_symlinks:
                            continue

                    if entry.is_file(follow_symlinks=follow_symlinks):
                        # stat 한 번만 호출 (성능)
                        total += entry.stat(follow_symlinks=follow_symlinks).st_size
                    elif entry.is_dir(follow_symlinks=follow_symlinks):
                        # 윈도우 reparse point(정션) 회피 (중복/순환 방지)
                        if skip_reparse:
                            try:
                                # Windows에서 reparse point 감지
                                st = entry.stat(follow_symlinks=False)
                                # 0x400 == FILE_ATTRIBUTE_REPARSE_POINT
                                if getattr(st, "st_file_attributes", 0) & 0x400:
                                    continue
                            except Exception:
                                pass
                        total += dir_size(entry.path, exclude_globs, follow_symlinks, skip_reparse)
                except (PermissionError, FileNotFoundError):
                    # 권한/경합 문제는 건너뛰기
                    continue
    except (NotADirectoryError, FileNotFoundError):
        return 0

    return total

def get_directory_info(path:str) -> dict:
    """
    주어진 경로의 디렉토리 및 파일 정보를 반환합니다.
    """
    info = {
        "path": path,
        "size": dir_size(path),
        "files": [],
        "folders": [],
    }

    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    info["files"].append(entry.name)
                elif entry.is_dir():
                    info["folders"].append(entry.name)
    except Exception as e:
        logger.exception("디렉토리 정보 조회 실패: %s", e)

    return info

if __name__ == "__main__":
    # from pprint import pprint
    # pprint(get_system_info())
    dir_info = get_directory_info("c:/auto_esafe/log")
    logger.info("디렉토리 정보: %s", dir_info)