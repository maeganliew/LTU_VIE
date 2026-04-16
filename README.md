for group - Anything

Tech stack: Python, Panda 3D

# CrowdSimEngine

## ZhenXi - Simulation / AI Core

responsible for:
- maintaining agent state
- updating agent movement every simulation tick
- following world target positions
- handling dynamic spawn/despawn counts
- applying lightweight local avoidance
- using a spatial grid to reduce neighbor lookup cost

The simulation writes updated positions into `WorldState.agents`, which are then consumed by the rendering layer.