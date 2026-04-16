class Renderer:
    def __init__(self):
        self.agent_nodes = []

    def update(self, agents):
        for i, agent in enumerate(agents):
            # update node positions (Panda3D NodePath later)
            pass