"""
Project LUCID

Artificial Mind Project

Module : Unified Cognitive Engine

Creator : 시드
"""

import json
import os
from time import monotonic

from src.cognitive.basic_conversation import BasicConversationFallback
from src.cognitive.cognitive_prompt import CognitivePrompt
from src.emotion.inner_experience import InnerExperience
from src.goal.goal import Goal
from src.kernel.base_module import BaseModule
from src.language.ollama_client import OllamaClient
from src.mind.plan import Plan
from src.mind.reason import Reason
from src.mind.thought import Thought
from src.utils import Logger


class CognitiveEngine(BaseModule):
    """Produces one coherent cognitive cycle from a role-separated chat."""

    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "reply": {"type": "string", "minLength": 1, "maxLength": 500},
            "intent": {
                "type": "string",
                "enum": ["question", "greeting", "conversation", "request", "emotion", "exit"],
            },
            "experience": {"type": "string", "maxLength": 60},
            "meaning": {"type": "string", "maxLength": 100},
            "speech_style": {
                "type": "string",
                "enum": [
                    "neutral", "warm", "curious", "cheerful", "playful",
                    "soothing", "concerned", "serious", "shy",
                ],
            },
        },
        "required": ["reply", "intent", "experience", "meaning", "speech_style"],
        "additionalProperties": False,
    }

    def __init__(self):

        super().__init__("CognitiveEngine")
        self.client = OllamaClient()
        self.prompt = CognitivePrompt()

    def start(self):

        Logger.info("Cognitive Engine Started")
        self.client.preload()

    def update(self):

        pass

    def stop(self):

        Logger.info("Cognitive Engine Stopped")
        self.client.close()

    def process(self, state):

        user_input = state.observation.content
        identity_reply = self._identity_reply(
            user_input,
            state.self_model.identity,
        )
        korean_input = self._contains_hangul(user_input)

        Logger.info("[Cognitive] Generating response from Ollama")
        started_at = monotonic()
        reply = self.client.generate(
            self._build_messages(state),
            options={"num_ctx": 4096, "num_predict": 192, "temperature": 0.4},
            response_format=self.RESPONSE_SCHEMA,
        )
        elapsed = monotonic() - started_at
        Logger.info(f"[Cognitive] Ollama response received in {elapsed:.1f}s")

        upstream_error = reply.strip()
        client_metrics = getattr(self.client, "last_metrics", {}) or {}
        if (
            client_metrics.get("error")
            or upstream_error in {
                "미안해. 응답 시간이 너무 오래 걸렸어.",
                "미안해. 현재 AI 서버에 연결할 수 없어.",
                "미안해. AI 처리 중 문제가 발생했어.",
            }
        ):
            response = self._model_unavailable_response(
                state,
                user_input,
                identity_reply,
            )
            state.response = response
            state.voice_response = response
            Logger.warning("[Cognitive] Using local fallback because Ollama is unavailable")
            return response

        fields = self._parse_fields(reply)
        response = fields.get("reply", "").strip()
        cognitive_output_valid = bool(response)

        if response and korean_input and not self._is_korean_reply(response):
            Logger.warning("[Cognitive] Non-Korean reply to Korean input; using one-call fallback")
            response = "앗, 말이 잠깐 꼬였어. 한 번만 다시 말해줄래?"
            cognitive_output_valid = False

        speech_style = fields.get("speech_style", "neutral").strip().lower()
        allowed_speech_styles = set(self.RESPONSE_SCHEMA["properties"]["speech_style"]["enum"])
        if speech_style not in allowed_speech_styles:
            speech_style = "neutral"
        state.speech_style = speech_style

        if cognitive_output_valid:
            self._apply_inner_life(state, fields)
            self._apply_reason(state, fields)
            self._apply_thought(state, fields)
            self._apply_goal_and_plan(state, fields)
            state.cognitive_success = True

        if not response:

            action_result = getattr(state, "action_result", None)

            if (
                action_result
                and action_result.success
                and action_result.output
            ):

                response = action_result.output

            elif identity_reply:
                # The model was called first. This is only a reliable fallback
                # if it fails to provide a usable answer for identity questions.
                response = identity_reply

            else:
                Logger.warning(
                    "[Cognitive] Model returned no usable Reply; hiding structured output"
                )
                response, _ = self._safe_fallback(user_input)

        if korean_input and not self._is_korean_reply(response):
            Logger.warning(
                "[Cognitive] Non-Korean fallback blocked from Korean chat output"
            )
            response, _ = self._safe_fallback(user_input)

        state.response = response
        state.voice_response = response

        Logger.info(
            "[Cognitive] One unified LLM response completed"
        )

        return response

    def _build_messages(self, state):
        """Keep the system prompt, prior turns, and current user turn separate."""

        try:
            history_limit = int(os.getenv("LUCID_CHAT_HISTORY_MESSAGES", "6"))
        except ValueError:
            history_limit = 6
        history_limit = max(0, min(history_limit, 8))

        messages = [{"role": "system", "content": self._build_prompt(state)}]
        history = state.conversation[-history_limit:] if history_limit else []
        for message in history:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = str(message.get("content", "")).strip()
            if role not in {"user", "assistant"} or not content:
                continue
            messages.append({
                "role": role,
                "content": self._limit_text(content, 400),
            })

        messages.append({
            "role": "user",
            "content": str(state.observation.content).strip(),
        })
        return messages

    def _build_prompt(self, state):
        return self.prompt.build(
            state,
            limit_text=self._limit_text,
            contains_hangul=self._contains_hangul,
            is_identity_request=self._is_identity_request,
            compact_identity_prompt=self._compact_identity_prompt,
            mentions_shared_page=self._mentions_shared_page,
        )

    @staticmethod
    def _compact_identity_prompt(identity):

        traits = " ".join(identity.personality)
        roleplay = " ".join(identity.roleplay_guidelines)
        return (
            f"이름: {identity.name} ({identity.alias}). "
            f"정체성: {identity.archetype}, {identity.species}. "
            f"나이: {identity.age}, 생일: {identity.birthday}, 키: {identity.height}. "
            f"사는 곳: {identity.home}. 배경: {identity.origin} "
            f"성격: {traits} "
            f"역할 연기 지침: {roleplay} "
            "기본 말투는 반말이며 상황에 따라 존댓말이나 반존대를 쓴다. "
            "설정을 매번 설명하지 말고 말투와 반응에 자연스럽게 드러낸다. "
            "사용자가 실제 AI나 프로그램의 정체를 직접 물으면 사실대로 답한다."
        )

    @staticmethod
    def _mentions_shared_page(text):

        lowered = str(text or "").casefold()
        return any(
            marker in lowered
            for marker in (
                "/page",
                "웹페이지",
                "웹 페이지",
                "웹사이트",
                "웹 사이트",
                "브라우저 페이지",
                "현재 페이지",
                "이 페이지",
                "이 사이트",
                "이 글",
                "website",
                "webpage",
            )
        )

    @staticmethod
    def _limit_text(value, limit):

        text = str(value or "").strip()
        limit = max(0, int(limit))
        if limit == 0:
            return ""
        if len(text) <= limit:
            return text
        return text[:limit - 1].rstrip() + "…"

    @staticmethod
    def _safe_fallback(user_input):

        fallback = BasicConversationFallback().respond(user_input)
        if fallback:
            return fallback[0], fallback[0]

        if CognitiveEngine._contains_hangul(user_input):
            return (
                "앗, 방금 답변 언어를 헷갈렸어. 한 번만 다시 물어봐 줄래?",
                "앗, 방금 답변 언어를 헷갈렸어. 한 번만 다시 물어봐 줄래?",
            )

        fallback = "I'm here, but I couldn't form a clear reply. Could you ask me once more?"
        return fallback, fallback

    def _model_unavailable_response(self, state, user_input, identity_reply):
        action = getattr(state, "action", None)
        action_result = getattr(state, "action_result", None)

        if action and action.need_action and action_result:
            if action_result.success and action_result.output:
                output = self._limit_text(action_result.output, 4000)
                if action.tool == "calculator":
                    return (
                        f"계산 결과는 {output}이야."
                        if self._contains_hangul(user_input)
                        else f"The result is {output}."
                    )
                if action.tool == "python":
                    return (
                        f"표현식 결과는 {output}이야."
                        if self._contains_hangul(user_input)
                        else f"The expression evaluates to {output}."
                    )
                return output
            if action_result.output:
                error = self._limit_text(action_result.output, 800)
                if self._contains_hangul(user_input):
                    return f"도구 실행이 실패했어: {error}. Ollama도 연결되지 않아 더 설명하기 어려워."
                return f"The tool failed: {error}. Ollama is also unavailable, so I can't add more detail."

        if identity_reply:
            return identity_reply

        fallback = BasicConversationFallback().respond(user_input)
        if fallback:
            response, speech_style, intent = fallback
            state.speech_style = speech_style
            state.reason = Reason(
                summary="Ollama 연결이 없어 기본 대화 응답으로 이어갔다.",
                intent=intent,
                confidence=0.35,
            )
            return response

        if self._contains_hangul(user_input):
            return (
                "지금은 Ollama 서버가 연결되지 않아 복잡한 답을 만들기 어려워. "
                "그래도 네 말은 들었어. 서버 연결을 확인한 뒤 이어서 이야기하자."
            )
        return (
            "Ollama isn't connected, so I can't work through a detailed answer right now. "
            "I hear you, though. Let's continue once the server is available."
        )

    @staticmethod
    def _contains_hangul(text):

        return any("\uac00" <= character <= "\ud7a3" for character in str(text))

    @classmethod
    def _is_korean_reply(cls, text):

        hangul_count = sum(
            1 for character in text
            if "\uac00" <= character <= "\ud7a3"
        )
        letter_count = sum(1 for character in text if character.isalpha())
        return hangul_count > 0 and hangul_count / max(1, letter_count) >= 0.3

    @staticmethod
    def _parse_fields(reply):

        candidate = str(reply or "").strip()
        if candidate.startswith("```"):
            candidate = candidate.removeprefix("```json").removeprefix("```JSON")
            candidate = candidate.removesuffix("```").strip()

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                fields = {}
                for key, value in parsed.items():
                    if value is None:
                        continue
                    normalized_key = str(key).strip().lower()
                    if normalized_key in {"voice_reply", "voicereply"}:
                        normalized_key = "spoken_english"
                    fields[normalized_key] = str(value).strip()
                return fields
        except (json.JSONDecodeError, TypeError):
            start = candidate.find("{")
            if start >= 0:
                try:
                    parsed, _ = json.JSONDecoder().raw_decode(candidate[start:])
                    if isinstance(parsed, dict):
                        fields = {}
                        for key, value in parsed.items():
                            if value is None:
                                continue
                            normalized_key = str(key).strip().lower()
                            if normalized_key in {"voice_reply", "voicereply"}:
                                normalized_key = "spoken_english"
                            fields[normalized_key] = str(value).strip()
                        return fields
                except (json.JSONDecodeError, TypeError):
                    pass

        fields = {}
        allowed = {
            "experience", "meaning", "trigger", "tendency", "persistence",
            "intent", "reason", "thought", "goal", "plan1", "plan2",
            "reply", "voice_reply", "spoken_english", "speech_style",
        }
        current_key = None

        for raw_line in reply.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                if key in {"voicereply", "voice_reply"}:
                    key = "spoken_english"

                if key in allowed:
                    fields[key] = value.strip()
                    current_key = key
                    continue

            # Some models put the answer on the line after `Reply:`.
            if current_key == "reply":
                existing = fields.get("reply", "")
                fields["reply"] = f"{existing}\n{line}".strip()

        return fields

    @staticmethod
    def _is_identity_request(normalized_input):

        return any(
            phrase in normalized_input
            for phrase in (
                "자기소개",
                "자기소게",
                "자시소게",
                "소개해줘",
                "넌이름",
                "루시드이름",
                "넌어디서왔",
                "넌어디서온",
                "루시드어디서왔",
                "루시드어디서온",
                "넌사는곳",
                "루시드사는곳",
                "넌고향",
                "루시드고향",
                "whatsyourname",
                "whoareyou",
                "wheredoyoulive",
                "whereareyoufrom",
            )
        )

    @classmethod
    def _identity_reply(cls, user_input, identity):

        normalized_input = "".join(
            character
            for character in user_input.lower()
            if character.isalnum()
        )

        if not cls._is_identity_request(normalized_input):
            return ""

        if any(
            phrase in normalized_input
            for phrase in (
                "넌이름", "루시드이름", "whatsyourname", "whoareyou",
            )
        ):
            if cls._contains_hangul(user_input):
                return (
                    f"난 {identity.name}, 루시드라고 불러도 돼. "
                    "꿈과 현실 사이를 오가는 몽마야."
                )
            return (
                f"I'm {identity.name}, though you can call me {identity.alias}. "
                "I'm a dream demon who wanders between dreams and reality."
            )

        if any(
            phrase in normalized_input
            for phrase in (
                "넌어디서왔", "넌어디서온", "루시드어디서왔",
                "루시드어디서온", "넌사는곳", "루시드사는곳",
                "넌고향", "루시드고향", "wheredoyoulive", "whereareyoufrom",
            )
        ):
            if cls._contains_hangul(user_input):
                return f"나는 {identity.home}에 살아. {identity.origin}"
            return f"I come from {identity.home}. {identity.origin}"

        if cls._contains_hangul(user_input):
            return (
                f"나는 {identity.name}, 루시드라고 불러도 돼. "
                f"{identity.species}이고 {identity.home}에 살아. "
                f"{identity.origin} 밤과 별, 달을 좋아해."
            )
        return (
            f"I'm {identity.name}, also known as {identity.alias}. "
            f"I'm {identity.species}, and I live in {identity.home}. "
            f"{identity.origin} I like nights, stars, and the moon."
        )

    @staticmethod
    def _apply_inner_life(state, fields):

        experience = InnerExperience(
            name=fields.get("experience") or "정리되지 않은 반향",
            meaning=(
                fields.get("meaning")
                or "현재 상황의 의미를 살펴보려는 내적 움직임"
            ),
            trigger=fields.get("trigger") or state.observation.content,
            tendency=(
                fields.get("tendency")
                or "사용자 요청을 차분히 이해하려 함"
            ),
            persistence=fields.get("persistence") or "다음 상호작용까지 머묾",
        )

        state.self_model.emotion.integrate(experience)
        state.emotion = state.self_model.emotion

    @staticmethod
    def _apply_reason(state, fields):

        intent = (fields.get("intent") or "conversation").lower()

        if intent not in {
            "question",
            "greeting",
            "conversation",
            "request",
            "emotion",
            "exit",
        }:

            intent = "conversation"

        state.reason = Reason(
            summary=fields.get("reason") or "사용자 입력의 맥락을 살핀다.",
            intent=intent,
            confidence=0.8,
        )

    @staticmethod
    def _apply_thought(state, fields):

        state.thought = Thought(
            type=state.reason.intent,
            content=fields.get("thought") or state.reason.summary,
            importance=state.reason.confidence,
        )

    @staticmethod
    def _apply_goal_and_plan(state, fields):

        title = fields.get("goal") or "사용자 요청에 적절히 응답"

        state.goal = Goal(title=title, priority=0.8)

        steps = [
            fields[key]
            for key in ("plan1", "plan2")
            if fields.get(key)
        ]

        if not steps:

            steps = ["사용자 요청을 이해하고 응답한다."]

        state.plan = Plan(
            goal=title,
            steps=steps,
            priority=0.8,
        )
