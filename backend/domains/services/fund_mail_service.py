import os
import subprocess
from typing import Optional

from backend.domains.schemas import ServiceStatus
from backend.domains.services.base_service import BaseService


class FundMailService(BaseService):
    def __init__(self, program_name: str = "fund_mail"):
        super().__init__(program_name)
    
    def check(self) -> ServiceStatus:
        """
        Fund Mail 서비스의 상태를 체크합니다.
        """
        try:
            # 기본 디렉토리 존재 여부 확인
            if not os.path.exists(self.base_dir):
                return self.error_status(f"Base directory not found: {self.base_dir}")
            
            # 로그 파일 확인
            last_log = self._get_last_log()
            
            # Windows Service 상태 확인 (fund_mail은 window service로 설정됨)
            if self._check_windows_service():
                return self.success_status("Fund Mail 서비스는 정상동작 중입니다.", last_log)
            else:
                return self.warning_status("Windows service may not be running", last_log)
            
        except Exception as e:
            return self.error_status(f"Error checking service: {str(e)}")
    
    def _get_last_log(self) -> Optional[str]:
        """마지막 로그를 가져옵니다."""
        log_file = os.path.join(self.base_dir, "logs", "fund_mail.log")
        
        if not os.path.exists(log_file):
            return None
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-1].strip() if lines else None
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def _check_windows_service(self) -> bool:
        """
        Windows Service로 Fund Mail이 실행되고 있는지 확인합니다.
        """
        try:
            # sc query 명령어로 서비스 상태 확인
            result = subprocess.run(
                ['sc', 'query'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                # fund_mail 관련 서비스가 실행 중인지 확인
                return 'fund' in output and 'mail' in output and 'running' in output
            
            return False
            
        except Exception:
            return False


# 사용 예시
if __name__ == "__main__":
    service = FundMailService("fund_mail")
    status = service.check()
    print(f"Status: {status.status} - {status.message}")
