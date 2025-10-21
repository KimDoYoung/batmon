"""
모듈 설명: 
    - /, /main
    - /main: 메인 페이지
    - /page: path에 해당하는 페이지를 가져와서 보낸다.

작성자: 김도영
작성일: 2025-07-21
버전: 1.0
"""
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.core.config import config
from backend.core.logger import get_logger
from backend.core.template_engine import render_template
from backend.domains.page_contexts.context_registry import PAGE_CONTEXT_PROVIDERS

logger = get_logger(__name__)

router = APIRouter()

def get_today():
    from datetime import datetime
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.now()
    weekday_str = weekdays[today.weekday()]
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f" ({weekday_str})"

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def display_root(request: Request):
    ''' 메인 '''
    return RedirectResponse(url="/main")


@router.get("/main", response_class=HTMLResponse, include_in_schema=False)
async def display_main(request: Request):
    ''' 메인 '''
    logger.debug("메인 페이지 요청됨")
    version = config.VERSION    
    context = { "request": request,  
                "path": '/main',
                "_version": version,
                "data": {
                    "title": "Dashboard",
                }
    }    
    return render_template("main.html", context)

@router.get("/page", response_class=HTMLResponse, include_in_schema=False)
async def page(
    request: Request, 
    path: str = Query(..., description="template폴더안의 html path")
):
    ''' path에 해당하는 페이지를 가져와서 보낸다. '''
    
    extra_params = {k: v for k, v in request.query_params.items()}

    
    page_page = path.lstrip('/')
    page_path = page_page if page_page else "main"
    version = config.VERSION
    logger.debug(f"VERSION: {version}")
    logger.debug(f"page 함수 호출: path={path}, page_path={page_path}")
    logger.debug(f"query_params: {dict(request.query_params)}")
    
    context = { 
                "_version": version,
                "request": request,  
                "page_path": page_path,
                **extra_params
            }

    func = PAGE_CONTEXT_PROVIDERS.get(page_path)
    if func:
        try:
            # 함수가 async인지 확인
            is_async = callable(func) and func.__code__.co_flags & 0x80
            
            # 함수가 매개변수를 받는지 확인
            func_params = func.__code__.co_argcount if callable(func) else 0
            
            if func_params > 0:
                # context를 매개변수로 전달
                data = await func(context) if is_async else func(context)
            else:
                # 매개변수가 없는 기존 함수 호환성 유지
                data = await func() if is_async else func()
                
            context["data"] = data
        except Exception as e:
            logger.error(f"{path}용 데이터 로딩 실패: {e}")
    else:
        data = {"title":"배치프로그램 모니터링"}
        context["data"] = data
    template_page = f"template/{path.lstrip('/')}.html"
    logger.debug(f"template_page 호출됨: {template_page}")
    return render_template(template_page, context)    