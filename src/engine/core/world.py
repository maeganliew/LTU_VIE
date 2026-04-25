from src.engine.core.config import Config
from src.engine.core.world_state import WorldState
from src.engine.simulation.agent_system import AgentSystem
from src.engine.systems.profiler import Profiler


class World:
    def __init__(self):
        self.config = Config()
        self.world_state = WorldState()

        # keep spawn_count in sync with config so changing Config.initial_agent_count
        # actually affects how many agents start in the world
        self.world_state.spawn_count = self.config.initial_agent_count

        self.agent_system = AgentSystem(self.world_state, self.config)
        self.profiler = Profiler()

        # vertical wall obstacle
        for z in range(-5, 6):
            self.world_state.obstacles.add((5, z))

        # small block cluster on the left
        for x in range(-15, -12):
            for z in range(2, 5):
                self.world_state.obstacles.add((x, z))

        self.agent_system.initialize_agents()

        self.frame_count = 0

    def update(self, dt):
        self.profiler.measure(self.agent_system.update, self.config.simulation_dt)

        # print performance summary every 30 frames
        if self.frame_count % 30 == 0:
            print(f"Frame {self.frame_count}")
            print(f"Agent count:        {len(self.world_state.agents)}")
            print(f"Last update:        {self.profiler.last_update_ms:.4f} ms")
            print(f"Average (60 frame): {self.profiler.average_ms:.4f} ms")
            print(f"Peak ever:          {self.profiler.peak_ms:.4f} ms")
            print(f"Budget violations:  {self.profiler.budget_exceeded_count}")
            print("-" * 40)

        self.frame_count += 1