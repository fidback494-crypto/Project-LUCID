class GoalEngine:

    def __init__(self):
        self.goal = None

    def set_goal(self, goal):
        self.goal = goal

    def get_goal(self):
        return self.goal

    def has_goal(self):
        return self.goal is not None

    def clear(self):
        self.goal = None