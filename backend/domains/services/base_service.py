from abc import ABC, abstractmethod
from datetime import datetime
import os
from typing import Optional

from backend.core.config import config
from backend.domains.batmon_schema import ServiceStatus


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
            run_time=self.run_time
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

    @abstractmethod
    def check(self) -> ServiceStatus:
        """서비스 상태를 체크하는 추상 메소드"""
        pass