from src.core.state import LucidState

print("=" * 40)
print("LUCID AI")
print("=" * 40)

lucid = LucidState()

print(lucid.status())
from src.emotion.emotion import EmotionEngine

emotion = EmotionEngine()

print("\nEmotion Before")
print(emotion.show())

emotion.praise()

print("\nAfter Praise")
print(emotion.show())
from src.memory.memory import MemoryEngine

memory = MemoryEngine()

memory.add_memory(
    "fact",
    "사용자는 고양이를 좋아한다.",
    0.9
)

print()

print("Memory")

for m in memory.get_memories():
    print(m)