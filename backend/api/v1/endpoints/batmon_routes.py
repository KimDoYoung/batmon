from backend.core.logger import get_logger
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = get_logger(__name__)

router = APIRouter()

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def check(request: Request):
    ''' 3개의 프로그램에 대해서 현재의 상황을 리포트한다. '''
    # auto_esafe는 base_dir + /log 밑에서  auto_esafe_오늘yyyy_mm_dd.log를 찾아서 있