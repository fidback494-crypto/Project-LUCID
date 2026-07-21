"""
Project LUCID

Artificial Mind Project

Module : Logger

Creator : 시드
"""

from datetime import datetime


class Logger:
    """LUCID의 모든 로그를 출력하는 클래스"""

    @staticmethod
    def info(message: str):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [INFO] {message}")

    @staticmethod
    def warning(message: str):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [WARNING] {message}")

    @staticmethod
    def error(message: str):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [ERROR] {message}")