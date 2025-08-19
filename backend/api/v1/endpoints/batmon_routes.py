import datetime

from backend.core.logger import get_logger
from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
from backend.domains.batmon_schema import HealthCheckResponse
from backend.domains.services.auto_esafe import AutoEsafeService
from backend.domains.services.fund_mail_service import FundMailService
from backend.domains.services.kindscrap_service import KindscrapService
from backend.core.config import config 

logger = get_logger(__name__)

KST = timezone(timedelta(hours=9))

router = APIRouter()
@router.get("/check", response_model=HealthCheckResponse, include_in_schema=True)
def check():
    ''' 3개의 프로그램에 대해서 현재의 상황을 리포트한다. '''
    programs = config.list_programs()
    services = []
    
    for program in programs:
        if program["name"] == "auto_esafe":
            autoesafe = AutoEsafeService("auto_esafe")
            service = autoesafe.check()
        elif program["name"] == "kindscrap":
            kindscrap = KindscrapService("kindscrap")
            service = kindscrap.check()
        elif program["name"] == "fund_mail":
            fund_mail = FundMailService("fund_mail")
            service = fund_mail.check()
        else:
            raise ValueError("Unknown program")
        services.append(service)
    
    # 전체 상태 집계
    ok_count = sum(1 for service in services if service.status == "OK")
    error_count = sum(1 for service in services if service.status == "ERROR")
    total_services = len(services)
    
    # 전체 상태 판단
    if error_count > 0:
        overall_status = "ERROR"
        summary = f"{error_count}개의 서비스에서 오류가 발생했습니다."
    else:
        overall_status = "OK"
        summary = "모든 서비스가 정상적으로 동작 중입니다."
    
    return HealthCheckResponse(
        timestamp=datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        overall_status=overall_status,
        services=services,
        summary=summary,
        total_services=total_services,
        ok_count=ok_count,
        error_count=error_count
    )