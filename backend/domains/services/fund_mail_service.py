import os
import subprocess
from datetime import datetime
from typing import Optional

from backend.domains.batmon_schema import ServiceStatus
from backend.domains.services.base_service import BaseService
from backend.core.logger import get_logger

logger = get_logger(__name__)

class FundMailService(BaseService):
    def __init__(self, program_name: str = "fund_mail"):
        super().__init__(program_name)
        self.log_dir = os.path.join(self.base_dir, "logs")
        self.data_dir = os.path.join(self.base_dir, "data")
    
    def check(self) -> ServiceStatus:
        """
        Fund Mail 서비스의 상태를 체크합니다.
        """
        try:
            logger.info("fund_mail 서비스 상태 체크 시작")
            # 기본 디렉토리 존재 여부 확인
            if not os.path.exists(self.base_dir):
                return self.error_status(f"설치폴더가 존재하지 않습니다.: {self.base_dir}")
            
            if not os.path.exists(self.log_dir):
                return self.error_status(f"로그 폴더가 존재하지 않습니다.: {self.log_dir}")
            logger.info("로그 폴더 확인 완료")

            # 데이터 폴더 확인
            if not os.path.exists(self.data_dir):
                return self.error_status(f"데이터 폴더가 존재하지 않습니다.: {self.data_dir}")
            ymd = datetime.now().strftime('%Y_%m_%d')
            today_data_folder = os.path.join(self.data_dir, f"{ymd}")
            if not os.path.exists(today_data_folder):
                return self.error_status(f"오늘의 데이터 폴더가 존재하지 않습니다.: {today_data_folder}")
            
            last_file = self._get_last_data_file(today_data_folder)
            if not last_file:
                return self.error_status(f"오늘의 데이터 폴더에 파일이 존재하지 않습니다.: {today_data_folder}")
            
            # fm_2025_07_14_20_20.db last_file
            last_file_datetime = self._parse_filename_to_datetime(last_file) if last_file else None
            # last_file_datetime이 지금 시각과 10분 이상 차이가 나면 error
            if last_file_datetime and (datetime.now() - last_file_datetime).total_seconds() > 600:
                return self.error_status(f"최근 파일의 시간 차이가 10분을 초과합니다.: 마지막 파일: {last_file}, 시간: {last_file_datetime}")
            else:
                last_log = self._get_last_log()
                last_log_time = self.get_last_log_time(last_log) if last_log else None
                return self.success_status("Fund Mail 서비스가 정상적으로 동작 중입니다.", last_log, last_log_time)

        except Exception as e:
            return self.error_status(f"Error checking service: {str(e)}")
    
    def _parse_filename_to_datetime(self, filename: str) -> Optional[datetime]:
        """
        파일명 'fm_2025_07_14_20_20.db'에서 datetime 객체를 추출합니다.
        
        Args:
            filename: 파일명 (예: 'fm_2025_07_14_20_20.db')
            
        Returns:
            datetime 객체 또는 None (파싱 실패 시)
        """
        try:
            if not filename or not isinstance(filename, str):
                return None
            
            # 확장자 제거
            name_without_ext = filename.replace('.db', '')
            
            # 'fm_' 접두사 제거하고 '_'로 분리
            parts = name_without_ext.replace('fm_', '').split('_')
            
            # 예상 형식: ['2025', '07', '14', '20', '20']
            if len(parts) != 5:
                logger.warning(f"파일명 형식이 예상과 다릅니다: {filename}")
                return None
            
            year, month, day, hour, minute = map(int, parts)
            
            return datetime(year, month, day, hour, minute)
            
        except (ValueError, IndexError) as e:
            logger.error(f"파일명 파싱 중 오류 발생: {filename}, 오류: {str(e)}")
            return None
        
    def _get_last_data_file(self, folder: str) -> Optional[str]:
        '''folder에서 확장자가 .db인 가장 최근의 파일'''
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.endswith('.db')]
            if not files:
                return None
            return max(files, key=lambda f: os.path.getctime(os.path.join(folder, f)))
        except Exception as e:
            return f"Error getting last data file: {str(e)}"

    def _get_last_log(self) -> Optional[str]:
        """마지막 로그를 가져옵니다."""
        log_file = os.path.join(self.base_dir, "logs", "fund_mail.log")
        return log_file if os.path.exists(log_file) else None            

    
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
