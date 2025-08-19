from backend.core.logger import get_logger
from fastapi import APIRouter, HTTPException, Request

from backend.domains.system_schema import SystemSummary
from backend.utils.sys_util import get_system_info


logger = get_logger(__name__)

router = APIRouter()

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