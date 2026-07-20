class MemorySearch:

    def __init__(self, memory_engine):
        self.memory = memory_engine

    def search(self, question):

        memories = []

        question = question.lower()

        if "이름" in question:
            name = self.memory.get_name()

            if name:
                memories.append(
                    f"사용자의 이름은 {name}이다."
                )

        if "동물" in question or "좋아" in question:
            animal = self.memory.get_favorite_animal()

            if animal:
                memories.append(
                    f"사용자가 좋아하는 동물은 {animal}이다."
                )

        if "프로젝트" in question or "개발" in question:
            project = self.memory.get_project()

            if project:
                memories.append(
                    f"사용자의 프로젝트는 {project}이다."
                )

        return memories