from src.engine.simulation.agent_system import AgentSystem
from src.engine.rendering.renderer import Renderer

class World:
    def __init__(self):
        self.agent_system = AgentSystem()
        self.renderer = Renderer()

    def update(self, dt):
        self.agent_system.update(dt)
        self.renderer.update(self.agent_system.agents)