from datetime import datetime
import os
import subprocess
from typing import Optional

from backend.domains.batmon_schema import ServiceStatus
from backend.domains.services.base_service import BaseService
from backend.core.logger import get_logger

logger = get_logger(__name__)

class KindscrapService(BaseService):
    def __init__(self, program_name: str = "kindscrap"):
        super().__init__(program_name)
    
    def check(self) -> ServiceStatus:
        """
        Kindscrap 서비스의 상태를 체크합니다.
        """
        try:
            logger.info("kindscrap 서비스 상태 체크 시작")
            # 기본 디렉토리 존재 여부 확인
            if not os.path.exists(self.base_dir):
                return self.error_status(f"설치 폴더가 존재하지 않습니다: {self.base_dir}")
            logger.info("설치 폴더 확인 완료")
            # 로그 파일 확인
            last_log = self._get_last_log()
            
            if not os.path.exists(self.log_dir):
                return self.error_status(f"로그 폴더가 존재하지 않습니다: {self.log_dir}")

            last_log_file = self._get_last_log()

            if not last_log_file or not os.path.exists(last_log_file):
                return self.error_status(f"오늘의 로그 파일을 찾을 수 없습니다.")

            result = self.result_of_logfile(last_log)
            if result == "ERROR":
                return self.error_status(f"로그 파일에서 오류를 발견했습니다: {last_log_file}")
            else:
                last_log_time = self.get_last_log_time(last_log_file) if last_log else None
                last_log_file = os.path.basename(last_log_file) if last_log else None

                return self.success_status("kindscrap 정상동작 중입니다", last_log_file, last_log_time)

        except Exception as e:
            return self.error_status(f"Error checking service: {str(e)}")
    
    def _get_last_log(self) -> Optional[str]:
        """마지막 로그를 가져옵니다."""
        ymd = datetime.now().strftime('%Y_%m_%d')
        filename = f"kindscrap_{ymd}.log"
        log_file = os.path.join(self.log_dir,  filename)
            
        return log_file
    
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
