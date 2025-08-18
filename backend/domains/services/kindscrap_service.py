import os
import subprocess
from typing import Optional

from backend.domains.schemas import ServiceStatus
from backend.domains.services.base_service import BaseService


class KindscrapService(BaseService):
    def __init__(self, program_name: str = "kindscrap"):
        super().__init__(program_name)
    
    def check(self) -> ServiceStatus:
        """
        Kindscrap 서비스의 상태를 체크합니다.
        """
        try:
            # 기본 디렉토리 존재 여부 확인
            if not os.path.exists(self.base_dir):
                return self.error_status(f"Base directory not found: {self.base_dir}")
            
            # 로그 파일 확인
            last_log = self._get_last_log()
            
            # 스케줄러 작업 상태 확인
            if self._check_scheduler_task():
                return self.success_status("Kindscrap는 정상동작 중입니다.", last_log)
            else:
                return self.warning_status("Scheduler task may not be configured or running", last_log)
            
        except Exception as e:
            return self.error_status(f"Error checking service: {str(e)}")
    
    def _get_last_log(self) -> Optional[str]:
        """마지막 로그를 가져옵니다."""
        log_file = os.path.join(self.base_dir, "logs", "kindscrap.log")
        
        if not os.path.exists(log_file):
            return None
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-1].strip() if lines else None
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def _check_scheduler_task(self) -> bool:
        """
        Windows Task Scheduler에서 Kindscrap 작업이 등록되어 있는지 확인합니다.
        """
        try:
            result = subprocess.run(
                ['schtasks', '/query', '/fo', 'csv'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                return 'kindscrap' in output
            
            return False
            
        except Exception:
            return False


# 사용 예시
if __name__ == "__main__":
    service = KindscrapService("kindscrap")
    status = service.check()
    print(f"Status: {status.status} - {status.message}")
