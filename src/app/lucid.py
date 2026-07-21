"""
Project LUCID

Artificial Mind Project

Application : LUCID

Creator : 시드
"""

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


class LucidEngine:

    def __init__(self):

        self.kernel = Kernel()

        # Life
        self.heartbeat = Heartbeat()
        self.consciousness = Consciousness()

        # World
        self.observation = ObservationEngine()

        # Memory
        self.memory = WorkingMemory()

        # Mind
        self.thought = ThoughtEngine()
        self.decision = DecisionEngine()

        # Language
        self.language = LanguageEngine()

        # Life Loop
        self.life = LifeLoop(
            observation_engine=self.observation,
            working_memory=self.memory,
            thought_engine=self.thought,
            decision_engine=self.decision,
            language_engine=self.language,
        )

        self.running = False

    def boot(self):

        Logger.info("Booting LUCID...")

        self.kernel.register(self.heartbeat)
        self.kernel.register(self.consciousness)
        self.kernel.register(self.memory)
        self.kernel.register(self.thought)
        self.kernel.register(self.decision)
        self.kernel.register(self.language)

        self.kernel.start()

        self.running = True

        Logger.info("LUCID is Alive.")

    def run(self):

        while self.running:

            user = input("\n시드 > ").strip()

            if not user:
                continue

            if user.lower() in ("exit", "quit"):

                self.shutdown()
                break

            try:

                reply = self.life.process(user)

                print(f"\nLUCID > {reply}")

            except Exception as e:

                Logger.error(f"LifeLoop Error : {e}")

    def shutdown(self):

        Logger.info("Shutting down LUCID...")

        self.kernel.stop()

        self.running = False