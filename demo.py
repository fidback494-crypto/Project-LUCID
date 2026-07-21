import time

from src.life.heartbeat import Heartbeat
from src.life.consciousness import Consciousness


heartbeat = Heartbeat()
consciousness = Consciousness()

heartbeat.start()
consciousness.start()

for _ in range(5):

    heartbeat.update()
    consciousness.update()

    time.sleep(1)

heartbeat.stop()
consciousness.stop()