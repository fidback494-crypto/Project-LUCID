from src.core.state import LucidState
from src.emotion.emotion import EmotionEngine
from src.memory.memory import MemoryEngine

class LucidEngine:

    def __init__(self):
        self.memory = MemoryEngine()
        self.state = LucidState()
        self.emotion = EmotionEngine()