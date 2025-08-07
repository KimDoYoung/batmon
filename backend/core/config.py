from dotenv import load_dotenv
import os
class Config:
    def __init__(self):
        self.PROFILE_NAME = os.getenv('BATMON_MODE', 'local')
        load_dotenv(dotenv_path=f'.env.{self.PROFILE_NAME}')
        # PORT 설정
        self.PORT = int(os.getenv('PORT', 8002))
        
        # BASE_DIR 설정
        self.BASE_DIR = os.getenv('BASE_DIR', 'c:\\batmon')
        self.DB_PATH =  f'{self.BASE_DIR}/db/batmon.db'
        db_dir = os.path.dirname(self.DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        # 로그 설정
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
        self.LOG_DIR = os.getenv('LOG_DIR', f'{self.BASE_DIR}/logs')
        self.LOG_FILE = self.LOG_DIR + '/batmon.log'
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(self.LOG_FILE)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

config = Config()