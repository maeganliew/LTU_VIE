from dataclasses import dataclass


@dataclass
class Config:
    world_width: int = 40
    world_height: int = 40
    cell_size: float = 1.0

    initial_agent_count: int = 10
    max_agents: int = 500

    move_speed: float = 3.0
    neighbor_radius: float = 1.5
    avoidance_strength: float = 1.2

    simulation_dt: float = 1.0 / 60.0