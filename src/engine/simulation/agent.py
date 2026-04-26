from dataclasses import dataclass, field
from typing import Tuple
from enum import Enum  


# three states of an agent's autonomous behaviour
class AgentBehavior(Enum):

    # moving toward the global shared target using the flow field
    NAVIGATING = "navigating"
    # reached within arrival_radius of the target, waiting
    ARRIVED    = "arrived"
    # waited long enough, now roaming to a random nearby point
    WANDERING  = "wandering"
    
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
    
    # current autonomous behaviour state
    behavior: AgentBehavior = AgentBehavior.NAVIGATING

    # how many seconds this agent has been in ARRIVED state
    # resets to 0.0 whenever behavior transitions to ARRIVED
    arrived_timer: float = 0.0

    # the random nearby point this agent walks toward in WANDERING state
    # picked fresh each time the agent transitions to WANDERING or reaches its current wander point
    wander_target: Tuple[float, float, float] = field(
        default_factory=lambda: (0.0, 0.0, 0.0)
    )
    