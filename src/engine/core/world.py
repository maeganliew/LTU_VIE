from src.engine.simulation.agent_system import AgentSystem

class World:
    def __init__(self):
        self.agent_system = AgentSystem()
        self.agent_system.spawn_agents(10)

    def update(self, dt):
        self.agent_system.update(dt)
