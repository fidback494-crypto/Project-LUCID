"""
Project LUCID

Artificial Mind Project

Module : Workspace Manager

Creator : 시드
"""

from .workspace import Workspace


class WorkspaceManager:

    def __init__(self):

        self._workspace = Workspace()

    def current(self):

        return self._workspace

    def reset(self):

        self._workspace.clear()

    def replace(self, workspace: Workspace):

        self._workspace = workspace