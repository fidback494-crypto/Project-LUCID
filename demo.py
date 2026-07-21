from src.mind.observation_engine import ObservationEngine
from src.memory.working_memory import WorkingMemory
from src.mind.thought_engine import ThoughtEngine
from src.mind.decision_engine import DecisionEngine

observation = ObservationEngine()
memory = WorkingMemory()
thought = ThoughtEngine()
decision = DecisionEngine()

observation.start()
memory.start()
thought.start()
decision.start()

# 1. 관찰
obs = observation.observe(
    "user",
    "시드가 안녕이라고 말했다."
)

# 2. 단기 기억
memory.add(obs)

# 3. 생각 생성
t = thought.create(
    "사용자에게 인사해야 한다."
)

# 4. 판단
d = decision.decide(t)

print()
print("===== Pipeline =====")
print(obs)
print(t)
print(d)

decision.stop()
thought.stop()
memory.stop()
observation.stop()