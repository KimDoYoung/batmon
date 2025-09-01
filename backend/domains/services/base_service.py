from abc import ABC, abstractmethod
from datetime import datetime
import os
import subprocess
from typing import Optional

from pathlib import Path
from backend.core.config import config
from backend.domains.batmon_schema import ServiceStatus
from backend.core.logger import get_logger

logger = get_logger(__name__)

class BaseService(ABC):
    def __init__(self, program_name: str):
        self.program_name = program_name
        
        # config에서 프로그램 설정 가져오기
        program_config = config.get_program(program_name)
        if not program_config:
            raise ValueError(f"Program '{program_name}' not found in config")
        
        self.name = program_config.get('name', program_name)
        self.description = program_config.get('description', '')
        self.base_dir = program_config.get('base_dir', '')
        self.scheduler = program_config.get('scheduler', '')
        self.run_time = program_config.get('run_time', [])
        self.retry_program_name = program_config.get('retry_program', '')
        self.retry_program = os.path.join(self.base_dir, self.retry_program_name) if self.retry_program_name else ''
        self.log_dir = os.path.join(self.base_dir, "log")

    def _create_status(self, status: str, message: str, last_log: Optional[str] = None, last_log_time: Optional[str] = None) -> ServiceStatus:
        """공통 ServiceStatus 생성 헬퍼 메소드"""
        return ServiceStatus(
            name=self.name,
            description=self.description,
            status=status,
            message=message,
            last_log=last_log,
            last_log_time=last_log_time,
            last_updated=datetime.now(),
            base_dir=self.base_dir,
            scheduler=self.scheduler,
            run_time=self.run_time,
            retry_program=self.retry_program,
            retry_program_name=self.retry_program_name
        )
    
    def success_status(self, message: str = "Service is running properly", last_log: Optional[str] = None, last_log_time:Optional[str]=None) -> ServiceStatus:
        """OK 상태의 ServiceStatus 생성"""
        return self._create_status("OK", message, last_log, last_log_time)

    def error_status(self, message: str, last_log: Optional[str] = None, last_log_time: Optional[str] = None) -> ServiceStatus:
        """ERROR 상태의 ServiceStatus 생성"""
        return self._create_status("ERROR", message, last_log, last_log_time)

    def result_of_logfile(self, log_file):
        '''log_file을 읽어서 ERROR가 있으면 ERROR, 없으면 OK를 반환합니다.'''
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if "ERROR" in line:
                        return "ERROR"
                return "OK"
        except Exception as e:
            return f"Error reading log file: {str(e)}"

    def get_last_log_time(self, log_file: str) -> Optional[str]:
        """마지막 로그의 시간을 효율적으로 가져옵니다 (대용량 파일 지원)."""
        try:
            # 10MB 이상 파일은 끝에서 8KB만 읽음
            file_size = os.path.getsize(log_file)
            read_size = 8192  # 8KB
            with open(log_file, 'rb') as f:
                if file_size > read_size:
                    f.seek(-read_size, os.SEEK_END)
                data = f.read().decode('utf-8', errors='ignore')
                lines = data.splitlines()
                # 마지막 줄에서 시간 추출
                for line in reversed(lines):
                    if line.strip():
                        # '2025-07-15 16:21:14,287 [I] ...' -> '2025-07-15 16:21:14'
                        # 앞 19글자만 반환 (YYYY-MM-DD HH:MM:SS)
                        return line[:19]
        except Exception:
            return None

    def _process_is_running(self, program: str):
            """
            주어진 프로그램이 현재 실행 중인지 확인합니다.
            """
            try:
                # tasklist 명령어로 현재 실행 중인 프로세스 목록 가져오기
                result = subprocess.run(
                    ['tasklist', '/FI', f'IMAGENAME eq {os.path.basename(program)}'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    output = result.stdout.lower()
                    return os.path.basename(program).lower() in output
                
                return False
                
            except Exception as e:
                logger.error(f"Error checking process: {str(e)}")
                return False
        
    def _run(self):
        """ 프로그램을 실행한다. """
        program = self.retry_program

        if not program:
            raise ValueError("실행할 프로그램이 지정되지 않았습니다.")

        program_path = Path(program)
        if not program_path.exists():
            raise FileNotFoundError(f"실행할 프로그램이 존재하지 않습니다: {program_path}")

        try:
            subprocess.Popen(
                ["cmd", "/c", str(program_path)],
                cwd=program_path.parent,
                shell=False,
                close_fds=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            return
        except Exception as e:
            raise RuntimeError(f"실행 실패: {program_path} ({e})")

    @abstractmethod
    def check(self) -> ServiceStatus:
        """서비스 상태를 체크하는 추상 메소드"""
        pass