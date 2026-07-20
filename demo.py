from src.brain.brain import Brain

brain = Brain()

emotion = {
    "happiness": 60,
    "curiosity": 75,
    "loneliness": 15,
}

memories = [
    "사용자는 고양이를 좋아한다.",
    "사용자는 AI를 직접 만들고 있다."
]

event = "사용자가 인사를 했다."

while True:
    user = input("나 : ")

    if user.lower() == "exit":
        break

    print("\n LUCID 생각 중...")

    reply = brain.think(
     emotion,
   
     event,
     user
    )

    print("\nLUCID :", reply)