"""입력과 추론 결과를 바탕으로 현재 생각과 중요도를 생성한다."""

from collections import deque

from lucid.language.ollama import OllamaModule
from lucid.language.prompts import format_history, format_memory
from lucid.log import Logger
from lucid.mind.models import Thought


class ThoughtEngine(OllamaModule):
    """입력과 추론 결과를 바탕으로 현재 생각과 중요도를 생성한다."""

    def _build_prompt(self, state):
        """관찰, 추론, 최근 대화와 기억을 생각 생성에 사용할 문자열로 묶는다."""
        observation = state.observation.content if state.observation else ""
        working = format_memory(state.working_memory, content_only=True)
        long_memory = format_memory(state.long_memory)
        history = format_history(state.conversation, 6)
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

    def _parse_response(
        self,
        reply,
        default_importance,
    ):
        """모델 응답에서 생각과 중요도를 추출한다. 중요도가 없으면 전달받은 기본값을 쓴다."""
        thought = "생각을 정리한다."

        importance = default_importance

        for line in reply.splitlines():
            line = line.strip()

            if line.lower().startswith("thought"):
                thought = line.split(":", 1)[1].strip()

            elif line.lower().startswith("importance"):
                try:
                    importance = float(line.split(":", 1)[1].strip())

                except Exception:
                    pass
        return thought, importance

    def process(self, state):
        """현재 관찰과 추론 결과를 받아 중요도가 포함된 생각을 반환한다."""
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


class ThoughtQueue:
    """LUCID의 현재 생각들을 저장하는 큐"""

    def __init__(self):
        """생각을 순서대로 꺼낼 대기열을 만든다."""
        self.queue = deque()

    def push(self, thought):
        """주어진 생각을 대기열의 끝에 추가한다."""
        self.queue.append(thought)

    def pop(self):
        """가장 오래된 생각을 꺼내고 대기열이 비었으면 None을 반환한다."""
        if self.queue:
            return self.queue.popleft()
        return None

    def is_empty(self):
        """처리할 생각이 남아 있는지 확인해 비었으면 True를 반환한다."""
        return len(self.queue) == 0

    def size(self):
        """대기 중인 생각 개수를 반환한다."""
        return len(self.queue)
