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


## Jia Wei — Input / Control / Stress Testing

responsible for:
- capturing keyboard and mouse input
- logging input events
- updating WorldState based on input:

spawn / remove agents
set target positions

- providing controls to adjust simulation load (10 → 500 agents)
- implementing performance tools (FPS, frame time, toggles)

The control system updates WorldState, which is used by simulation and rendering.


## Larissa — Visualization / Rendering

responsible for:
- setting up Panda3D scene (window, camera, lighting, basic floor)
- rendering agents using WorldState.agents
- create and update NodePath objects
- sync positions every frame

handling dynamic rendering:

spawn/despawn visual agents
scale up to 500 agents efficiently

- optimizing rendering using object reuse (pooling)

The rendering system reads from WorldState and displays the simulation visually without modifying any logic.
