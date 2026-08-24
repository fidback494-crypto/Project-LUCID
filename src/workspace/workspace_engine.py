"""
Project LUCID

Artificial Mind Project

Module : Workspace Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .workspace_manager import WorkspaceManager


class WorkspaceEngine(BaseModule):

    def __init__(self):

        super().__init__("WorkspaceEngine")

        self.manager = WorkspaceManager()

    def start(self):

        Logger.info("Workspace Engine Started")

    def update(self):

        pass

    def stop(self):

        Logger.info("Workspace Engine Stopped")

    def current(self):

        return self.manager.current()

    def reset(self):

        self.manager.reset()