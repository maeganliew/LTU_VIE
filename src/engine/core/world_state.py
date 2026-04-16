from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from src.engine.simulation.agent import AgentState


@dataclass
class WorldState:
    agents: List[AgentState] = field(default_factory=list)
    spawn_count: int = 10
    target_position: Tuple[float, float, float] = (10.0, 0.0, 10.0)
    simulation_speed: float = 1.0
    debug_flags: Dict[str, bool] = field(default_factory=lambda: {
        "pathfinding": False,
        "avoidance": True,
        "profiling": True,
    })