# CrowdSimEngine — Virtual Interactive Environment (VIE)

> **Course Assignment | LTU Virtual Interactive Environments**
> A real-time 3D crowd simulation engine built in Python and Panda3D, featuring autonomous agent navigation, BFS flow-field pathfinding, spatial hash-grid acceleration, a three-state agent behaviour machine, and a clean data-driven architecture.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Module Breakdown](#3-module-breakdown)
4. [How Assignment Requirements Are Met](#4-how-assignment-requirements-are-met)
5. [Performance Analysis](#5-performance-analysis)
6. [Installation & Setup Guide](#6-installation--setup-guide)
7. [User Guide & Controls](#7-user-guide--controls)
8. [What to Expect When Running the Engine](#8-what-to-expect-when-running-the-engine)
9. [Key Technical Concepts — Presentation Reference](#9-key-technical-concepts--presentation-reference)
10. [Project File Structure](#10-project-file-structure)
11. [Team Members & Responsibilities](#11-team-members--responsibilities)

---

## 1. Project Overview

**CrowdSimEngine** is a 3D Virtual Interactive Environment that simulates a crowd of autonomous agents navigating around obstacles toward a player-controlled target in real time. Each agent has a three-state behaviour machine — navigating toward the target, arriving and waiting, then wandering autonomously to nearby points — making the crowd feel genuinely alive rather than purely reactive.

| Layer | Technology |
|---|---|
| Language | Python 3.9 – 3.11 |
| 3D Engine | Panda3D 1.10.16 |
| Simulation | Custom engine written from scratch on top of Panda3D |

The environment is a **40 × 40 unit** 3D world containing:

- **Coloured box agents** — blue while navigating, green when arrived, yellow when wandering
- **Red tall-wall obstacles** — a vertical wall and a block cluster that agents route around
- **A green target marker** — appears at the clicked point so it is always clear where agents are heading
- **A 3D grid floor** — spanning the full world for spatial reference
- **A live debug HUD** — showing agent count and behaviour breakdown, per-subsystem timing, toggle states, and a full controls legend

The game design is minimal. The primary focus is the **engine technology**: architecture, performance, and autonomous behaviour.

---

## 2. Architecture Overview

The engine uses three fully independent layers that communicate only through `WorldState` — a single shared data object. No layer holds a reference to any other layer or calls its methods directly.

```
┌──────────────────────────────────────────────────────────────────┐
│                          CrowdSimApp                             │
│               (Panda3D ShowBase — main game loop)                │
└────────────────┬──────────────────────┬─────────────────────────┘
                 │                      │                  │
          ┌──────▼──────┐    ┌──────────▼───────┐  ┌──────▼──────┐
          │    World    │    │  InputManager    │  │  Renderer   │
          │  (engine)   │    │  (input layer)   │  │  (display)  │
          └──────┬──────┘    └──────────┬───────┘  └──────┬──────┘
                 │                      │                   │
                 └──────────────┐       │    ┌──────────────┘
                                ▼       ▼    ▼
                           ┌────────────────────┐
                           │     WorldState     │  ← shared data bus
                           │                    │
                           │  agents            │  List[AgentState]
                           │  spawn_count       │  desired crowd size
                           │  target_position   │  (x, 0.0, z)
                           │  simulation_speed  │  0.1× – 5.0×
                           │  camera_mode       │  "angled" | "topdown"
                           │  debug_flags       │  pathfinding/avoidance/obstacles
                           │  obstacles         │  Set[(int, int)]
                           └────────────────────┘
          ┌──────────────────────────────────────────────────────┐
          │                    AgentSystem                       │
          │  ┌──────────────────────────────────────────────┐    │
          │  │             NavigationField                  │    │
          │  │  BFS flow-field — 8-directional              │    │
          │  │  Lazily rebuilt only when target or          │    │
          │  │  obstacle state changes                      │    │
          │  └──────────────────────────────────────────────┘    │
          │  ┌──────────────────────────────────────────────┐    │
          │  │               SpatialGrid                    │    │
          │  │  Hash-grid — O(n) rebuild, O(1) neighbour   │    │
          │  │  lookup for local avoidance                  │    │
          │  └──────────────────────────────────────────────┘    │
          └──────────────────────────────────────────────────────┘
```

### Frame Execution Order (every tick in `CrowdSimApp.update`)

```
1. InputManager.update(dt)
   └─ reads held WASD keys → shifts target_position
   └─ clamps target to world bounds

   (mouse click fires as a Panda3D event before this step)
   └─ Plane.intersectsLine() ray cast → validates → writes target_position

2. World.update(dt)
   └─ Profiler.measure( AgentSystem.update(dt) )
        └─ sync_spawn_count()             (timed: grid_rebuild_ms)
        └─ SpatialGrid.rebuild()          (timed: nav_rebuild_ms)
        └─ rebuild_navigation_if_needed() (timed: agent_loop_ms)
        └─ detect global target change → wake ARRIVED/WANDERING agents
        └─ per-agent loop:
             _update_agent_behavior() → steering target
             move_towards()           → new position
             apply_avoidance()        → push from neighbours
             resolve_obstacle_collision() → axis-slide wall avoidance
             clamp_to_world()         → boundary enforcement
             relocate_if_inside_obstacle() → safety net
   └─ print per-subsystem breakdown every 30 frames

3. Renderer.update(agents, world_state, last_ms, avg_ms, peak_ms, timing)
   └─ create/update/remove agent box nodes (node pool)
   └─ colour agents by behaviour state (blue/green/yellow)
   └─ create/show/hide obstacle wall nodes
   └─ reposition green target marker
   └─ update HUD text (timing, states, controls legend)
   └─ update_camera() — tracks crowd centroid
```

> The renderer **never modifies** simulation state. The simulation **never calls** any Panda3D function. These boundaries are strictly enforced.

---

## 3. Module Breakdown

| Module | File | Responsibility |
|---|---|---|
| `Config` | `src/engine/core/config.py` | All tunable constants — world size, speeds, counts, radii, behaviour timers |
| `WorldState` | `src/engine/core/world_state.py` | Shared data bus — agents, target, speed, camera, flags, obstacles |
| `World` | `src/engine/core/world.py` | Top-level engine — creates systems, defines obstacles, owns `AgentSystem` and `Profiler`, drives update |
| `AgentBehavior` | `src/engine/simulation/agent.py` | Enum: NAVIGATING / ARRIVED / WANDERING |
| `AgentState` | `src/engine/simulation/agent.py` | Per-agent dataclass — position, velocity, target, speed, radius, behavior, arrived_timer, wander_target |
| `AgentSystem` | `src/engine/simulation/agent_system.py` | Master simulation loop — all movement, avoidance, behaviour state machine, per-subsystem timing |
| `movement.py` | `src/engine/simulation/movement.py` | Stateless vector math — `vec_sub`, `vec_add`, `vec_mul`, `vec_normalize`, `move_towards` |
| `NavigationField` | `src/engine/systems/navigation_field.py` | BFS flow-field — 8-directional, lazy rebuild, O(1) per-agent steering lookup |
| `SpatialGrid` | `src/engine/systems/spatial_grid.py` | Hash-grid — O(n) rebuild per tick, O(1) 3×3 neighbour lookup |
| `Profiler` | `src/engine/systems/profiler.py` | Simulation timer — last/average/peak ms, budget violation count |
| `InputManager` | `src/input/input_manager.py` | All keyboard/mouse bindings — WASD, `Plane.intersectsLine()` click, toggles, speed, camera |
| `Renderer` | `src/rendering/renderer.py` | Panda3D scene — lighting, grid, agent/obstacle node pools, target marker, camera, HUD |
| `CrowdSimApp` | `src/game/app.py` | Panda3D `ShowBase` subclass — wires all systems, drives the task loop |

---

## 4. How Assignment Requirements Are Met

### Requirement 1 — 3D Graphical Representations of Objects 

All objects are rendered using Panda3D's full 3D scene graph with real lighting shading:

- A **3D grid floor** built with `LineSegs`, drawing lines at 1-unit intervals across a 40 × 40 area at Panda3D Z = 0, providing spatial depth and scale reference
- **Coloured scaled box agents** using Panda3D's built-in `models/box` at `setScale(0.3, 0.3, 0.3)`, placed at height `z = 0.15` so they sit above the ground
- **Red tall wall obstacles** at `setScale(0.5, 0.5, 2.0)` centred at `z = 1.0` — the 2-unit vertical extent makes the 3D nature unambiguous from any camera angle
- **A green target marker** at `setScale(0.5, 0.5, 1.0)`, taller than agents, repositioned every frame to the current `target_position`
- `AmbientLight` at 50% intensity and `DirectionalLight` at orientation `(45, -60, 0)` — directional shading makes 3D depth visible on all surfaces
- A **crowd-tracking camera** in either angled mode (`setPos(avg_x, avg_z - 30, 22)`) or top-down mode (`setPos(avg_x, avg_z, 40)`), always pointing at the crowd centroid

All positions are stored as `(x, y, z)` three-dimensional tuples. The simulation uses `y = 0.0` for agent positions and obstacle walls extend upward along Z, confirming genuine three-dimensional geometry.

---

### Requirement 2 — Autonomous Agents That You Can Interact With 

Every agent is an `AgentState` instance driven by a two-layer autonomous system.

**Layer 1 — Three-State Behaviour Machine (`AgentBehavior`)**

Each agent independently transitions through three states:

| State | Colour | What the agent does |
|---|---|---|
| `NAVIGATING` | Blue | Uses the BFS flow field to route around obstacles toward the global target |
| `ARRIVED` | Green | Stops at the target, increments `arrived_timer` each tick |
| `WANDERING` | Yellow | After `wander_delay` seconds, picks a random free point within `wander_radius` and roams there |

Transitions:
- `NAVIGATING → ARRIVED`: distance to target ≤ `arrival_radius` (1.5 units)
- `ARRIVED → WANDERING`: `arrived_timer ≥ wander_delay` (2.0 seconds)
- `WANDERING → WANDERING`: on reaching a wander point, picks a new one using polar coordinates (uniform angle + distance) to avoid corner bias
- Any state `→ NAVIGATING`: when the player moves the global target, all agents are immediately reset to `NAVIGATING`

Wander target selection uses polar coordinates:
```
angle = random(0, 2π)
r = random(1.0, wander_radius)
wx = agent.x + cos(angle) * r
wz = agent.z + sin(angle) * r
```
Up to 50 attempts are made to find a free (non-obstacle) position. The wander target is always clamped to world bounds.

**Layer 2 — Flow-Field Pathfinding (`NavigationField`)**

A BFS runs from the target cell outward in 8 directions across the 40 × 40 grid. Every walkable cell gets a distance value. Agents call `get_steering_target()` — one dictionary lookup — to find the centre of their best next cell. When the agent's next cell is the target cell itself, `get_steering_target()` returns the exact floating-point `target_position` (not the cell centre), so agents stop precisely where the player clicked.

`find_nearest_walkable()` handles clicking inside an obstacle — a secondary BFS expands outward from the click point until a free cell is found, so clicking on a wall always produces valid navigation.

**Layer 3 — Local Avoidance (`SpatialGrid` + `apply_avoidance`)**

After flow-field steering, each agent queries the spatial grid for neighbours within its 3 × 3 cell neighbourhood. Any neighbour closer than `agent.radius + other.radius` (0.8 units for same-size agents) generates a push-away force:

```
strength = (combined_radius - distance) / combined_radius
push = (direction_away / distance) * strength * avoidance_strength
```

Forces are damped by 0.03 to prevent jitter. This layer is completely independent of pathfinding.

**Player interaction that directly affects all agents:**

| Input | Immediate engine effect |
|---|---|
| Left click | `Plane.intersectsLine()` ray cast → valid world coordinate → `target_position` written → all agents reset to NAVIGATING → BFS rebuilds next tick |
| Hold W/A/S/D | `target_position` shifts at 10 units/second → agents continuously reroute |
| Q / E | `spawn_count` changes → `sync_spawn_count()` creates or removes agents on next tick |
| P / O / V | `debug_flags` toggle → affects pathfinding, obstacle collision, and avoidance independently |

---

### Requirement 3 — Amount of Objects Is Configurable and Dynamic 

**At startup:** `World.__init__()` sets `world_state.spawn_count = config.initial_agent_count` (default: 10), so the two are always in sync. Changing `Config.initial_agent_count` changes the starting population.

**At runtime:** `AgentSystem.sync_spawn_count()` runs at the top of every tick:
- If `spawn_count > len(agents)`: `_create_random_agent()` tries up to 200 random positions checking each with `is_blocked()`. Falls back to world origin with a console warning if all attempts fail.
- If `spawn_count < len(agents)`: `world_state.agents = world_state.agents[:desired]` — Python list slicing, O(1). The renderer detects missing IDs and calls `removeNode()` to clean up their Panda3D scene nodes.

**All configurable parameters (in `Config`):**

| Parameter | Default | Effect |
|---|---|---|
| `world_width` / `world_height` | 40 | World boundary in world units |
| `cell_size` | 1.0 | Grid cell size (both pathfinding and spatial hash) |
| `initial_agent_count` | 10 | Starting crowd size |
| `max_agents` | 500 | Hard cap on agent population |
| `move_speed` | 5.0 | Agent movement speed (units/second) |
| `avoidance_strength` | 1.2 | Push-away force magnitude |
| `simulation_dt` | 1/60 | Fixed simulation step size |
| `arrival_radius` | 1.5 | Distance to target that counts as "arrived" |
| `wander_delay` | 2.0 | Seconds to wait at target before wandering |
| `wander_radius` | 5.0 | Maximum wander distance from current position |

Changing any `Config` value affects the whole engine without touching any other file.

---

### Requirement 4 — Simulation Update Time < 16.67 ms 

`Profiler.measure()` wraps `AgentSystem.update()` exclusively using `time.perf_counter()`. Panda3D rendering, input processing, and HUD updates are completely outside the measured scope.

**What the profiler tracks:**

| Property | Description |
|---|---|
| `last_update_ms` | Most recent simulation tick time in milliseconds |
| `average_ms` | Rolling average over the last 60 frames (~1 second) |
| `peak_ms` | Worst single frame ever since startup |
| `budget_exceeded_count` | Frames that exceeded 16.67 ms |

**Console output every 30 frames:**
```
Frame 90
  Agent count:        200
  --- Simulation budget (target < 16.67 ms) ---
  Total last frame:   1.8843 ms
  60-frame average:   1.7621 ms
  Peak ever:          2.1034 ms
  Budget violations:  0
  --- Per-subsystem breakdown ---
  Grid rebuild:       0.1203 ms
  Nav field rebuild:  0.0041 ms
  Agent loop:         1.7599 ms
  ---------------------------------------------
```

**Immediate budget warning:**
```
[PROFILER] WARNING: budget exceeded! 17.23 ms > 16.67 ms (total violations: 1)
```

**Measured performance:**

| Agent Count | Last Frame (ms) | 60-Frame Avg (ms) | Peak (ms) | Within Budget |
|---|---|---|---|---|
| 10 | ~0.15 | ~0.14 | ~0.25 | Yes |
| 50 | ~0.45 | ~0.43 | ~0.70 | Yes |
| 100 | ~0.90 | ~0.87 | ~1.20 | Yes |
| 200 | ~1.85 | ~1.76 | ~2.10 | Yes |
| 500 | ~4.60 | ~4.35 | ~5.80 | Yes |

---

## 5. Performance Analysis

### 5.1 Agent Neighbour Lookup — `SpatialGrid`

**Why it is performance-critical:**
Avoidance requires knowing which agents are near each other. Without spatial partitioning, every agent must be compared to every other agent — O(n²). At 500 agents: 250,000 comparisons per tick, enough to blow the 16.67 ms budget alone.

**How it is optimised:**
`SpatialGrid` divides the world into uniform cells of `cell_size = 1.0` unit. `rebuild()` inserts every active agent into its cell using `int(x // cell_size)` — O(n). `get_neighbors()` checks only the 9 surrounding cells — constant time regardless of population.

```
Without SpatialGrid:  O(n²)    → 500 agents = 250,000 checks/tick
With SpatialGrid:     O(n · k) → 500 agents ≈ a few thousand checks/tick
```

The grid is rebuilt from scratch each tick (O(n)) — intentional, since incremental updates add complexity for minimal gain at these scales.

**Per-subsystem timing shows this:** `grid_rebuild_ms` in the console breakdown tells you exactly how much time this costs each frame.

**Further optimisation possibilities:**
- Replace `defaultdict` with a flat array indexed by `x * width + z` to eliminate Python dict hashing
- Use incremental insert/remove for agents that stay in the same cell between frames
- Vectorise distance calculations with NumPy

---

### 5.2 Pathfinding — `NavigationField` (Lazy BFS Flow Field)

**Why it is performance-critical:**
A BFS over 40 × 40 = 1,600 cells every frame would be far too expensive. Running a separate BFS per agent per frame would be O(n × grid_area) — catastrophic.

**How it is optimised — three strategies:**

**Lazy rebuild:** `rebuild_navigation_if_needed()` caches `last_target_cell` and `last_obstacles_enabled`. The BFS only runs when one of these actually changed. During stationary play the BFS cost per frame is exactly zero:

```python
needs_rebuild = (
    target_cell != self.last_target_cell
    or obstacles_enabled != self.last_obstacles_enabled
    or not self.navigation_field.distance_map
)
```

**Shared field:** The distance map is built once and shared by all 500 agents. Each agent's navigation cost per tick is a single `dict.get()` — O(1), not another BFS.

**8-directional expansion:** `rebuild()` uses `get_neighbors8()`. Diagonal paths allow agents to take shortcuts through open space, producing natural movement and shorter total paths. 4-directional BFS causes visible staircase patterns.

**`nav_rebuild_ms` in the per-subsystem breakdown** shows this is ~0.00 ms on most frames and only spikes on the tick when a rebuild runs.

**Further optimisation possibilities:**
- Pre-allocate the distance map as a flat list indexed by `x * width + z`
- Limit BFS radius for very large worlds
- Use Dijkstra with weighted cells for terrain difficulty

---

### 5.3 Agent Update Loop

**Why it is performance-critical:**
The per-agent loop runs for every agent every tick. At 500 agents in Python's interpreted loop, the cumulative overhead of attribute accesses, function calls, and arithmetic becomes the dominant cost — shown clearly by `agent_loop_ms`.

**How it is optimised:**
- `AgentState` is a `@dataclass` with direct attribute access — no dictionary indirection per field
- `apply_avoidance` uses `if dist_sq < 1e-8: continue` before `math.sqrt()` — the squared check eliminates degenerate pairs without the expensive square root
- `combined_radius = agent.radius + other.radius` is physically correct and computed once per neighbour pair
- `move_towards()` operates on plain tuples with no external library calls
- `_update_agent_behavior()` returns early for ARRIVED state (no movement computed) — idle agents cost almost nothing

**Further optimisation possibilities:**
- Store positions and velocities in NumPy arrays for batch vectorised update
- Use `__slots__` on `AgentState` for cache locality
- Implement the inner avoidance loop in Cython or a C extension

---

### 5.4 Renderer Node Pool

**Why it is performance-critical:**
Panda3D `loadModel()` and `attachNewNode()` are expensive Python-to-C++ operations. Creating a new node for every agent every frame would dominate frame time even though rendering is excluded from the simulation budget.

**How it is optimised:**
`Renderer` maintains `self.agent_nodes` and `self.obstacle_nodes` — dictionaries keyed by ID. Nodes are created **once** on first encounter. Every subsequent frame calls only `node.setPos()` and `node.setColor()` — cheap matrix and colour updates. Despawned agents trigger `removeNode()` and dict removal. This is a manual object-pooling pattern.

**Further optimisation possibilities:**
- GPU instanced rendering: draw all agents in a single draw call
- Level-of-detail: simpler geometry for distant agents
- Batch `setPos` updates via `GeomVertexWriter` for a flat geometry buffer

---

## 6. Installation & Setup Guide

Complete step-by-step instructions for running from a clean machine.

### Prerequisites

- **Python 3.9, 3.10, or 3.11** — Panda3D 1.10.x does not support Python 3.12+
- **pip** — Python package installer
- A machine with a display — the engine opens a native OpenGL window

### Step 1 — Clone the Repository

```bash
git clone https://github.com/maeganliew/LTU_VIE.git
cd LTU_VIE
```

### Step 2 — Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Panda3D bundles its own OpenGL renderer, windowing system, model loader, and input handler. No additional graphics libraries are needed.

> **macOS:** If a Gatekeeper security warning appears, go to System Settings → Privacy & Security and allow the application.

> **Linux:** If the window fails to open: `sudo apt install libgl1-mesa-glx libgles2-mesa`

### Step 4 — Run the Engine

```bash
python main.py
```

### Step 5 — Verify Performance Output

Within 2 seconds, the terminal prints:

```
[APP] Panda3D started
[INPUT] InputManager initialized
Frame 0
  Agent count:        10
  --- Simulation budget (target < 16.67 ms) ---
  Total last frame:   0.2341 ms
  60-frame average:   0.2341 ms
  Peak ever:          0.2341 ms
  Budget violations:  0
  --- Per-subsystem breakdown ---
  Grid rebuild:       0.0312 ms
  Nav field rebuild:  0.1891 ms
  Agent loop:         0.0138 ms
  ---------------------------------------------
```

### Step 6 — Stress Test

1. Press **Q** repeatedly to raise agent count to 500
2. Watch `Total last frame` — it should remain well under 16.67 ms
3. Press **V** to toggle avoidance off and on — observe the spatial grid's effect
4. Press **P** to toggle pathfinding — agents walk through walls when off
5. Left-click anywhere on the ground — a green marker appears and the crowd reroutes
6. Press **C** to switch camera between angled and top-down view

---

## 7. User Guide & Controls

### Keyboard & Mouse Reference

| Input | Action | What happens in the engine |
|---|---|---|
| **Left Click** | Set navigation target | `Plane.intersectsLine()` ray cast from camera through cursor hits ground plane (Z = 0). Validated to be inside world bounds. Coordinate written to `WorldState.target_position`. All ARRIVED/WANDERING agents reset to NAVIGATING. BFS rebuilds next tick. |
| **W** *(hold)* | Move target forward | `InputManager.update(dt)` shifts `target_position` Z by `+10.0 × dt` per frame. Clamped to ±20. |
| **S** *(hold)* | Move target backward | Shifts Z by `−10.0 × dt`. |
| **A** *(hold)* | Move target left | Shifts X by `−10.0 × dt`. |
| **D** *(hold)* | Move target right | Shifts X by `+10.0 × dt`. |
| **Q** | Add 10 agents | `spawn_count += 10` (max 500). `sync_spawn_count()` creates agents at random free positions next tick. |
| **E** | Remove 10 agents | `spawn_count -= 10` (min 0). Agent list sliced; renderer removes orphaned nodes. |
| **P** | Toggle pathfinding | **ON:** BFS flow field routes agents around obstacles. **OFF:** Agents aim directly at target in a straight line, ignoring walls. |
| **O** | Toggle obstacles | **ON:** Obstacle cells block movement and pathfinding. **OFF:** All cells treated as walkable. |
| **V** | Toggle avoidance | **ON:** Agents push apart using the spatial grid. **OFF:** Agents overlap and pile onto the target. |
| **C** | Toggle camera | Switches `camera_mode` between `"angled"` (height 22, offset 30 behind crowd) and `"topdown"` (height 40, directly above). Camera always tracks crowd centroid. |
| **=** or **+** | Increase simulation speed | `simulation_speed += 0.25` up to 5.0×. Applied as multiplier to agent speed in `move_towards()`. |
| **-** | Decrease simulation speed | `simulation_speed -= 0.25` down to 0.1×. |

### Debug HUD Reference

The HUD updates every frame in the top-left corner:

```
Agents: 50  [Nav:30 Arr:12 Wan:8]
Last:    0.843 ms
Avg:     0.791 ms
Peak:    1.204 ms
Speed:   1.00x
Camera:  angled
Path: ON  Obs: ON  Avoid: ON
Target: (8.5, 6.2)
Grid rebuild: 0.031 ms
Nav rebuild:  0.004 ms
Agent loop:   0.808 ms
--- Legend: Blue=Nav  Green=Arr  Yellow=Wan ---
WASD:move  Q/E:agents  P:path  O:obs  V:avoid
C:camera   +/-:speed   Click:set target
```

| Field | Source | Meaning |
|---|---|---|
| `Agents: N [Nav:x Arr:y Wan:z]` | `len(agents)` + behavior counts | Total and per-state breakdown |
| `Last` | `profiler.last_update_ms` | Simulation-only time for most recent tick |
| `Avg` | `profiler.average_ms` | Rolling 60-frame average |
| `Peak` | `profiler.peak_ms` | Worst frame since startup |
| `Speed` | `world_state.simulation_speed` | Current time multiplier |
| `Camera` | `world_state.camera_mode` | Active camera view |
| `Path / Obs / Avoid` | `debug_flags` | Current toggle states |
| `Target` | `world_state.target_position` | Current target X and Z |
| `Grid/Nav/Agent` | `agent_system.timing` | Per-subsystem breakdown |

---

## 8. What to Expect When Running the Engine

### On Startup

The Panda3D window opens. Ten blue box agents are scattered randomly across the world. Two red tall-wall obstacle structures are visible:
- **Vertical wall** — 11 red boxes in a line at simulation X = 5, spanning Z = −5 to Z = 5
- **Block cluster** — 9 red boxes in a 3 × 3 rectangle at the upper-left (X = −15 to −12, Z = 2 to 4)

A green target marker sits at the initial target position (10, 0, 10).

### After Clicking or Holding WASD

All agents turn blue (NAVIGATING) and begin routing toward the new target. The green marker moves to the click point. Agents approaching the vertical wall visibly split — some going around the top, some around the bottom — and reconverge. Agents within 1.5 units of the target turn green (ARRIVED) and stop. After 2 seconds, green agents turn yellow (WANDERING) and begin roaming in random directions nearby.

### Toggle Demonstrations

| Key press | What you see |
|---|---|
| **P off** | Agents stop following the wall route and walk in straight lines, passing through obstacles |
| **V off** | All agents collapse onto the same position — crowd becomes a single overlapping pile |
| **O off** | Red walls become passable — agents walk through them and the BFS ignores them |
| **C** | View switches to bird's eye — useful for observing the full crowd spread |

### Console Output

```
[APP] Panda3D started
[INPUT] InputManager initialized
Frame 0  ...
[INPUT] target = (8.52, 0.0, 6.21)
[INPUT] spawn_count = 20
[INPUT] pathfinding = False
[INPUT] pathfinding = True
[INPUT] camera_mode = topdown
[INPUT] simulation_speed = 1.25
Frame 30  ...
```

---

## 9. Key Technical Concepts — Presentation Reference

### What is a Flow Field?

A flow field solves the crowd pathfinding problem without running A* for each agent. One BFS runs from the target cell outward, giving every walkable cell a distance value. Each agent then does one dictionary lookup — "what cell is closest to the target from where I am?" — and steps there. Total pathfinding cost per frame is O(grid_area) amortised across all agents, not O(n × grid_area).

Our implementation is additionally lazy: the BFS only runs when the target cell changes. On most frames the cost is zero.

### What is a Spatial Hash Grid?

A spatial hash grid divides the world into uniform cells. Each agent is bucketed into its cell using integer division. To find an agent's neighbours, only the 9 surrounding cells are checked — a constant number of lookups regardless of total population. This reduces avoidance from O(n²) to approximately O(n).

### What is the Behaviour State Machine?

A state machine is a system where an object can be in one of a fixed set of states, with defined rules for transitioning between them. Our agents have three states: NAVIGATING, ARRIVED, and WANDERING. Each state defines what the agent does and when it transitions to the next state. The machine runs autonomously every tick — the player never needs to control individual agents. This is what makes the agents genuinely "autonomous."

### What is WorldState / Data Bus Architecture?

`WorldState` is a shared dataclass passed to every system. No system holds a reference to another system — they only read and write `WorldState`. This is the reason the simulation, renderer, and input manager are completely decoupled. Each can be tested, modified, or replaced without touching the others.

### What is a Lazy Rebuild?

Instead of recomputing an expensive operation every frame, a lazy system caches the inputs it depends on. Before computing, it checks if inputs changed. If not, it skips. Our BFS caches `last_target_cell` and `last_obstacles_enabled`. If neither changed, the BFS is skipped entirely — regardless of agent count or frame number.

### What Trade-offs Does Python Introduce?

Python is interpreted and single-threaded. The same algorithm in C++ would run 10–50× faster. We chose Python for readable architecture that is easy to explain and verify. The algorithmic optimisations (spatial grid, lazy flow field, node pooling) keep the engine within the 16.67 ms budget at all supported agent counts. For a production system, the inner simulation loop would be migrated to NumPy or Cython while the outer architecture remains unchanged.

---

## 10. Project File Structure

```
LTU_VIE/
├── main.py                              # Entry point: creates CrowdSimApp, calls app.run()
├── requirements.txt                     # Runtime dependency: Panda3D 1.10.16
├── assets/
│   ├── models/                          # Placeholder for custom 3D models
│   ├── scenes/                          # Placeholder for scene definitions
│   └── textures/                        # Placeholder for textures
└── src/
    ├── __init__.py
    ├── engine/
    │   ├── __init__.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py                # All tunable constants (single source of truth)
    │   │   ├── world.py                 # Top-level engine — creates systems, defines obstacles
    │   │   └── world_state.py           # Shared data bus — all simulation state
    │   ├── simulation/
    │   │   ├── __init__.py
    │   │   ├── agent.py                 # AgentBehavior enum + AgentState dataclass
    │   │   ├── agent_system.py          # Full simulation loop with behaviour state machine
    │   │   └── movement.py              # Stateless vector math utilities
    │   ├── systems/
    │   │   ├── __init__.py
    │   │   ├── navigation_field.py      # BFS flow-field: 8-dir, lazy rebuild, O(1) lookup
    │   │   ├── spatial_grid.py          # Hash-grid: O(n) rebuild, O(1) neighbour query
    │   │   └── profiler.py              # Simulation timer: last/avg/peak/violations
    │   └── utils/
    │       └── __init__.py
    ├── game/
    │   ├── __init__.py
    │   └── app.py                       # CrowdSimApp — ShowBase subclass, frame loop
    ├── input/
    │   ├── __init__.py
    │   └── input_manager.py             # All bindings + Plane.intersectsLine() click
    └── rendering/
        ├── __init__.py
        └── renderer.py                  # Scene: lighting, node pools, marker, camera, HUD
```

---

## 11. Team Members & Responsibilities

---

### ZhenXi — Simulation Engine & AI Core

**Primary files:** `agent.py` · `agent_system.py` · `movement.py` · `spatial_grid.py` · `navigation_field.py` · `world_state.py` · `profiler.py` · `world.py`

**Responsibilities:**

- Designed `AgentBehavior` enum (NAVIGATING / ARRIVED / WANDERING) and integrated it into `AgentState` alongside `arrived_timer` and `wander_target` fields
- Implemented all vector math in `movement.py`: `vec_sub`, `vec_add`, `vec_mul`, `vec_length`, `vec_normalize`, `move_towards` (halts at distance < 0.05 to prevent jitter)
- Built `SpatialGrid` with `_cell_key` integer-division hashing, O(n) `rebuild()`, and O(1) `get_neighbors()` 3×3 cell lookup — eliminating O(n²) avoidance comparisons
- Designed and implemented `NavigationField` with 8-directional BFS `rebuild()`, `find_nearest_walkable()` for obstacle-click recovery, `get_best_next_cell()` for O(1) per-agent distance-map lookup, and `get_steering_target()` that returns exact float target_position at the final cell
- Implemented the full three-state behaviour machine in `_update_agent_behavior()`: ARRIVED transition on `arrival_radius` check, timer-based ARRIVED→WANDERING transition, polar-coordinate wander target selection via `_pick_wander_target()` with 50-attempt obstacle-avoidance
- Implemented global-target-change detection (`last_global_target` cache) to wake all ARRIVED/WANDERING agents when the player moves the target
- Implemented per-subsystem timing using `time.perf_counter()` inside `update()` for `grid_rebuild_ms`, `nav_rebuild_ms`, and `agent_loop_ms` — directly supporting the assignment's performance reporting requirement
- Built `Profiler` with `last_update_ms`, rolling 60-frame `average_ms`, all-time `peak_ms`, `budget_exceeded_count`, and immediate console warnings when 16.67 ms is exceeded
- Implemented `AgentSystem` including `initialize_agents()`, `_create_random_agent()` with 200-attempt obstacle-free placement, `sync_spawn_count()` for dynamic spawn/despawn, `apply_avoidance()` with `combined_radius` physical separation, `resolve_obstacle_collision()` with X-slide and Z-slide fallback, `clamp_to_world()` boundary enforcement, and `relocate_if_inside_obstacle()` safety net (actively called after each agent's update)
- Designed `WorldState` as the shared data bus and ensured `spawn_count` is synced from `Config.initial_agent_count` at startup in `World.__init__()`

---

### Jia Wei — Input System & Controls

**Primary files:** `input_manager.py` · `debug_flags`, `camera_mode`, `simulation_speed` fields in `world_state.py`

**Responsibilities:**

- Implemented the full `InputManager` using Panda3D's `DirectObject.accept` event system with `setup_key_listeners()` for WASD held-key tracking and `setup_control_bindings()` for all one-shot actions
- Implemented `update(dt)` polling loop: reads `self.keys` every frame, shifts `target_position` at 10 units/second per held key, clamps to ±20 world bounds, writes back to `WorldState`
- Implemented `on_click()` with `Plane.intersectsLine()` ray-to-ground-plane picking: `camLens.extrude()` generates lens-space ray, `render.getRelativePoint(cam, ...)` converts to world space, `Plane(Vec3(0,0,1), Point3(0,0,0)).intersectsLine()` computes the intersection, result validated against world bounds before writing to `WorldState.target_position` (fixes the edge-clamping bug where clicking near screen edges gave ±20 values)
- Implemented all toggle functions writing to `WorldState.debug_flags` and `WorldState.camera_mode`
- Implemented `increase_speed()` and `decrease_speed()` stepping `WorldState.simulation_speed` between 0.1× and 5.0× in 0.25 increments
- Added `camera_mode`, `simulation_speed` fields to `WorldState`
- Conducted stress testing at 10–500 agents verifying simulation stays within 16.67 ms budget and all toggle interactions produce correct observable changes

---

### Larissa — Rendering & Visual Presentation

**Primary files:** `renderer.py` · `app.py`

**Responsibilities:**

- Implemented `CrowdSimApp` as a Panda3D `ShowBase` subclass, enforcing the correct frame execution order: `input_manager.update(dt)` → `world.update(dt)` → `renderer.update(...)`
- Passed `agent_system.timing` dict from `World` through `app.py` into `renderer.update()` so the HUD displays all three subsystem timing values
- Implemented `setup_lighting()` with `AmbientLight` at 50% intensity and `DirectionalLight` at `setHpr(45, -60, 0)` providing directional shading that makes 3D depth visible
- Built the 3D grid floor using `LineSegs` at 1-unit intervals across the 40 × 40 world at Z = 0
- Implemented the **agent node pool** (`self.agent_nodes` dict keyed by `agent_id`) — blue/green/yellow box models created once, updated with `setPos()` and `setColor()` every frame based on `agent.behavior`, removed with `removeNode()` on despawn
- Implemented the **obstacle node pool** (`self.obstacle_nodes`) — red wall models at `setScale(0.5, 0.5, 2.0)` and `z = 1.0` height, with `show()` / `hide()` toggling from `debug_flags["obstacles"]`
- Implemented `_update_target_marker()` — creates a bright green box at `setScale(0.5, 0.5, 1.0)` once, repositioned every frame to `world_state.target_position`, making the current navigation target visually explicit
- Implemented `update_debug_text()` with all 10+ HUD fields including per-state agent count (`Nav/Arr/Wan`), per-subsystem timing, all toggle states, and a full controls legend at the bottom
- Implemented `update_camera()` reading `world_state.camera_mode` each frame, computing the live crowd centroid from all agent positions, placing the camera in angled mode (`avg_z - 30, height 22`) or top-down mode (`height 40`) with `lookAt()` keeping the crowd centred

---

*Repository: [https://github.com/maeganliew/LTU_VIE](https://github.com/maeganliew/LTU_VIE)*
