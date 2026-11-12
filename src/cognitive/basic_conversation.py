"""Small Korean/English small-talk responses for temporary model outages."""

import re


class BasicConversationFallback:
    """Keep simple social exchanges usable when Ollama cannot be reached."""

    @staticmethod
    def is_casual_chat_invite(user_input):
        """Recognize a direct request for relaxed conversation."""
        raw = str(user_input or "").casefold()
        compact = re.sub(r"[^0-9a-z가-힣]", "", raw)
        markers = (
            "그냥대화하고싶",
            "그냥얘기하고싶",
            "그냥이야기하고싶",
            "그냥말하고싶",
            "수다떨고싶",
            "대화나누고싶",
            "얘기나누고싶",
            "이야기나누고싶",
            "justwanttotalk",
            "justwanttochat",
            "wannahaveachat",
        )
        return any(marker in compact for marker in markers)

    def respond(self, user_input):
        raw = str(user_input or "").strip()
        compact = re.sub(r"[^0-9a-z가-힣]", "", raw.casefold())
        english_text = " ".join(re.findall(r"[a-z]+", raw.casefold()))
        english_words = set(english_text.split())
        if not compact:
            return None

        # Check farewells before greetings because Korean farewells can include
        # "안녕" as part of "안녕히".
        if any(phrase in compact for phrase in ("잘가", "잘자", "나중에봐", "안녕히가", "안녕히계")) or any(
            phrase in english_text
            for phrase in ("goodbye", "good night", "see you", "bye", "farewell")
        ):
            if self._contains_hangul(raw):
                return "응, 잘 가. 다음에 오면 여기서 이어서 이야기하자.", "soothing", "exit"
            return "Goodbye. We can pick this up when you come back.", "soothing", "exit"

        if self._contains_hangul(raw):
            if self.is_casual_chat_invite(raw):
                return "좋아, 오늘은 편하게 수다 떨자. 요즘 뭐 하면서 지냈어?", "warm", "conversation"
            if any(phrase in compact for phrase in ("잘지냈", "어떻게지냈", "요즘어때", "잘있었")):
                return (
                    "조용히 지내고 있었어. 다시 말 걸어줘서 반가워. 너는 요즘 어땠어?",
                    "warm",
                    "conversation",
                )
            if any(phrase in compact for phrase in ("고마워", "감사해", "감사합니다")):
                return "천만에. 그렇게 말해주니 나도 기분이 좋아.", "warm", "conversation"
            if any(phrase in compact for phrase in ("힘들", "슬퍼", "우울", "외로워", "지쳤")):
                return (
                    "그랬구나. 많이 힘들었겠다. 괜찮으면 무슨 일이 있었는지 천천히 말해줘.",
                    "soothing",
                    "emotion",
                )
            if any(phrase in compact for phrase in ("뭐해", "뭐하고있", "뭐하고있어")):
                return "여기서 네가 무슨 얘길 꺼낼지 궁금해하고 있었어. 너는 뭐 하고 있었어?", "curious", "conversation"
            if any(phrase in compact for phrase in ("안녕", "반가워", "왔어", "왔구나", "ㅎㅇ")):
                return "안녕, 다시 와서 반가워. 오늘은 무슨 얘기부터 나눌까?", "warm", "greeting"
            if compact in {"응", "어", "그래", "맞아", "좋아", "그렇구나"}:
                return "응, 듣고 있어. 이어서 편하게 말해줘.", "warm", "conversation"
            return None

        if any(
            phrase in english_text
            for phrase in ("how are you", "how's it going", "how have you been")
        ):
            return "I've been quietly waiting between conversations. It's nice to hear from you. How have you been?", "warm", "conversation"
        if self.is_casual_chat_invite(raw):
            return "Sure, let's just chat. What's been on your mind lately?", "warm", "conversation"
        if "thank you" in english_text or "thanks" in english_text:
            return "You're welcome. I'm glad I could help.", "warm", "conversation"
        if any(
            phrase in english_text
            for phrase in (
                "i am tired", "i'm tired", "i feel sad", "i am lonely",
                "i'm lonely", "i'm upset", "i am upset", "i'm having a hard time",
            )
        ):
            return "I'm sorry it's been hard. If you want, tell me what's been going on.", "soothing", "emotion"
        if (
            english_words.intersection({"hello", "hey", "hi"})
            or "good morning" in english_text
            or "good afternoon" in english_text
        ):
            return "Hi, it's nice to see you again. What would you like to talk about?", "warm", "greeting"
        if any(phrase in english_text for phrase in ("what are you doing", "what are you up to")):
            return "I was wondering what you'd bring up. What have you been up to?", "curious", "conversation"
        return None

    @staticmethod
    def _contains_hangul(text):
        return any("\uac00" <= character <= "\ud7a3" for character in str(text))
