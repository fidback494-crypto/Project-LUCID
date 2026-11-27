"""최근 메시지와 대화에서 선택한 말높임을 관리한다."""

from collections import deque


class ConversationManager:
    """최근 메시지와 대화에서 선택한 말높임을 관리한다."""

    def __init__(self, capacity=10):
        """capacity만큼 최근 메시지를 보관하고 기본 말높임을 설정한다."""
        self.history = deque(maxlen=capacity)
        self.speech_register = "banmal"

    def update_speech_register(self, user_text):
        """사용자의 명시적인 변경 요청을 반영한 대화 말높임을 반환한다."""
        normalized = "".join(
            character
            for character in str(user_text or "").casefold()
            if character.isalnum()
        )

        # 문서 작성을 위해 지정한 문체는 대화 전체의 말높임과 분리한다.
        artifact_markers = (
            "문장",
            "이메일",
            "메일",
            "대사",
            "번역",
            "공지",
            "문구",
            "예문",
            "보고서",
            "안내문",
            "편지",
            "자소서",
        )
        if any(marker in normalized for marker in artifact_markers):
            return self.speech_register

        requests = (
            (
                "half_polite",
                (
                    "앞으로반존대",
                    "계속반존대",
                    "이제부터반존대",
                    "반존대로말해",
                    "반존대로해줘",
                    "반존대로해",
                    "반존대써",
                    "말투를반존대",
                ),
            ),
            (
                "polite",
                (
                    "앞으로존댓말",
                    "계속존댓말",
                    "이제부터존댓말",
                    "존댓말로말해",
                    "존댓말로해줘",
                    "존댓말로해",
                    "존댓말써",
                    "존댓말부탁",
                    "존댓말로대화",
                    "나한테존댓말",
                    "말투를존댓말",
                    "존댓말로답해",
                    "높임말로말해",
                    "공손하게말해줘",
                    "정중하게대화해",
                ),
            ),
            (
                "banmal",
                (
                    "앞으로반말",
                    "계속반말",
                    "이제부터반말",
                    "반말로말해",
                    "반말로해줘",
                    "반말로해",
                    "반말써",
                    "반말부탁",
                    "반말로대화",
                    "나한테반말",
                    "말투를반말",
                    "말놔줘",
                    "말편하게해줘",
                    "편하게대화해",
                ),
            ),
        )
        explicit_requests = [
            (normalized.rfind(marker), register)
            for register, markers in requests
            for marker in markers
            if marker in normalized
        ]
        if explicit_requests:
            self.speech_register = max(explicit_requests)[1]
        return self.speech_register

    def add_user(self, text):
        """사용자 발화를 대화 기록 끝에 추가한다."""
        self.history.append(
            {
                "role": "user",
                "content": text,
            }
        )

    def add_assistant(self, text):
        """응답 문구를 대화 기록 끝에 추가한다."""
        self.history.append(
            {
                "role": "assistant",
                "content": text,
            }
        )

    def messages(self):
        """기록된 메시지를 발생 순서대로 복사해 반환한다."""
        return list(self.history)

    def clear(self):
        """최근 메시지와 선택된 대화 말높임을 초기화한다."""
        self.history.clear()
        self.speech_register = "banmal"
