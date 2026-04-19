from src.engine.core.config import Config
from src.engine.core.world_state import WorldState
from src.engine.simulation.agent_system import AgentSystem
from src.engine.systems.profiler import Profiler

class World:
    def __init__(self):
        self.config = Config()
        self.world_state = WorldState()
        self.agent_system = AgentSystem(self.world_state, self.config)
        self.profiler = Profiler()

        self.agent_system.initialize_agents()
        self.agent_system.spawn_agents(10)

        self.frame_count = 0

    def update(self, dt):
        # run simulation step
        self.profiler.measure(self.agent_system.update, self.config.simulation_dt)

        # debug print every 30 frames
        if self.frame_count % 30 == 0:
            print(f"Frame {self.frame_count}")
            print(f"Agent count: {len(self.world_state.agents)}")
            print(f"Simulation update time: {self.profiler.last_update_ms:.4f} ms")

            for agent in self.world_state.agents[:3]:
                print(
                    f"Agent {agent.agent_id}: pos={agent.position}, vel={agent.velocity}"
                )
            print("-" * 40)

        self.frame_count += 1
