from .client import OllamaClient
from .prompt_builder import PromptBuilder
from src.conversation import ConversationManager
from src.memory import MemoryEngine, MemoryExtractor
from src.memory.search import MemorySearch


class Brain:
    def __init__(self):
        self.client = OllamaClient()

        self.memory = MemoryEngine()
        self.extractor = MemoryExtractor()
        self.search = MemorySearch(self.memory)

        self.builder = PromptBuilder()
        self.conversation = ConversationManager()

    def think(self, emotion, event, user_message):

        # 1. 사용자 입력에서 기억 추출
        new_memories = self.extractor.extract(user_message)

        # 2. 새로운 기억 저장
        for memory_type, content, importance in new_memories:

            if not self.memory.exists(content):
                self.memory.add_memory(
                    memory_type,
                    content,
                    importance,
                )

        memories = self.search.search(
         user_message
)

        # 5. 시스템 프롬프트 생성
        system_prompt = self.builder.build(
            emotion,
            memories,
            event,
        )

        # 6. 시스템 프롬프트 갱신
        self.conversation.update_system(system_prompt)

        # 7. 사용자 입력 추가
        self.conversation.add_user(user_message)

        # 8. AI 호출
        reply = self.client.chat(
            self.conversation.get_messages()
        )

        # 9. AI 답변 저장
        self.conversation.add_assistant(reply)

        return reply