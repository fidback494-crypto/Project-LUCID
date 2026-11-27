"""등록한 도구를 실행하고 결과를 통일된 형식으로 반환한다."""

from lucid.actions.models import Action, ActionResult
from lucid.core.kernel import BaseModule
from lucid.log import Logger


class ActionRegistry:
    """도구 이름과 객체를 등록 순서대로 보관한다."""

    def __init__(self):
        """등록한 도구를 이름으로 조회할 사전을 초기화한다."""
        self._tools = {}

    def register(self, name, tool):
        """이름에 도구를 연결한다. 같은 이름은 새 도구로 교체한다."""
        self._tools[name] = tool

    def get(self, name):
        """이름으로 도구를 조회하고 미등록이면 None을 돌려준다."""
        return self._tools.get(name)

    def exists(self, name):
        """해당 이름의 도구가 등록되어 있는지 반환한다."""
        return name in self._tools

    def names(self):
        """등록된 도구 이름의 복사본을 반환한다."""
        return list(self._tools)


class ActionEngine(BaseModule):
    """결정 단계가 선택한 도구를 실행한다."""

    def __init__(self):
        """도구 명령을 처리할 빈 레지스트리를 만든다."""
        super().__init__()
        self.registry = ActionRegistry()

    def register(self, name, tool):
        """도구를 주어진 이름으로 등록한다."""
        self.registry.register(name, tool)
        Logger.info(f"[Action] Tool Registered : {name}")

    def process(self, action: Action | None) -> ActionResult:
        """명령을 등록된 도구로 실행하고 성공 여부와 결과를 반환한다."""
        if action is None or not action.need_action:
            return ActionResult(success=True, output="")

        tool = self.registry.get(action.tool)
        if tool is None:
            Logger.warning(f"[Action] Unknown Tool : {action.tool}")
            return ActionResult(
                success=False, output=f"Tool '{action.tool}' not found."
            )

        Logger.info(f"[Action] {action.tool}")
        try:
            result = tool.execute(action.command)
        except Exception as error:
            Logger.error(f"[Action Error] {error}")
            return ActionResult(success=False, output=str(error))

        if isinstance(result, ActionResult):
            return result
        return ActionResult(success=True, output=str(result))
