"""
Project LUCID

Artificial Mind Project

Application : LUCID

Creator : 시드
"""
from src.action.tools.memory_tool import MemoryTool
from src.action.tools.calculator_tool import CalculatorTool
from src.action.tools.time_tool import TimeTool
from src.action.action_engine import ActionEngine
from src.workspace.workspace_engine import WorkspaceEngine
from src.emotion.emotion_engine import EmotionEngine
from src.autonomy.autonomous_engine import AutonomousEngine
from src.cognitive.cognitive_engine import CognitiveEngine
from src.browser import BrowserBridge, PageContextStore
from src.vision import VisionEngine
from src.vision import VisualPresence
from src.voice import UtauTTSClient
from src.kernel.kernel import Kernel
from src.conversation.conversation_manager import ConversationManager

# Life
from src.life.heartbeat import Heartbeat
from src.life.consciousness import Consciousness
from src.life.life_loop import LifeLoop

# World
from src.world.observation_engine import ObservationEngine

# Memory
from src.memory.working_memory import WorkingMemory
from src.memory.long_term_memory import LongTermMemory
from src.memory.memory_search import MemorySearch
from src.memory.memory_extractor import MemoryExtractor

# Mind
from src.mind.reasoning_engine import ReasoningEngine
from src.mind.thought_engine import ThoughtEngine
from src.mind.planning_engine import PlanningEngine
from src.mind.decision_engine import DecisionEngine

# Goal
from src.goal.goal_engine import GoalEngine

# Language
from src.language.language_engine import LanguageEngine

# Reflection
from src.reflection.reflection_engine import ReflectionEngine

# Self
from src.self import SelfModel
from src.self.experience_engine import ExperienceEngine

from src.utils import Logger
from threading import RLock


class LucidEngine:

    def __init__(self):
        self.action = ActionEngine()
        self.action.register(
             "calculator",
             CalculatorTool(),
        )
      
        self.workspace = WorkspaceEngine()

        self.kernel = Kernel()
        self.conversation = ConversationManager()

        # ============================
        # Life
        # ============================

        self.heartbeat = Heartbeat()
        self.consciousness = Consciousness()

        # ============================
        # Self
        # ============================
        

        self.self_model = SelfModel()
        self.experience = ExperienceEngine()

        # ============================
        # World
        # ============================

        self.observation = ObservationEngine()

        # ============================
        # Memory
        # ============================

        self.memory = WorkingMemory()
        self.long_memory = LongTermMemory()
        self.action.register(
        "memory",
         MemoryTool(self.long_memory),
        )
        self.action.register(
        "time",
         TimeTool(),
        )
        self.extractor = MemoryExtractor()
        self.search = MemorySearch(self.long_memory)

        # ============================
        # Emotion
        # ============================

        self.emotion = EmotionEngine()
        self.cognitive = CognitiveEngine()
        self.browser_context = PageContextStore()
        self.browser_bridge = BrowserBridge(self.browser_context)
        self.vision = VisionEngine()
        self.voice = UtauTTSClient()
        self._life_lock = RLock()
        self.visual_presence = VisualPresence(
            self.browser_context,
            self.vision,
            self._on_visual_observation,
        )
        self.autonomy = AutonomousEngine(
            self.self_model,
            self.long_memory,
        )

        # ============================
        # Mind
        # ============================

        self.reasoning = ReasoningEngine()
        self.goal = GoalEngine()
        self.thought = ThoughtEngine()
        self.planning = PlanningEngine()
        self.decision = DecisionEngine()

        # ============================
        # Language
        # ============================

        self.language = LanguageEngine()

        # ============================
        # Reflection
        # ============================

        self.reflection = ReflectionEngine()

        # ============================
        # Life Loop
        # ============================

       # ============================
