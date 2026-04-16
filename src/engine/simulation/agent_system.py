from src.engine.simulation.agent import Agent

class AgentSystem:
    def __init__(self):
        self.agents = []

    def spawn_agents(self, count):
        for _ in range(count):
            self.agents.append(Agent((0, 0, 0)))

    def update(self, dt):
        for agent in self.agents:
            agent.position = (
                agent.position[0] + 0.1,
                agent.position[1],
                agent.position[2]
            )