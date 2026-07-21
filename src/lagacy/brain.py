#from ..brain.client import OllamaClient
#from .prompt_builder import PromptBuilder
from src.conversation import ConversationManager
from src.memory import MemoryEngine, MemoryExtractor
from src.memory.search import MemorySearch
from src.emotion import EmotionEngine
from src.goal import GoalEngine

class Brain:
    def __init__(self):
        #self.client = OllamaClient()
        self.emotion = EmotionEngine()
        self.goal = GoalEngine()

        self.memory = MemoryEngine()
        self.extractor = MemoryExtractor()
        self.search = MemorySearch(self.memory)

        #self.builder = PromptBuilder()
        self.conversation = ConversationManager()

    def think(self, emotion, event, user_message):

        print("Emotion :", emotion)

        # 감정 업데이트
        self.emotion.update(user_message)

        # 현재 감정 가져오기
        emotion = self.emotion.get()

        # 사용자 입력에서 기억 추출
        new_memories = self.extractor.extract(user_message)

        # 새로운 기억 저장
        for memory_type, content, importance in new_memories:
            # 프로젝트 목표 설정
            if "Project-LUCID" in user_message:
              self.goal.set_goal("Project-LUCID 개발")

            if not self.memory.exists(content):
                self.memory.add_memory(
                    memory_type,
                    content,
                    importance,
                )

        # 질문과 관련된 기억 검색
        memories = self.search.search(
            user_message
        )
        goal = self.goal.get_goal()
        # 시스템 프롬프트 생성
        system_prompt = self.builder.build(
            emotion,
            memories,
            event,
            goal,
        
        )

        # 시스템 프롬프트 갱신
        self.conversation.update_system(system_prompt)

        # 사용자 입력 추가
        self.conversation.add_user(user_message)

        # AI 호출
        reply = self.client.chat(
            self.conversation.get_messages()
        )

        # AI 답변 저장
        self.conversation.add_assistant(reply)

        return reply