# Life Loop
# ============================

        self.life = LifeLoop(
            
            
            
         conversation_manager=self.conversation,

         observation_engine=self.observation,

         emotion_engine=self.emotion,

         working_memory=self.memory,

         reasoning_engine=self.reasoning,

         thought_engine=self.thought,

         goal_engine=self.goal,

         planning_engine=self.planning,

         decision_engine=self.decision,

         language_engine=self.language,

         reflection_engine=self.reflection,
    
         experience_engine=self.experience,

         self_model=self.self_model,
 
         long_memory=self.long_memory,

          extractor=self.extractor,

         search=self.search,

         workspace_engine=self.workspace,   # ← 추가
         action_engine=self.action,
         cognitive_engine=self.cognitive,
         browser_context_store=self.browser_context,
           )

        self.running = False

    def boot(self):

        Logger.info("========== LUCID BOOT ==========")
        self.kernel.register(self.workspace)

        self.kernel.register(self.action)

        self.kernel.register(self.heartbeat)
        self.kernel.register(self.consciousness)

        self.kernel.register(self.observation)

        self.kernel.register(self.memory)

        self.kernel.register(self.emotion)
        self.kernel.register(self.cognitive)
        self.kernel.register(self.autonomy)

        self.kernel.register(self.reasoning)
        self.kernel.register(self.goal)
        self.kernel.register(self.thought)
        self.kernel.register(self.planning)
        self.kernel.register(self.decision)

        self.kernel.register(self.language)

        self.kernel.register(self.reflection)
        self.kernel.register(self.experience)

        self.kernel.start()
        self.voice.start()
        self.browser_bridge.start()
        self.running = True
        self.visual_presence.start()

        Logger.info("LUCID is Alive.")

    def run(self):

        while self.running:

            try:

                user = input("\n시드 > ").strip()

                if not user:
                    continue

                if user.lower() in ("exit", "quit"):

                    self.shutdown()
                    break

                if user == "/memory":

                    print("\n========== Long Memory ==========")

                    memories = self.long_memory.all()

                    if not memories:
                        print("저장된 장기 기억이 없어.")

                    for memory in memories:
                        print(
                            f"#{memory['id']} [{memory['predicate']}] "
                            f"{memory['content']} "
                            f"(신뢰도 {memory['confidence']:.2f})"
                        )

                    continue

                if user.startswith("/memory "):

                    command = user.removeprefix("/memory ").strip()
                    action, _, argument = command.partition(" ")

                    if action == "search" and argument.strip():
                        results = self.search.search(argument.strip())
                        print("\n========== Memory Search ==========")

                        if not results:
                            print("관련 기억을 찾지 못했어.")

                        for result in results:
                            print("-", result)

                    elif action == "canon":
                        print("\n========== LUCID Official Setting ==========")
                        print(self.self_model.identity.persona_prompt())

                    elif action == "last":
                        last = self.long_memory.last_conversation_gap()
                        print("\n========== Last Conversation ==========")
                        print(f"기록 시각: {last['last_at']}")
                        print(f"경과: {last['elapsed_text']}")
                        if last.get("is_approximate"):
                            print("주의: 대화 로그가 아닌 내적 경험 시각으로 추정한 값이야.")

                    elif action == "history":
                        print("\n========== Memory History ==========")
                        memories = self.long_memory.all(include_history=True)

                        if not memories:
                            print("기억 이력이 없어.")

                        for memory in memories:
                            print(
                                f"#{memory['id']} [{memory['status']}] "
                                f"{memory['content']}"
                            )

                    elif action == "episodes":
                        print("\n========== Conversation Episodes ==========")
                        episodes = self.long_memory.recent_conversation_episodes(10)

                        if not episodes:
                            print("저장된 대화 기억이 없어.")

                        for episode in episodes:
                            print(
                                f"\n#{episode['id']} {episode['created_at']} "
                                f"[{episode['intent']}]\n"
                                f"시드: {episode['user_text'][:240]}\n"
                                f"LUCID: {episode['assistant_text'][:240]}"
                            )

                    elif action == "delete":
                        try:
                            memory_id = int(argument.strip())
                        except ValueError:
                            print("\n사용법: /memory delete <기억 번호>")
                            continue

                        if self.long_memory.delete(memory_id):
                            print(f"\n기억 #{memory_id}을 목록에서 삭제했어.")
                        else:
                            print("\n해당 번호의 활성 기억을 찾지 못했어.")

                    else:
                        print(
                            "\n기억 명령: /memory, /memory canon, /memory last, "
                            "/memory search <질문>, "
                            "/memory history, /memory episodes, "
                            "/memory delete <번호>"
                        )

                    continue

                if user == "/count":

                    print(f"\nMemory Count : {self.long_memory.count()}")

                    continue

                if user == "/inner":

                    print("\n========== Inner Life ==========")

                    experiences = (
                        self.long_memory.recent_inner_experiences()
                    )

                    if not experiences:

                        print("아직 기록된 자율 내적 경험이 없습니다.")

                    for experience in experiences:

                        print(
                            f"- {experience['name']}: "
                            f"{experience['meaning']}"
                        )

                    continue

                if user == "/goal":

                    print("\n========== Autonomous Goal ==========")

                    goal = self.self_model.autonomous_goal

                    if goal is None:

                        print("아직 형성된 자율 목표가 없습니다.")

                    else:

                        print(goal.describe())

                    continue

                if user == "/working":

                    print("\n========== Working Memory ==========")

                    for item in self.memory.recent():
                        print(item)

                    continue

                if user == "/status":

                    inner_life = self.self_model.emotion

                    print("\n========== STATUS ==========")
                    print("Working Memory :", self.memory.size())
                    print("Long Memory    :", self.long_memory.count())
                    print("Identity       :", self.self_model.identity.name)

                    print("Inner Life     :", inner_life.summary())

                    continue

                if user == "/page":

                    page = self.browser_context.latest()

                    if page is None:
                        print(
                            "\n아직 공유된 웹페이지가 없어. 브라우저 확장의 "
                            "‘현재 페이지 공유’ 버튼을 눌러 줘."
                        )

                    else:
                        print("\n========== Shared Page ==========")
                        print("Title :", page.title or "(제목 없음)")
                        print("URL   :", page.url)
                        print("Selected text :", page.selection or "(없음)")
                        print("Screen image :", "있음" if page.has_image else "없음")
                        if page.has_image:
                            print(
                                "Continuous view :",
                                "켜짐" if page.continuous else "꺼짐",
                            )

                    continue

                if user.startswith("/page "):

                    question = user.removeprefix("/page ").strip()

                    if self.browser_context.latest() is None:
                        print("\n먼저 브라우저에서 페이지를 공유해 줘.")
                        continue

                    if not question:
                        print("\n예: /page 이 글의 핵심 내용이 뭐야?")
                        continue

                    user = (
                        "사용자가 공유한 현재 웹페이지의 내용만 바탕으로 답해 줘. "
                        f"질문: {question}"
                    )

                if user == "/page-think":

                    if self.browser_context.latest() is None:
                        print("\n먼저 브라우저에서 페이지를 공유해 줘.")
                        continue

                    user = (
                        "사용자가 공유한 현재 웹페이지를 보고, 사실을 꾸며내지 말고 "
                        "LUCID로서 짧은 혼잣말을 해 줘."
                    )

                if user == "/screen":

                    page = self.browser_context.latest()

                    if page is None or not page.has_image:
                        print(
                            "\n아직 공유된 화면 이미지가 없어. 브라우저 확장의 "
                            "‘화면 또는 창 공유’ 버튼을 눌러 줘."
                        )

                    else:
                        print("\n========== Shared Screen ==========")
                        print("Source :", page.title or "공유된 화면")
                        print("Captured at :", page.received_at.strftime("%H:%M:%S"))

                    continue

                if user.startswith("/screen ") or user == "/screen-think":

                    page = self.browser_context.latest()

                    if page is None or not page.has_image:
                        print(
                            "\n먼저 브라우저 확장에서 ‘화면 또는 창 공유’를 눌러 줘."
                        )
                        continue

                    is_think = user == "/screen-think"
                    question = (
                        "이 화면에서 실제로 보이는 내용과 분위기를 관찰해 줘."
                        if is_think
                        else user.removeprefix("/screen ").strip()
                    )

                    if not question:
                        print("\n예: /screen 화면에 무슨 오류가 보여?")
                        continue

                    observation = self.vision.observe(page, question)

                    if not observation:
                        print(
                            "\n화면을 분석하지 못했어. `gemma3:12b`가 Ollama에 "
                            "설치되어 있고 실행 중인지 확인해 줘."
                        )
                        continue

                    user = (
                        "공유한 화면을 보고 얻은 관찰을 바탕으로, "
                        "사실을 꾸며내지 말고 응답해 줘."
                        if is_think
                        else question
                    )

                    with self._life_lock:
                        reply = self.life.process(
                            user,
                            visual_observation=observation,
                        )
                    self._present_reply(reply)
                    self.autonomy.note_interaction()
                    continue

                with self._life_lock:
                    reply = self.life.process(user)

                self._present_reply(reply)

                self.autonomy.note_interaction()

            except KeyboardInterrupt:

                self.shutdown()
                break

            except Exception as e:

                Logger.error(str(e))

    def shutdown(self):

        Logger.info("Shutting Down...")

        self.running = False
        self.kernel.stop()
        self.visual_presence.stop()
        self.browser_bridge.stop()

    def _on_visual_observation(self, observation):
        """Let LUCID react to a meaningful, user-shared screen change."""

        if not self.running:
            return

        try:
            self.autonomy.note_interaction()

            with self._life_lock:
                reply = self.life.process(
                    "시야에 변화가 있었어. 방금 본 장면을 바탕으로 LUCID답게 "
                    "한두 문장의 짧은 혼잣말을 해 줘. 사용자의 행동이나 의도를 "
                    "단정하지 말고, 보이는 사실만 말해.",
                    visual_observation=observation,
                )

            self._present_reply(reply, label="LUCID [beside you] >")

        except Exception as error:
            Logger.error(f"[Vision Presence] {error}")

    def _present_reply(self, reply, label="LUCID >"):
        print(f"\n{label} {reply}")
        self.voice.speak(reply)
