from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set

from src.engine.simulation.agent import AgentState


@dataclass
class WorldState:

    # master list of all agents in the world
    agents: List[AgentState] = field(default_factory=list)

    # target agent count — input manager changes this, agent_system syncs to it
    spawn_count: int = 10

    # shared target all agents navigate toward
    target_position: Tuple[float, float, float] = (10.0, 0.0, 10.0)

    # 1.0 = normal speed, 2.0 = twice as fast, 0.5 = half speed
    simulation_speed: float = 1.0

    # "angled" or "topdown" — input manager toggles, renderer reads
    camera_mode: str = "angled"

    debug_flags: Dict[str, bool] = field(default_factory=lambda: {
        "pathfinding": True,
        "avoidance": True,
        "profiling": True,
        "obstacles": True,
    })

    # blocked grid cells as integer (x, z) coordinates
    obstacles: Set[Tuple[int, int]] = field(default_factory=set)