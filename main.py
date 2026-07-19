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