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

        
        # simple vertical wall of blocked cells
        for z in range(-5, 6):
            self.world_state.obstacles.add((5, z))
            
        # small block on left
        for x in range(-15, -12):
            for z in range(2, 5):
                self.world_state.obstacles.add((x, z))
                
        self.agent_system.initialize_agents()
        
        self.frame_count = 0

    def update(self, dt):
        # run simulation step
        self.profiler.measure(self.agent_system.update, self.config.simulation_dt)

        # debug print every 30 frames
        if self.frame_count % 30 == 0:
            print(f"Frame {self.frame_count}")
            print(f"Agent count: {len(self.world_state.agents)}")
            print(f"Simulation update time: {self.profiler.last_update_ms:.4f} ms")

            # for agent in self.world_state.agents[:3]:
            #     print(
            #         f"Agent {agent.agent_id}: pos={agent.position}, vel={agent.velocity}"
            #     )
            print("-" * 40)

        self.frame_count += 1
