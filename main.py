from src.engine.core.config import Config
from src.engine.core.world_state import WorldState
from src.engine.simulation.agent_system import AgentSystem
from src.engine.systems.profiler import Profiler


def main():
    config = Config()
    world_state = WorldState()
    agent_system = AgentSystem(world_state, config)
    profiler = Profiler()

    agent_system.initialize_agents()

    # 180 simulation steps , at 60 updates per second, that is about 3 seconds of simulation
    for frame in range(180):
        
        # run one simulation update and measure how long it took.
        profiler.measure(agent_system.update, config.simulation_dt)

        # every 30 frames, print debug information
        if frame % 30 == 0:
            print(f"Frame {frame}")
            print(f"Agent count: {len(world_state.agents)}")
            print(f"Simulation update time: {profiler.last_update_ms:.4f} ms")

            # look at only first 3 agents
            for agent in world_state.agents[:3]:
                print(
                    f"Agent {agent.agent_id}: pos={agent.position}, vel={agent.velocity}"
                )
            print("-" * 40)


if __name__ == "__main__":
    main()