from dataclasses import dataclass
from typing import Tuple


@dataclass
class AgentState:
    agent_id: int
    
    # 3d x,y,z
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    
    # stores where the agent heading to
    target: Tuple[float, float, float] = (10.0, 0.0, 10.0)
    
    # how fast individual agent move
    speed: float = 3.0
    active: bool = True
    
    # approximate size used for avoidance separation distance
    radius: float = 0.4
    