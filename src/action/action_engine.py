"""
Project LUCID

Artificial Mind Project

Module : Action Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .action_result import ActionResult
from .action_registry import ActionRegistry


class ActionEngine(BaseModule):

    def __init__(self):

        super().__init__("ActionEngine")

        self.registry = ActionRegistry()

    # =================================================
    # Lifecycle
    # =================================================

    def start(self):

        Logger.info("Action Engine Started")

    def update(self):

        pass

    def stop(self):

        Logger.info("Action Engine Stopped")

    # =================================================
    # Register Tool
    # =================================================

    def register(self, name, tool):

        self.registry.register(
            name,
            tool
        )

        Logger.info(
            f"[Action] Tool Registered : {name}"
        )

    # =================================================
    # Process
    # =================================================

    def process(self, action):

        if action is None:

            return ActionResult(
                success=True,
                output="",
            )

        if not action.need_action:

            return ActionResult(
                success=True,
                output="",
            )

        # ---------------------------------------------
        # Tool 검색
        # ---------------------------------------------

        tool = self.registry.get(
            action.tool
        )

        if tool is None:

            Logger.warning(
                f"[Action] Unknown Tool : {action.tool}"
            )

            return ActionResult(
                success=False,
                output=(
                    f"Tool '{action.tool}' not found."
                ),
            )

        Logger.info(
            f"[Action] "
            f"{action.tool} -> "
            f"{action.command}"
        )

        # ---------------------------------------------
        # Tool 실행
        # ---------------------------------------------

        try:

            result = tool.execute(
                action.command
            )

            # Tool이 ActionResult를 반환하는 경우
            if isinstance(
                result,
                ActionResult
            ):

                return result

            # 일반 결과값
            return ActionResult(
                success=True,
                output=str(result),
            )

        except Exception as e:

            Logger.error(
                f"[Action Error] {e}"
            )

            return ActionResult(
                success=False,
                output=str(e),
            )