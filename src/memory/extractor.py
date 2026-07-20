import re


class MemoryExtractor:

    def extract(self, text):

        memories = []

        # 이름
        m = re.search(r"내 이름은 (.+?)(?:야|입니다|이야)?$", text)

        if m:
            memories.append(
                (
                    "name",
                    m.group(1),
                    1.0,
                )
            )

        # 좋아하는 동물
        m = re.search(r"나는 (.+?)를 좋아해", text)

        if m:
            memories.append(
                (
                    "favorite_animal",
                    m.group(1),
                    0.9,
                )
            )

        # 프로젝트
        if "Project-LUCID" in text:
            memories.append(
                (
                    "project",
                    "Project-LUCID",
                    0.9,
                )
            )

        return memories