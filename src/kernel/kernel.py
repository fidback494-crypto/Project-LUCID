"""
Project LUCID

Artificial Mind Project

Module : Kernel

Creator : 시드
"""

from src.utils import Logger


class Kernel:

    def __init__(self):
        self.modules = []

    def register(self, module):
        """기관 등록"""
        self.modules.append(module)
        Logger.info(f"Module Registered : {module.name}")

    def start(self):
        Logger.info("Kernel Started")

        for module in self.modules:
            module.start()

    def update(self):
        for module in self.modules:
            module.update()

    def stop(self):
        Logger.info("Kernel Stopped")

        for module in self.modules:
            module.stop()