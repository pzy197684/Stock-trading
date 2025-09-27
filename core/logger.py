
# core/logger.py
# 功能：日志记录功能，支持不同级别的日志输出（控制台+文件）
import logging
import os

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "runtime.log")

class Logger:
    def __init__(self, log_file=LOG_FILE):
        self.logger = logging.getLogger("stock_trading")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        # 控制台
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        # 文件
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        # 避免重复添加handler
        if not self.logger.handlers:
            self.logger.addHandler(ch)
            self.logger.addHandler(fh)

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)

    def log_exception(self, message):
        self.logger.exception(message)

# 实例化 Logger
logger = Logger()
