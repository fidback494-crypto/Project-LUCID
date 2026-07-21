from src.world.observation import Observation
from src.mind.reasoning_engine import ReasoningEngine

engine = ReasoningEngine()

obs = Observation(
    source="user",
    content="안녕",
)

reason = engine.process(obs)

print(reason)