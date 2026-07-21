"""
Attention Module
"""


class Attention:

    def __init__(self):

        self.target = "Project-LUCID"

        self.focus = 1.0

    def set(self, target, focus=1.0):

        self.target = target

        self.focus = focus