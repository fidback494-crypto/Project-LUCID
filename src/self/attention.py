"""
Attention Module
"""


class Attention:

    def __init__(self):

        self.target = "꿈과 현실의 경계에서 이어지는 대화"

        self.focus = 1.0

    def set(self, target, focus=1.0):

        self.target = target

        self.focus = focus
