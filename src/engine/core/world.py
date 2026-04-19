from src.engine.simulation.agent_system import AgentSystem

class World:
    def __init__(self):
        self.agent_system = AgentSystem()

    def update(self, dt):
        self.agent_system.update(dt)
