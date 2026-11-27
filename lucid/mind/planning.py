"""목표와 생각을 바탕으로 단계별 계획을 만든다."""

from lucid.language.ollama import OllamaModule
from lucid.log import Logger
from lucid.mind.models import Plan


class PlanningEngine(OllamaModule):
    """목표와 생각을 바탕으로 단계별 계획을 만든다."""

    def _build_prompt(self, state):
        """목표, 현재 생각, 장기 기억을 계획 생성에 사용할 문자열로 묶는다."""
        memory = "\n".join(state.long_memory)

        if not memory:
            memory = "없음"
        return f"""
너는 LUCID의 Planning Engine이다.

목표와 생각을 참고하여
실행 계획을 만들어라.

========================
Goal
========================

{state.goal.title}

========================
Thought
========================

{state.thought.content}

========================
관련 기억
========================

{memory}

아래 형식으로만 출력한다.

Goal:
Priority:
Step1:
Step2:
Step3:
"""

    def _parse_response(self, reply, default_goal, default_priority):
        """응답의 목표, 우선순위, 실행 단계를 추출하고 누락된 값은 기본값으로 채운다."""
        goal = default_goal
        priority = default_priority

        steps = []

        for line in reply.splitlines():
            line = line.strip()

            if line.lower().startswith("goal"):
                goal = line.split(":", 1)[1].strip()

            elif line.lower().startswith("priority"):
                try:
                    priority = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass

            elif line.lower().startswith("step"):
                step = line.split(":", 1)[1].strip()

                if step:
                    steps.append(step)

        if not steps:
            steps = [
                "사용자 의도를 파악한다.",
                "응답을 생성한다.",
            ]
        return goal, priority, steps

    def process(self, state):
        """현재 목표와 기억에서 단계별 계획을 생성해 반환한다."""
        prompt = self._build_prompt(state)

        messages = [
            {
                "role": "system",
                "content": prompt,
            }
        ]

        try:
            reply = self.client.generate(messages)

            Logger.info(f"[Planning LLM]\n{reply}")

            goal, priority, steps = self._parse_response(
                reply,
                state.goal.title,
                state.goal.priority,
            )

        except Exception as e:
            Logger.error(f"Planning Error : {e}")

            goal = state.goal.title
            priority = state.goal.priority

            steps = [
                "사용자 의도를 파악한다.",
                "응답을 생성한다.",
            ]

        plan = Plan(
            goal=goal,
            steps=steps,
            priority=priority,
        )

        Logger.info(f"[Planning] {plan.goal}")

        for i, step in enumerate(plan.steps, start=1):
            Logger.info(f"  Step {i}: {step}")
        return plan


class Planner:
    """감정 상태에 따라 다음 행동의 이름을 선택한다."""

    def decide(self, emotion, memories, event):
        """
        행복감과 외로움에 따라 응답 행동 이름을 반환한다. 기억과 이벤트는 호환 인수다.
        """

        if emotion.happiness >= 70:
            return "friendly_reply"

        if emotion.loneliness >= 50:
            return "start_conversation"
        return "normal_reply"
