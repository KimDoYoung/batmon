import os
from pathlib import Path
from fastapi import HTTPException
from backend.core.config import config
from backend.core.logger import get_logger

logger = get_logger(__name__)

def files_tree(context):
    program_name = context.get("name", "unknown")
    program_config = config.get_program(program_name)
    if not program_config:
        raise HTTPException(status_code=404, detail="프로그램을 찾을 수 없습니다.")

    return {
        "title" : f"{program_name} 탐색",
        "program_name": program_name,
        "base_dir": program_config.get("base_dir", ""),
        "description": program_config.get("description", ""),
    }
def batmon_log(file_path):
    try:
        # full_path = os.path.join("c:\\batmon", file_path)
        full_path = file_path
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        file_type = "text"
    except UnicodeDecodeError:
        # UTF-8로 읽기 실패시 다른 인코딩 시도
        try:
            with open(full_path, 'r', encoding='cp949') as f:
                content = f.read()
            file_type = "text"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 인코딩 오류: {str(e)}")    
    return {
            "title" : "Batmon로그",
            "file_name": "batmon.log",
            "file_type": "text",
            "content": content,
            "program_name": "batmon",
            "file_path": file_path,
            "file_ext": ".log",
            "file_size": 0,
            "base_dir": "c:\\batmon"
    }
def files_view(context):
    """파일 보기 페이지용 컨텍스트 데이터를 생성합니다."""
    logger.info("files_view 컨텍스트 생성")
    # URL 파라미터에서 데이터 추출
    program_name = context.get("program_name", "unknown")
    file_path = context.get("file_path", "")

    # 시스템로그 보는 것 야매로
    if program_name == "batmon":
        return batmon_log(file_path)
    
    logger.debug(f"files_view: program_name={program_name}, file_path={file_path}")
    
    if not program_name or not file_path:
        raise HTTPException(status_code=400, detail="program_name과 file_path 파라미터가 필요합니다.")
    
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
            raise HTTPException(status_code=400, detail="디렉토리는 볼 수 없습니다.")
        
        # 파일 정보 추출
        file_ext = Path(full_path).suffix.lower()
        file_name = Path(full_path).name
        file_size = os.path.getsize(full_path)
        
        # 파일 내용 처리
        content = ""
        file_type = "unknown"
        
        if file_ext in ['.xls', '.xlsx']:
            # Excel 파일 처리
            logger.debug(f"Excel 파일 처리 시작: {full_path}")
            try:
                import pandas as pd
                logger.debug("pandas 임포트 성공")
                
                df = pd.read_excel(full_path, sheet_name=0)
                logger.debug(f"Excel 파일 읽기 성공: {df.shape} 크기")
                
                # HTML 테이블로 변환
                content = df.to_html(
                    classes='table table-striped table-hover table-sm',
                    escape=False,
                    table_id='excel-table'
                )
                file_type = "excel"
                logger.debug("Excel 파일을 HTML로 변환 완료")
            except ImportError as e:
                logger.error(f"pandas ImportError: {e}")
                raise HTTPException(status_code=500, detail="Excel 파일을 읽기 위한 pandas가 설치되지 않았습니다.")
            except Exception as e:
                logger.error(f"Excel 파일 읽기 실패: {e}")
                raise HTTPException(status_code=500, detail=f"Excel 파일 읽기 실패: {str(e)}")
        
        elif file_ext in ['.txt', '.log', '.bat', '.json', '.xml', '.html', '.htm', '.css', '.js', '.py', '.java', '.cpp', '.c', '.h', '.md', '.csv', '.ini', '.conf', '.cfg', '.yml', '.yaml']:
            # 텍스트 파일 처리
            try:
                # 파일 크기 확인 (10MB 제한)
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="파일이 너무 큽니다 (10MB 초과). 다운로드를 이용해주세요.")
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_type = "text"
            except UnicodeDecodeError:
                # UTF-8로 읽기 실패시 다른 인코딩 시도
                try:
                    with open(full_path, 'r', encoding='cp949') as f:
                        content = f.read()
                    file_type = "text"
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"파일 인코딩 오류: {str(e)}")
        
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
            # 이미지 파일 처리 - 스트리밍 엔드포인트 사용
            content = f"/api/v1/system/file/stream/{program_name}?file_path={file_path}"
            file_type = "image"
        
        elif file_ext == '.pdf':
            # PDF 파일 처리 - 스트리밍 엔드포인트 사용
            content = f"/api/v1/system/file/stream/{program_name}?file_path={file_path}"
            file_type = "pdf"
        
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {file_ext}")
        
        return {
            "title" : "파일보기",
            "file_name": file_name,
            "file_type": file_type,
            "content": content,
            "program_name": program_name,
            "file_path": file_path,
            "file_ext": file_ext[1:] if file_ext else "",  # . 제거
            "file_size": file_size,
            "base_dir": base_dir
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("파일 보기 컨텍스트 생성 실패: %s", e)
        raise HTTPException(status_code=500, detail=f"파일을 읽는 데 실패했습니다: {str(e)}")
