"""서버 없이 관찰, 작업 기억, 도구 선택, 계산까지 한 턴을 실행한다."""

from lucid.actions.tools.calculator import CalculatorTool
from lucid.core.state import BrainState
from lucid.memory.working import WorkingMemory
from lucid.mind.decisions import DecisionEngine
from lucid.mind.observation import ObservationEngine


def main() -> None:
    """예시 수식의 관찰과 도구 선택, 실제 계산 결과를 콘솔에 출력한다."""
    observation = ObservationEngine().process("2+3")
    memory = WorkingMemory()
    memory.add(observation)
    state = BrainState(observation=observation, working_memory=memory.recent())
    action = DecisionEngine().process(state).action_object
    print(f"관찰: {observation.content}")
    print(f"도구: {action.tool}")
    if action.tool == "calculator":
        print(f"결과: {CalculatorTool().execute(action.command).output}")


if __name__ == "__main__":
    main()
