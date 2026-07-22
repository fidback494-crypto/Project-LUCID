"""
Project LUCID

Artificial Mind Project

Module : Planning Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from src.language.ollama_client import OllamaClient

from .plan import Plan


class PlanningEngine(BaseModule):

    def __init__(self):

        super().__init__("PlanningEngine")

        self.client = OllamaClient()

    def start(self):
        Logger.info("Planning Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Planning Engine Stopped")

    # -------------------------------------------------
    # Prompt
    # -------------------------------------------------

    def _build_prompt(self, state):

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

    # -------------------------------------------------
    # Parse
    # -------------------------------------------------

    def _parse_response(self, reply, default_goal, default_priority):

        goal = default_goal
        priority = default_priority

        steps = []

        for line in reply.splitlines():

            line = line.strip()

            if line.lower().startswith("goal"):

                goal = line.split(":", 1)[1].strip()

            elif line.lower().startswith("priority"):

                try:
                    priority = float(
                        line.split(":", 1)[1].strip()
                    )
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

    # -------------------------------------------------
    # Process
    # -------------------------------------------------

    def process(self, state):

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