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
        "calculator",
        CalculatorTool(),
       )


        
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

        self.kernel.register(self.reasoning)
        self.kernel.register(self.goal)
        self.kernel.register(self.thought)
        self.kernel.register(self.planning)
        self.kernel.register(self.decision)

        self.kernel.register(self.language)

        self.kernel.register(self.reflection)
        self.kernel.register(self.experience)

        self.kernel.start()

        self.running = True

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

                    for memory in self.long_memory.all():
                        print(memory)

                    continue

                if user == "/count":

                    print(f"\nMemory Count : {self.long_memory.count()}")

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

                reply = self.life.process(user)

                print(f"\nLUCID > {reply}")

            except KeyboardInterrupt:

                self.shutdown()
                break

            except Exception as e:

                Logger.error(str(e))

    def shutdown(self):

        Logger.info("Shutting Down...")

        self.kernel.stop()

        self.running = False
