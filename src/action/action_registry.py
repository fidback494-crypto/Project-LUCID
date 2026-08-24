"""
Project LUCID

Artificial Mind Project

Module : Action Registry

Creator : 시드
"""


class ActionRegistry:

    def __init__(self):

        self._tools = {}

    # -----------------------------------------
    # Register
    # -----------------------------------------

    def register(self, name, tool):

        self._tools[name] = tool

    # -----------------------------------------
    # Get
    # -----------------------------------------

    def get(self, name):

        return self._tools.get(name)

    # -----------------------------------------
    # Exists
    # -----------------------------------------

    def exists(self, name):

        return name in self._tools

    # -----------------------------------------
    # List
    # -----------------------------------------

    def names(self):

        return list(self._tools.keys())