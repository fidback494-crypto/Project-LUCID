"""
Project LUCID

Artificial Mind Project

Application : LUCID

Creator : 시드
"""
from src.mind.reasoning_engine import ReasoningEngine
from src.kernel.kernel import Kernel

from src.life.heartbeat import Heartbeat
from src.life.consciousness import Consciousness
from src.life.life_loop import LifeLoop

from src.world.observation_engine import ObservationEngine

from src.memory.working_memory import WorkingMemory

from src.mind.thought_engine import ThoughtEngine
from src.mind.decision_engine import DecisionEngine

from src.language.language_engine import LanguageEngine

from src.utils import Logger
from src.self import SelfModel
from src.mind.reasoning_engine import ReasoningEngine
from src.mind.planning_engine import PlanningEngine


class LucidEngine:

    def __init__(self):

        
        from src.self import SelfModel
        self.self_model = SelfModel()

        self.planning = PlanningEngine()
        
     # Self
        self.self_model = SelfModel()

       # Reasoning
        self.reasoning = ReasoningEngine()
        

        self.kernel = Kernel()


        # Life
        self.heartbeat = Heartbeat()
        self.consciousness = Consciousness()

        # World
        self.observation = ObservationEngine()

        # Memory
        self.memory = WorkingMemory()

        # Mind
        self.reasoning = ReasoningEngine()
        self.thought = ThoughtEngine()
        self.decision = DecisionEngine()

        # Language
        self.language = LanguageEngine()

        # LifeLoop
        self.life = LifeLoop(
        
           observation_engine=self.observation,
           working_memory=self.memory,
           reasoning_engine=self.reasoning,
           thought_engine=self.thought,
           planning_engine=self.planning,
           decision_engine=self.decision,
           language_engine=self.language,
           self_model=self.self_model,
)


        self.running = False

    def boot(self):

        Logger.info("========== LUCID BOOT ==========")

        self.kernel.register(self.heartbeat)
        self.kernel.register(self.consciousness)
        self.kernel.register(self.planning)

        self.kernel.register(self.observation)

        self.kernel.register(self.memory)

        self.kernel.register(self.reasoning)
        self.kernel.register(self.thought)
        self.kernel.register(self.decision)

        self.kernel.register(self.language)

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