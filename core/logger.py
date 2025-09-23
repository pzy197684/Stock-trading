# core/logger.py
import logging
import os

class Logger:
    def __init__(self, log_file="logs/runtime.log"):
        # 创建日志器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # 控制台输出处理
        self.console_handler = logging.StreamHandler()
        # 文件输出处理
        self.file_handler = logging.FileHandler(log_file)

        # 日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.console_handler.setFormatter(formatter)
        self.file_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)

    def log_info(self, message):
        """日志 - 信息级别"""
        self.logger.info(message)

    def log_warning(self, message):
        """日志 - 警告级别"""
        self.logger.warning(message)

    def log_error(self, message):
        """日志 - 错误级别"""
        self.logger.error(message)

    def log_exception(self, message):
        """日志 - 异常级别"""
        self.logger.exception(message)

# 实例化 Logger
logger = Logger()
