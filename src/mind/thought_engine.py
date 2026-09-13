"""
Project LUCID

Artificial Mind Project

Module : Thought Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger
from src.language.ollama_client import OllamaClient

from .thought import Thought


class ThoughtEngine(BaseModule):

    def __init__(self):

        super().__init__("ThoughtEngine")

        self.client = OllamaClient()

    def start(self):

        Logger.info("Thought Engine Started")

    def update(self):
        pass

    def stop(self):

        Logger.info("Thought Engine Stopped")

    # -------------------------------------------------

    def _build_prompt(self, state):

        observation = ""

        if state.observation:

            observation = state.observation.content

        # Working Memory

        working = []

        for item in state.working_memory:

            try:
                working.append(item.content)
            except:
                working.append(str(item))

        working = "\n".join(working)

        if not working:

            working = "없음"

        # Long Memory

        long_memory = []

        for item in state.long_memory:

            long_memory.append(str(item))

        long_memory = "\n".join(long_memory)

        if not long_memory:

            long_memory = "없음"

        # Conversation

        history = []

        for msg in state.conversation[-6:]:

            try:

                history.append(
                    f"{msg['role']} : {msg['content']}"
                )

            except:

                history.append(str(msg))

        history = "\n".join(history)

        if not history:

            history = "없음"

        # Inner life

        inner_life = state.self_model.emotion.summary()

        autonomous_goal = (
            state.self_model.autonomous_goal.describe()
            if state.self_model.autonomous_goal is not None
            else "없음"
        )

        return f"""
너는 LUCID의 Thought Engine이다.

목표

사용자의 입력을 보고

AI 내부에서 가장 적절한 생각을 만든다.

감정

기억

최근 대화

추론 결과를 모두 고려한다.

================================

사용자 입력

{observation}

================================

Reason

Intent : {state.reason.intent}

Summary : {state.reason.summary}

================================

최근 대화

{history}

================================

Working Memory

{working}

================================

Long Memory

{long_memory}

================================

현재 내적 경험

{inner_life}

================================

지속 관심과 자율 목표

{autonomous_goal}

사용자의 현재 요청이 항상 우선이다.

================================

반드시 아래 형식만 출력한다.

Thought:

Importance:
"""

    # -------------------------------------------------

    def _parse_response(
        self,
        reply,
        default_importance,
    ):

        thought = "생각을 정리한다."

        importance = default_importance

        for line in reply.splitlines():

            line = line.strip()

            if line.lower().startswith("thought"):

                thought = line.split(":", 1)[1].strip()

            elif line.lower().startswith("importance"):

                try:

                    importance = float(
                        line.split(":", 1)[1].strip()
                    )

                except:

                    pass

        return thought, importance

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

            Logger.info(f"[Thought LLM]\n{reply}")

            thought_text, importance = self._parse_response(
                reply,
                state.reason.confidence,
            )

        except Exception as e:

            Logger.error(f"Thought Error : {e}")

            thought_text = state.reason.summary

            importance = state.reason.confidence

        thought = Thought(
            type=state.reason.intent,
            content=thought_text,
            importance=importance,
        )

        Logger.info(f"[Thought] {thought.content}")

        return thought
