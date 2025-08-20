# dir_util.py
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from backend.core.config import config  # Config 싱글톤: programs 파싱/캐시 제공

__all__ = [
    "is_hidden",
    "allowed_roots",
    "normalize_and_guard",
    "stat_safe",
    "dir_size",
    "fmt_mtime",
    "get_directory_info",
]

# -------------------------
# 기본 유틸
# -------------------------

def is_hidden(p: Path) -> bool:
    """윈도우/리눅스 공통 '숨김' 판단(윈도우 속성 + dotfile)."""
    try:
        if sys.platform.startswith("win"):
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
            if attrs != -1 and (attrs & FILE_ATTRIBUTE_HIDDEN):
                return True
        # dotfile
        return p.name.startswith(".")
    except Exception:
        return False


def stat_safe(entry: os.DirEntry):
    """symlink 무시하고 안전하게 stat."""
    try:
        return entry.stat(follow_symlinks=False)
    except Exception:
        return None


def dir_size(p: Path) -> int:
    """폴더 전체 용량(비용 큼). 필요 시에만 호출 권장."""
    total = 0
    for root, dirs, files in os.walk(p, followlinks=False):
        for fname in files:
            fpath = Path(root) / fname
            try:
                st = fpath.stat()
                total += getattr(st, "st_size", 0)
            except Exception:
                pass
    return total


def fmt_mtime(ts: float | None) -> str | None:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else None


# -------------------------
# 루트 가드 (BATMON.yml 기반)
# -------------------------

def allowed_roots() -> List[Path]:
    """
    BATMON.yml 의 programs[].base_dir 목록을 Path로 정규화하여 반환.
    config.list_programs()는 YAML 변경을 감지해 자동 재로딩함.
    """
    roots: List[Path] = []
    for prog in (config.list_programs() or []):  # YAML 변경 감지 후 최신값
        base = (prog or {}).get("base_dir")
        if not base:
            continue
        try:
            roots.append(Path(base).resolve(strict=False))
        except Exception:
            continue

    # 중복 제거 (Windows 대소문자/경로 구분 완화)
    seen = set()
    uniq: List[Path] = []
    for r in roots:
        key = str(r).casefold()
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def _is_subpath(child: Path, parent: Path) -> bool:
    """child 가 parent 하위 경로인지 안전 판정."""
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except Exception:
        return False


def normalize_and_guard(path: str) -> Path:
    """
    경로 정규화 + BATMON.yml 에 정의된 base_dir 들 중 하나의 하위만 허용.
    허용 루트 밖이면 PermissionError.
    """
    real = Path(path).resolve(strict=False)
    for root in allowed_roots():
        if real == root or _is_subpath(real, root):
            return real
    raise PermissionError(f"Access denied outside allowed roots: {real}")


# -------------------------
# 디렉터리 조회
# -------------------------

def get_directory_info(
    path: str,
    *,
    recursive: bool = False,
    max_depth: int = 1,
    include_hidden: bool = False,
    compute_size: bool = False,          # 파일/폴더 사이즈 계산
) -> Dict[str, Any]:
    """
    주어진 경로의 디렉토리/파일 정보를 반환.
    - recursive=True면 하위 폴더를 depth 제한(max_depth)까지 포함.
    - include_hidden=False면 숨김 항목 제외.
    - compute_size=True면 파일 size, 폴더 size(재귀) 계산.

    반환 스키마:
    {
      "path": "C:/auto_esafe/download",
      "is_dir": True,
      "size": 12345,         # 선택
      "folders": [ { name, path, is_dir, size?, mtime, children? }, ... ],
      "files":   [ { name, path, is_dir: False, ext, size?, mtime }, ... ]
    }
    """
    root = normalize_and_guard(path)
    info: Dict[str, Any] = {
        "path": str(root).replace("\\", "/"),
        "is_dir": True,
        "size": dir_size(root) if compute_size else None,
        "folders": [],
        "files": [],
    }

    try:
        with os.scandir(root) as it:
            for entry in it:
                try:
                    p = Path(entry.path)
                    if not include_hidden and is_hidden(p):
                        continue

                    st = stat_safe(entry)
                    mtime = fmt_mtime(getattr(st, "st_mtime", None)) if st else None

                    if entry.is_dir(follow_symlinks=False):
                        node: Dict[str, Any] = {
                            "name": entry.name,
                            "path": str(p).replace("\\", "/"),
                            "is_dir": True,
                            "mtime": mtime,
                            "size": (dir_size(p) if compute_size else None),
                        }
                        if recursive and max_depth > 1:
                            # 하위 폴더 재귀
                            child = get_directory_info(
                                str(p),
                                recursive=True,
                                max_depth=max_depth - 1,
                                include_hidden=include_hidden,
                                compute_size=compute_size,
                            )
                            node["children"] = {
                                "folders": child.get("folders", []),
                                "files": child.get("files", []),
                            }
                        info["folders"].append(node)

                    elif entry.is_file(follow_symlinks=False):
                        ext = p.suffix[1:].lower() if p.suffix else ""
                        size = getattr(st, "st_size", None) if (st and compute_size) else None
                        info["files"].append({
                            "name": entry.name,
                            "path": str(p).replace("\\", "/"),
                            "is_dir": False,
                            "ext": ext,
                            "size": size,
                            "mtime": mtime,
                        })

                    else:
                        # 기타(심볼릭 링크, 소켓 등)는 스킵
                        continue

                except Exception:
                    # 개별 항목 오류는 무시하고 계속
                    continue

        # 보기 좋게 정렬(자연정렬/한글은 클라 정렬로 처리하므로 여기선 기본 정렬)
        info["folders"].sort(key=lambda x: (x["name"] or "").lower())
        info["files"].sort(key=lambda x: (x["name"] or "").lower())

    except Exception as e:
        # 전체 디렉토리 접근 예외
        info["error"] = str(e)

    return info

if __name__ == "__main__":
    dir_info = get_directory_info("C:/auto_esafe", recursive=False, max_depth=2, include_hidden=False, compute_size=True)
    print(dir_info)