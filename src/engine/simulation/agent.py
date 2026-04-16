from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class AgentState:
    agent_id: int
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target: Tuple[float, float, float] = (10.0, 0.0, 10.0)
    speed: float = 3.0
    active: bool = True
    radius: float = 0.4
    path: list = field(default_factory=list)