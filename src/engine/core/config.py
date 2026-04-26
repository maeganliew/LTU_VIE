from dataclasses import dataclass


@dataclass
class Config:
    # horizontal and vertical size of world and each grid cell is 1 unit wide
    world_width: int = 40
    world_height: int = 40
    cell_size: float = 1.0

    initial_agent_count: int = 10
    max_agents: int = 500

    move_speed: float = 5.0
    neighbor_radius: float = 1.5
    # how strongly agents try to push away neighbours
    avoidance_strength: float = 1.2

    # simulation step
    simulation_dt: float = 1.0 / 60.0
    
    
    # agent behaviour state machine settings
    # how close to the global target position = considered "arrived" (world units)
    arrival_radius: float = 1.5

    # how many seconds an agent waits at the target before it starts wandering
    wander_delay: float = 2.0

    # how far from its current position an agent can pick a wander destination
    wander_radius: float = 5.0