import os
import platform, socket, uuid, psutil, datetime
from typing import Iterable

def get_system_info():
    info = {}
    # OS / Host
    info["os"] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info["hostname"] = socket.gethostname()
    
    # Network
    info["ip_address"] = socket.gethostbyname(socket.gethostname())
    info["mac_address"] = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                                    for i in range(0, 8*6, 8)][::-1])
    
    # CPU / Memory
    info["cpu"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=True)
    info["cpu_usage"] = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    info["memory_total"] = f"{mem.total // (1024**3)} GB"
    info["memory_used"] = f"{mem.used // (1024**3)} GB"
    
    # Disk
    disk = psutil.disk_usage("C:\\")
    info["disk_total"] = f"{disk.total // (1024**3)} GB"
    info["disk_free"] = f"{disk.free // (1024**3)} GB"
    
    # Boot
    info["boot_time"] = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    
    return info


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

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_system_info())
