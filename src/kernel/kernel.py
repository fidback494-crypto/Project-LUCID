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
        self._started_modules = []

    def register(self, module):
        """기관 등록"""
        if any(existing.name == module.name for existing in self.modules):
            Logger.warning(f"Module already registered : {module.name}")
            return False
        self.modules.append(module)
        Logger.info(f"Module Registered : {module.name}")
        return True

    def start(self):
        if self._started_modules:
            return

        Logger.info("Kernel Started")

        for module in self.modules:
            if not getattr(module, "enabled", True):
                continue
            self._started_modules.append(module)
            try:
                module.start()
            except Exception as error:
                Logger.error(
                    f"Module start failed : {module.name} ({type(error).__name__})"
                )
                self._stop_started_modules()
                raise

    def update(self):
        for module in tuple(self._started_modules):
            if not getattr(module, "enabled", True):
                continue
            try:
                module.update()
            except Exception as error:
                Logger.error(
                    f"Module update failed : {module.name} ({type(error).__name__})"
                )

    def stop(self):
        Logger.info("Kernel Stopped")
        self._stop_started_modules()

    def _stop_started_modules(self):
        while self._started_modules:
            module = self._started_modules.pop()
            try:
                module.stop()
            except Exception as error:
                Logger.error(
                    f"Module stop failed : {module.name} ({type(error).__name__})"
                )
