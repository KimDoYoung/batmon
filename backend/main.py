import os
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.v1.endpoints.batmon_routes import router as batmon_router
from backend.api.v1.endpoints.home_routes import router as home_router
from backend.api.v1.endpoints.system_routes import router as system_router
from backend.core.batmon_db import (
    create_batmon_db,  # Add this import (adjust path if needed)
)
from backend.core.config import config
from backend.core.exception_handler import add_exception_handlers
from backend.core.logger import get_logger

logger = get_logger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="Batmon - 배치프로그램 모니터링", version="0.0.1")
    add_routes(app)
    add_event_handlers(app)
    add_static_files(app)
    add_exception_handlers(app)
    return app


def add_routes(app: FastAPI):
    # API 라우터 포함
    app.include_router(home_router) # 화면
    app.include_router(batmon_router, prefix="/api/v1/batmon", tags=["batmon"])
    app.include_router(system_router, prefix="/api/v1/system", tags=["system"])

def add_event_handlers(app: FastAPI):
    ''' 이벤트 핸들러 설정 '''
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)

def add_static_files(app: FastAPI):
    ''' 정적 파일 설정, pyinstaller 패키징 고려 '''
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        static_files_path = os.path.join(sys._MEIPASS, 'frontend', 'public')
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_files_path = os.path.join(BASE_DIR, 'frontend', 'public')

    app.mount("/public", StaticFiles(directory=static_files_path), name="public")

async def startup_event():
    ''' Batmon application  시작 '''
    logger.info('---------------------------------')
    logger.info('▶️  Startup 프로세스 시작')
    logger.info('---------------------------------')

    b = config.reload_yaml(force=True)
    if b:
        logger.info(f"BATMON.yml 파일을 다시 로딩했습니다: {config.YAML_PATH} (프로그램 수: {len(config.programs)})")
    else:
        logger.error(f"BATMON.yml 파일이 존재하지 않거나 변경되지 않았습니다: {config.YAML_PATH}")

    db_path = config.DB_PATH 
    parent_dir = os.path.dirname(db_path)
    # sqlite3데이터베이스 생성
    if not os.path.exists(parent_dir):
        logger.info(f"DB 디렉토리가 존재하지 않습니다. 생성합니다: {parent_dir}")
        os.makedirs(parent_dir, exist_ok=True)
        # Batmon DB 생성
    create_batmon_db(db_path)

    logger.info(f"DB 파일 경로: {db_path}")
    logger.info(f"로그 파일 경로: {config.LOG_FILE}")
    logger.info('---------------------------------')
    logger.info('◀️  Startup 프로세스 종료')
    logger.info('---------------------------------')    

async def shutdown_event():
    ''' Batmon application 종료 '''
    logger.info('---------------------------------')
    logger.info('▶️  Shutdown 프로세스 시작')
    logger.info('---------------------------------')
    logger.info("Batmon application 종료 중...")    
    logger.info('---------------------------------')
    logger.info('◀️  Shutdown 프로세스 종료')
    logger.info('---------------------------------')

app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = getattr(config, "PORT", 8002)
    logger.info("batmon : Batch Program 모니터링, FastAPI 서버 시작 on port %s", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
