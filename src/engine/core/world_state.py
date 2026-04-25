from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set

from src.engine.simulation.agent import AgentState


@dataclass
class WorldState:
    
    # master list of all agents in the world
    agents: List[AgentState] = field(default_factory=list)
    
    # jiawei can change the value to increase/decrease agent
    spawn_count: int = 10
    
    # shared target agents move toward
    target_position: Tuple[float, float, float] = (10.0, 0.0, 10.0)
    
    # multiplier for movement speed (1.0 = normal speed 2.0 = twice as fast 0.5 = half speed)
    simulation_speed: float = 1.0
    
    debug_flags: Dict[str, bool] = field(default_factory=lambda: {
        "pathfinding": True,
        "avoidance": True,  # avoidance logic
        "profiling": True,  #show timing info
        "obstacles": True, #toggle obstacle handling on or off
    })
    
    # stores blocked cells as integer grid coordinates
    obstacles: Set[Tuple[int, int]] = field(default_factory=set)