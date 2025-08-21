
import os
import subprocess
from typing import Optional

from backend.domains.batmon_schema import ServiceStatus
from backend.domains.services.base_service import BaseService
from datetime import datetime
from backend.core.logger import get_logger

logger = get_logger(__name__)

class AutoEsafeService(BaseService):
    def __init__(self, program_name: str = "auto_esafe"):
        super().__init__(program_name)
    
    def check(self) -> ServiceStatus:
        """
        Auto Esafe 서비스의 상태를 체크합니다.
        """
        try:
            logger.info("auto_esafe 서비스 상태 체크시작")
            # 기본 디렉토리 존재 여부 확인
            if not os.path.exists(self.base_dir):
                return self.error_status(f"설치 폴더가 존재하지 않습니다.: {self.base_dir}")
            logger.info("설치 폴더 확인 완료")
            # 로그폴더가 있는지 체크
            if not os.path.exists(self.log_dir):
                return self.error_status(f"로그 폴더가 존재하지 않습니다.: {self.log_dir}")
            logger.info("로그 폴더 확인 완료")

            # 로그 파일이 있는지 체크 
            last_log_file = self._get_last_log()
            if not last_log_file or not os.path.exists(last_log_file):
                return self.error_status(f"생성되어야 할 로그파일을 찾지 못함"  )
            result = self.result_of_logfile(last_log_file)
            if result == "ERROR":
                return self.error_status(f"로그파일에서 ERROR 발견: {last_log_file}")
            else:
                last_log_time = self.get_last_log_time(last_log_file)
                last_log_file = os.path.basename(last_log_file) if last_log_file else None
                return self.success_status("Auto_Esafe는 정상동작 중입니다.", last_log_file, last_log_time)

        except Exception as e:
            return self.error_status(f"Error checking service: {str(e)}")
    
    def _get_last_log(self) -> Optional[str]:
        """마지막 로그를 가져옵니다."""
        ymd = datetime.now().strftime('%Y_%m_%d')
        # ymd = "2025_08_13"
        log_file = os.path.join(self.log_dir, f"auto_esafe_{ymd}.log")
        return log_file


    
    def _check_scheduler_task(self) -> bool:
        """
        Windows Task Scheduler에서 Auto Esafe 작업이 등록되어 있는지 확인합니다.
        """
        try:
            # taskschd.msc 명령어로 작업 목록 확인
            result = subprocess.run(
                ['taskschd.msc', '/query', '/fo', 'csv'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Auto Esafe 관련 작업이 있는지 확인
                output = result.stdout.lower()
                return 'auto' in output and 'esafe' in output
            
            return False
            
        except Exception:
            # schtasks 명령어 실행 실패 시 기본값 반환
            return False


# 사용 예시
if __name__ == "__main__":
    # config에서 auto_esafe 설정을 자동으로 로드
    service = AutoEsafeService("auto_esafe")
    
    print(f"Service Name: {service.name}")
    print(f"Description: {service.description}")
    print(f"Base Directory: {service.base_dir}")
    print(f"Scheduler: {service.scheduler}")
    print(f"Run Time: {service.run_time}")
    print(f"last log: {service._get_last_log()}")
    
    # 상태 체크
    status = service.check()
    print(f"\nStatus Check Result:")
    print(f"Status: {status.status}")
    print(f"Message: {status.message}")
    print(f"Last Updated: {status.last_updated}")

