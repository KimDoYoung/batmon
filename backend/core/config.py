# config.py
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv


class Config:
    def __init__(self):
        # 1) 기존 .env 기반 설정 (유지)
        self.PROFILE_NAME = os.getenv('BATMON_MODE', 'local')
        load_dotenv(dotenv_path=f'.env.{self.PROFILE_NAME}')
        self.VERSION = os.getenv('VERSION', '0.0.3')
        self.PORT = int(os.getenv('PORT', 8002))

        # 2) 경로/로그 (유지)
        self.BASE_DIR = os.getenv('BASE_DIR', r'c:\batmon')
        self.DB_PATH = f'{self.BASE_DIR}/db/batmon.db'
        os.makedirs(Path(self.DB_PATH).parent, exist_ok=True)

        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
        self.LOG_DIR = os.getenv('LOG_DIR', f'{self.BASE_DIR}/logs')
        self.LOG_FILE = f'{self.LOG_DIR}/batmon.log'
        os.makedirs(Path(self.LOG_FILE).parent, exist_ok=True)

        # 3) YAML 경로 및 로드
        #    - 기본은 BASE_DIR/BATMON.yml
        #    - 환경변수 BATMON_YAML로 오버라이드 가능
        self.YAML_PATH = Path(os.getenv('BATMON_YAML', f'{self.BASE_DIR}/BATMON.yml'))
        self._yaml_mtime: float = 0.0
        self.programs: List[Dict[str, Any]] = []  # 통합된 결과 보관

        self.reload_yaml(force=True)


    # --- YAML 처리부 ---------------------------------------------------------
    def reload_yaml(self, force: bool = False) -> bool:
        """BATMON.yml 변경 시 다시 읽어들이고, programs에 반영"""
        if not self.YAML_PATH.exists():
            self.programs = []
            return False

        mtime = self.YAML_PATH.stat().st_mtime
        if force or mtime > self._yaml_mtime:
            with self.YAML_PATH.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            self.programs = self._validate_and_normalize(data)
            self._yaml_mtime = mtime
            return True

    def _validate_and_normalize(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """스키마 최소 검증 + 기본값 주입"""
        items = data.get('programs') or []
        norm: List[Dict[str, Any]] = []
        for i, raw in enumerate(items):
            if not isinstance(raw, dict):
                raise ValueError(f'programs[{i}] 항목이 객체가 아닙니다.')
            name = (raw.get('name') or '').strip()
            if not name:
                raise ValueError(f'programs[{i}].name 누락')

            norm.append({
                'name': name,
                'description': raw.get('description', ''),
                'base_dir': raw.get('base_dir', ''),
                'scheduler': raw.get('scheduler', ''),   # e.g. "taskschd.msc" | "windows service"
                'run_time': raw.get('run_time', []),     # e.g. ["0630","1830"] 또는 "*/5min" 등
                'retry_program': raw.get('retry_program', ''), # e.g. "run_kindscrap.bat"
            })
        return norm

    # --- 조회 헬퍼 -----------------------------------------------------------
    def list_programs(self) -> List[Dict[str, Any]]:
        self.reload_yaml()  # 변경 감지 후 필요 시 재로딩
        return self.programs

    def get_program(self, name: str) -> Optional[Dict[str, Any]]:
        self.reload_yaml()
        for p in self.programs:
            if p['name'] == name:
                return p
        return None

# 단일톤
config = Config()
