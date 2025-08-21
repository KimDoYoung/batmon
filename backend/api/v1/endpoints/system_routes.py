import mimetypes
import os
from pathlib import Path

from fastapi.responses import FileResponse, StreamingResponse
from backend.core.config import config
from backend.core.logger import get_logger
from fastapi import APIRouter, HTTPException, Request

from backend.domains.system_schema import SystemSummary
from backend.utils.dir_util import get_directory_info
from backend.utils.sys_util import get_system_info


logger = get_logger(__name__)

router = APIRouter()

@router.get("/time",  include_in_schema=True)
def time(request: Request):

    """
    서버의 시간을 리턴합니다.
    """
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content =  {"time": now}
    return content

@router.get("/info", response_model=SystemSummary, include_in_schema=True)
def info(request: Request):
    """
    시스템 정보를 반환합니다.
    """
    logger.info("시스템 정보 요청")
    try:
        summary = get_system_info()  # 반드시 SystemSummary 인스턴스를 반환하도록 구현
    except Exception as e:
        logger.exception("시스템 정보 조회 실패: %s", e)
        # JSON으로 {"detail": "..."} 형식 반환
        raise HTTPException(status_code=500, detail="시스템 정보를 가져오는 데 실패했습니다.")

    if summary is None:
        raise HTTPException(status_code=500, detail="시스템 정보가 비어 있습니다.")

    return summary  # OK: 200 + JSON (SystemSummary 직렬화)

@router.get("/dir/{name}", include_in_schema=True)
def get_dirs(name: str, subpath: str = "", request: Request = None):
    """ name에 해당하는 디렉토리의 하위 디렉토리 목록을 반환합니다. """
    logger.info("디렉토리 정보 요청: %s, subpath: %s", name, subpath)
    try:
        # config에서 프로그램 정보 가져오기
        program_config = config.get_program(name)
        if not program_config:
            raise HTTPException(status_code=404, detail=f"프로그램 '{name}'을 찾을 수 없습니다.")
        
        base_dir = program_config.get('base_dir', '')
        if not base_dir:
            raise HTTPException(status_code=400, detail=f"프로그램 '{name}'의 base_dir이 설정되지 않았습니다.")
        
        # 경로 조합
        if subpath:
            path = os.path.join(base_dir, subpath)
        else:
            path = base_dir
            
        # 경로 존재 여부 확인
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"경로를 찾을 수 없습니다: {path}")
        
        # 디렉토리 정보 가져오기
        dir_info = get_directory_info(
            path, 
            recursive=False, 
            max_depth=3, 
            include_hidden=True, 
            compute_size=True
        )

    except HTTPException:
        # HTTPException은 그대로 re-raise
        raise
    except PermissionError as e:
        logger.warning("권한 오류: %s", e)
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    except Exception as e:
        logger.exception("디렉토리 정보 조회 실패: %s", e)
        raise HTTPException(status_code=500, detail="디렉토리 정보를 가져오는 데 실패했습니다.")

    return dir_info  # OK: 200 + JSON (디렉토리 정보 직렬화)

   

@router.get("/download/{program_name}", include_in_schema=True)
def file_download(program_name: str, file_path: str, request: Request):
    """ 파일을 다운로드합니다. """
    logger.info("파일 다운로드 요청: program=%s, path=%s", program_name, file_path)
    
    try:
        if program_name == "batmon":
            file_name = "batmon.log"
            return FileResponse(
                path=file_path,
                filename=file_name,
                media_type='text/plain'
            )
        # 프로그램 설정 가져오기
        program_config = config.get_program(program_name)
        if not program_config:
            raise HTTPException(status_code=404, detail=f"프로그램 '{program_name}'을 찾을 수 없습니다.")
        
        base_dir = program_config.get('base_dir', '')
        if not base_dir:
            raise HTTPException(status_code=400, detail=f"프로그램 '{program_name}'의 base_dir이 설정되지 않았습니다.")
        
        # 전체 파일 경로 구성
        full_path = os.path.join(base_dir, file_path)
        
        # 파일 존재 여부 확인
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")
        
        if not os.path.isfile(full_path):
            raise HTTPException(status_code=400, detail="디렉토리는 다운로드할 수 없습니다.")
        
        # MIME 타입 결정
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        return FileResponse(
            path=full_path,
            filename=Path(full_path).name,
            media_type=mime_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("파일 다운로드 실패: %s", e)
        raise HTTPException(status_code=500, detail=f"파일 다운로드에 실패했습니다: {str(e)}")

@router.get("/file/stream/{program_name}", include_in_schema=True)
def stream_file(program_name: str, file_path: str, request: Request):
    """ 파일을 스트림으로 서빙합니다 (이미지, PDF 등 브라우저에서 직접 표시용). """
    logger.info("파일 스트림 요청: program=%s, file_path=%s", program_name, file_path)
    
    try:
        # 프로그램 설정 가져오기
        program_config = config.get_program(program_name)
        if not program_config:
            raise HTTPException(status_code=404, detail=f"프로그램 '{program_name}'을 찾을 수 없습니다.")
        
        base_dir = program_config.get('base_dir', '')
        if not base_dir:
            raise HTTPException(status_code=400, detail=f"프로그램 '{program_name}'의 base_dir이 설정되지 않았습니다.")
        
        # 전체 파일 경로 구성
        full_path = os.path.join(base_dir, file_path)
        
        # 파일 존재 여부 확인
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")
        
        if not os.path.isfile(full_path):
            raise HTTPException(status_code=400, detail="디렉토리는 스트리밍할 수 없습니다.")
        
        # MIME 타입 결정
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # 파일 스트리밍
        def iterfile():
            with open(full_path, "rb") as file_like:
                yield from file_like
        
        return StreamingResponse(
            iterfile(),
            media_type=mime_type,
            headers={
                "Content-Disposition": "inline",  # 브라우저에서 직접 표시
                "Cache-Control": "public, max-age=3600"  # 1시간 캐시
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("파일 스트리밍 실패: %s", e)
        raise HTTPException(status_code=500, detail=f"파일 스트리밍에 실패했습니다: {str(e)}")
