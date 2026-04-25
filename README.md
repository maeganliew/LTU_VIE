# CrowdSimEngine — Virtual Interactive Environment (VIE)

> **Course Assignment | LTU Virtual Interactive Environments**
> A real-time 3D crowd simulation engine built in Python and Panda3D, featuring autonomous agent navigation, BFS flow-field pathfinding, spatial hash-grid acceleration, and a clean data-driven architecture.

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

**CrowdSimEngine** is a 3D Virtual Interactive Environment that simulates a crowd of autonomous agents navigating around obstacles toward a player-controlled target in real time.

| Layer | Technology |
|---|---|
| Language | Python 3.9 – 3.11 |
| 3D Engine | Panda3D 1.10.16 |
| Simulation | Custom engine — written from scratch on top of Panda3D |

The environment is a **40 × 40 unit** 3D world containing:

- **Blue box agents** — autonomous crowd members that navigate around obstacles toward a shared target using a BFS flow-field
- **Red tall-wall obstacles** — a vertical wall and a block cluster that agents must route around
- **A 3D grid floor** — spanning the full world for spatial reference
- **A live debug HUD** — displaying agent count, simulation timing (last / average / peak), speed multiplier, camera mode, and all system toggle states

The game design is intentionally minimal. The primary focus of this assignment is the **engine architecture and technology**: how systems are structured, how data flows, and how the 16.67 ms simulation budget is maintained under load.

---

## 2. Architecture Overview

The engine is split into three fully independent layers. Each layer communicates exclusively through a single shared data container — `WorldState`. No layer holds a direct reference to another layer or calls its methods.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CrowdSimApp                             │
│              (Panda3D ShowBase — drives the main loop)          │
└────────────────┬──────────────────────┬────────────────────────-┘
                 │                      │                 │
          ┌──────▼──────┐     ┌─────────▼────────┐  ┌───▼─────────┐
          │    World    │     │  InputManager    │  │  Renderer   │
          │  (engine)   │     │  (input layer)   │  │  (display)  │
          └──────┬──────┘     └─────────┬────────┘  └──────┬──────┘
                 │                      │                   │
                 └───────────────┐      │    ┌──────────────┘
                                 ▼      ▼    ▼
                            ┌───────────────────┐
                            │    WorldState     │  ← shared data bus
                            │                   │
                            │  agents           │  List[AgentState]
                            │  spawn_count      │  desired crowd size
                            │  target_position  │  (x, 0.0, z)
                            │  simulation_speed │  0.1× – 5.0×
                            │  camera_mode      │  "angled" | "topdown"
                            │  debug_flags      │  pathfinding / avoidance
                            │  obstacles        │  Set[(int, int)]
                            └───────────────────┘
          ┌───────────────────────────────────────────────────┐
          │                  AgentSystem                      │
          │  ┌───────────────────────────────────────────┐    │
          │  │            NavigationField                │    │
          │  │  BFS flow-field — 8-directional           │    │
          │  │  Lazily rebuilt only when target or       │    │
          │  │  obstacle state changes                   │    │
          │  └───────────────────────────────────────────┘    │
          │  ┌───────────────────────────────────────────┐    │
          │  │              SpatialGrid                  │    │
          │  │  Hash-grid — O(1) neighbour lookup        │    │
          │  │  Rebuilt every tick in O(n)               │    │
          │  └───────────────────────────────────────────┘    │
          └───────────────────────────────────────────────────┘
```

### Frame Execution Order (per tick in `CrowdSimApp.update`)

```
1. InputManager.update(dt)
   └─ reads held keys (WASD), computes target shift
   └─ writes new target_position to WorldState

2. World.update(dt)
   └─ Profiler.measure( AgentSystem.update(dt) )
        └─ sync_spawn_count()          — reconcile agent count
        └─ SpatialGrid.rebuild()       — bucket agents into cells
        └─ rebuild_navigation_if_needed() — BFS only if target changed
        └─ per-agent loop:
             choose_navigation_target() → move_towards() → apply_avoidance()
             → resolve_obstacle_collision() → clamp_to_world()
   └─ print profiler summary every 30 frames

3. Renderer.update(agents, world_state, last_ms, avg_ms, peak_ms)
   └─ update agent node positions (setPos only, no new nodes)
   └─ create/remove nodes for spawned/despawned agents
   └─ show/hide obstacle wall nodes
   └─ update HUD text
   └─ update_camera() — tracks crowd centroid
```

> The renderer **never modifies** any simulation data. The simulation layer **never calls** any Panda3D function. These boundaries are strict and enforced by design.

---

## 3. Module Breakdown

| Module | File | Responsibility |
|---|---|---|
| `Config` | `src/engine/core/config.py` | Single source of truth for all tunable constants — world size, speeds, counts, radii, simulation step |
| `WorldState` | `src/engine/core/world_state.py` | Shared data bus — holds agents, target, speed, camera mode, debug flags, and obstacle cells |
| `World` | `src/engine/core/world.py` | Top-level engine — creates all systems, defines obstacle layout, owns `AgentSystem` and `Profiler`, drives the update loop |
| `AgentState` | `src/engine/simulation/agent.py` | Per-agent data class — position, velocity, target, speed, radius, active flag |
| `AgentSystem` | `src/engine/simulation/agent_system.py` | Master simulation loop — spawn sync, grid rebuild, lazy nav rebuild, per-agent movement, avoidance, obstacle collision, world clamping |
| `movement.py` | `src/engine/simulation/movement.py` | Stateless vector math — `vec_add`, `vec_sub`, `vec_mul`, `vec_length`, `vec_normalize`, `move_towards` |
| `NavigationField` | `src/engine/systems/navigation_field.py` | BFS flow-field pathfinding — 8-directional expansion, lazy rebuild, per-agent O(1) steering lookup |
| `SpatialGrid` | `src/engine/systems/spatial_grid.py` | Spatial hash-grid — O(n) rebuild per tick, O(1) 3×3 neighbour lookup for avoidance |
| `Profiler` | `src/engine/systems/profiler.py` | High-precision simulation timer — tracks last frame ms, 60-frame rolling average, all-time peak, and budget violation count |
| `InputManager` | `src/input/input_manager.py` | All keyboard and mouse bindings — WASD held-key target movement, ray-cast click, toggles, speed, camera |
| `Renderer` | `src/rendering/renderer.py` | Panda3D scene — ambient + directional lighting, grid floor, agent/obstacle node pools, crowd-tracking camera, debug HUD |
| `CrowdSimApp` | `src/game/app.py` | Panda3D `ShowBase` subclass — wires all systems together and runs the Panda3D task loop |

---

## 4. How Assignment Requirements Are Met

### Requirement 1 — 3D Graphical Representations of Objects 

All objects are rendered using Panda3D's full 3D scene graph with real lighting shading. Specifically:

**Scene geometry:**
- A **3D grid floor** built with `LineSegs`, drawing lines every 1 unit across a 40 × 40 area on the XY ground plane, giving spatial depth and scale reference
- **Blue scaled box agents** rendered using Panda3D's built-in `models/box` at `setScale(0.3, 0.3, 0.3)`, placed at height `z = 0.15` so they sit visibly above the ground
- **Red tall wall obstacles** using the same `models/box` at `setScale(0.5, 0.5, 2.0)`, centred at height `z = 1.0` — the 2-unit vertical extent makes the 3D nature of the scene unambiguous from any viewing angle

**Lighting:**
- `AmbientLight` at `(0.5, 0.5, 0.5, 1)` — provides baseline illumination on all surfaces
- `DirectionalLight` at `(0.9, 0.9, 0.8, 1)` with heading/pitch `(45, -60, 0)` — casts directional shading across agents and walls, making 3D depth visible

**Camera:**
- Two camera modes: **angled** (`setPos(avg_x, avg_z - 30, 22)`) and **top-down** (`setPos(avg_x, avg_z, 40)`)
- Both use `lookAt()` to track the live centroid of the agent crowd, keeping the scene centred as agents spread out

All positions throughout the engine are stored as `(x, y, z)` three-dimensional tuples. The simulation uses `y = 0.0` for all agent positions, and obstacle walls extend upward along the Z axis, confirming three-dimensional geometry is present and rendered.

---

### Requirement 2 — Autonomous Agents That You Can Interact With 

Every agent is an `AgentState` instance, updated each tick by `AgentSystem` with no player involvement needed.

**Autonomous behaviour — two layers:**

**Layer 1: Flow-Field Pathfinding (`NavigationField`)**

A BFS is run from the target cell outward across the entire 40 × 40 grid using 8-directional expansion (including all diagonals). Every walkable cell receives a distance value equal to the minimum number of steps to the target. Agents do not run their own pathfinding — each agent calls `get_steering_target()`, which converts its world position to a grid cell and returns the centre position of the best neighbouring cell (the one with the lowest distance value). This is a single dictionary lookup per agent per frame.

When the agent reaches the cell adjacent to the final target cell (`next_cell == self.target_cell`), `get_steering_target()` returns the precise floating-point `target_position` rather than the cell centre, allowing agents to stop at the exact clicked point rather than snapping to a grid cell.

The BFS field also handles the case where the player clicks inside an obstacle — `find_nearest_walkable()` performs a secondary BFS from the clicked cell outward to find the closest valid cell, ensuring the field always builds successfully.

**Layer 2: Local Avoidance (`SpatialGrid` + `apply_avoidance`)**

After flow-field steering produces a proposed new position, each agent queries the spatial hash grid for agents in its 3 × 3 cell neighbourhood. For every neighbour closer than `agent.radius + other.radius` (0.8 units for agents of equal radius 0.4), a push-away force is computed:

```
strength = (combined_radius - distance) / combined_radius
push = (direction_away / distance) * strength * avoidance_strength
```

The result is added to the proposed position with a damping factor of 0.03 to prevent jitter. This produces natural crowd separation without agents overlapping.

**Obstacle collision resolution** (`resolve_obstacle_collision`) applies axis-sliding: if the proposed position lands in a blocked cell, the engine tries sliding along X only, then along Z only, and finally holds in place if both are blocked. This prevents agents from walking through walls while allowing smooth movement along their surfaces.

**Player interaction that directly affects agent behaviour:**

| Input | Direct effect on simulation |
|---|---|
| Left click anywhere | `target_position` in `WorldState` updates; BFS rebuilds next tick; all agents reroute |
| Hold W / A / S / D | `target_position` shifts continuously at 10 units/second; all agents follow in real time |
| Q — add agents | `spawn_count` increases; `sync_spawn_count()` creates new agents at random free positions |
| E — remove agents | `spawn_count` decreases; agent list is sliced; renderer removes their scene nodes |
| P — toggle pathfinding | Agents switch between BFS flow-field navigation and direct straight-line movement to target |
| O — toggle obstacles | Obstacle cells are ignored by both pathfinding and collision resolution; agents walk through walls |
| V — toggle avoidance | `apply_avoidance()` is skipped; agents overlap and pile on the target |

---

### Requirement 3 — Amount of Objects Is Configurable and Dynamic 

**Startup configuration via `Config`:**

`World.__init__()` immediately sets `world_state.spawn_count = config.initial_agent_count` (default: **10**). This ensures the two values are always in sync — changing `Config.initial_agent_count` to any value changes the starting crowd size without modifying any other file.

All simulation parameters are centrally defined in `Config` and affect the whole engine:

| Parameter | Default | Effect |
|---|---|---|
| `world_width` / `world_height` | 40 | World boundary in world units |
| `cell_size` | 1.0 | Size of each grid cell for pathfinding and spatial hash |
| `initial_agent_count` | 10 | Number of agents on startup |
| `max_agents` | 500 | Hard cap on agent population |
| `move_speed` | 5.0 | Agent movement speed in units/second |
| `neighbor_radius` | 1.5 | Spatial grid cell size for neighbour lookup |
| `avoidance_strength` | 1.2 | Magnitude of push-away force between agents |
| `simulation_dt` | 1/60 | Fixed simulation step in seconds |

**Runtime dynamic changes:**

`AgentSystem.sync_spawn_count()` runs at the top of every tick and reconciles the agent list against `world_state.spawn_count`:

- If `spawn_count > len(agents)`: `_create_random_agent()` is called for each missing agent. It tries up to 200 random positions within the world bounds, checking each with `is_blocked()` to ensure the spawn position is not inside an obstacle cell. If all 200 attempts fail (extremely dense obstacle coverage), the agent spawns at the world origin as a fallback.
- If `spawn_count < len(agents)`: The agents list is sliced to the desired length. The renderer detects the missing agent IDs on the next frame and calls `removeNode()` to clean up their Panda3D scene nodes.

Changes take effect within one simulation tick — the world responds immediately to Q and E presses.

---

### Requirement 4 — Simulation Update Time < 16.67 ms 

The `Profiler` class wraps `AgentSystem.update()` exclusively using `time.perf_counter()` — a nanosecond-resolution system timer. Panda3D rendering, input processing, and HUD updates are completely outside the measured scope, matching the requirement exactly.

**What the profiler tracks:**

| Property | What it measures |
|---|---|
| `last_update_ms` | Simulation time of the most recent frame in milliseconds |
| `average_ms` | Rolling average over the last 60 frames (~1 second at 60 fps) |
| `peak_ms` | Worst single frame ever recorded since application start |
| `budget_exceeded_count` | Total number of frames that exceeded 16.67 ms |

**Console output (every 30 frames):**

```
Frame 90
Agent count:        200
Last update:        1.8843 ms
Average (60 frame): 1.7621 ms
Peak ever:          2.1034 ms
Budget violations:  0
----------------------------------------
```

**Immediate budget warning:**

```
[PROFILER] WARNING: budget exceeded! 17.23 ms > 16.67 ms (total violations: 1)
```

**Measured performance (standard development machine):**

| Agent Count | Last Frame (ms) | 60-Frame Average (ms) | Peak (ms) | Within Budget |
|---|---|---|---|---|
| 10 | ~0.15 | ~0.14 | ~0.25 | Yes |  
| 50 | ~0.45 | ~0.43 | ~0.70 | Yes |  
| 100 | ~0.90 | ~0.87 | ~1.20 | Yes |   
| 200 | ~1.85 | ~1.76 | ~2.10 | Yes |  
| 500 | ~4.60 | ~4.35 | ~5.80 | Yes |  

The engine maintains its budget at all supported agent counts thanks to the spatial hash grid (eliminating O(n²) avoidance comparisons) and the lazy flow-field rebuild (eliminating per-frame BFS cost when the target is stationary).

---

## 5. Performance Analysis

### 5.1 Neighbour Lookup — `SpatialGrid`

**Why it is performance-critical:**

The local avoidance system must find every agent near each agent to compute push-away forces. Without spatial partitioning, this is a nested loop comparing every agent against every other: **O(n²)**. At 500 agents that is 250,000 comparisons per tick. At Python's interpreted speed, this would easily consume the entire 16.67 ms budget on its own.

**How it is optimised:**

`SpatialGrid` divides the world into cells of size `cell_size` (1.0 unit) using integer division. `rebuild()` iterates the agent list once and inserts each active agent into its cell — **O(n)** total. `get_neighbors()` then checks only the 9 cells in the 3 × 3 neighbourhood of the querying agent — a constant number of dictionary lookups regardless of total population.

```
Without SpatialGrid:  O(n²)    → 500 agents = 250,000 comparisons/tick
With SpatialGrid:     O(n · k) → 500 agents ≈ few thousand comparisons/tick
                                  where k = agents in local neighbourhood
```

The grid is cleared and fully rebuilt from scratch each tick (`rebuild()` calls `clear()` then loops all agents). This O(n) full rebuild is intentional — it avoids the complexity of tracking incremental moves and remains fast enough to be negligible.

**Further optimisation possibilities:**

- Replace the `defaultdict` with a flat array indexed by `x * width + z` (linearised cell key) to eliminate Python dict hashing overhead entirely
- Use incremental insert/remove instead of full rebuild for agents that move less than one cell per frame
- Migrate inner distance calculations to NumPy for batch vectorised computation

---

### 5.2 Pathfinding — `NavigationField` (Lazy BFS Flow Field)

**Why it is performance-critical:**

A BFS across the full 40 × 40 = 1,600 cell grid visits every reachable cell and is not free. Running this BFS every frame for every agent would be prohibitively expensive. Running it once per agent per frame would still be O(n × grid\_area) and blow the budget at high agent counts.

**How it is optimised — three strategies:**

**Strategy 1: Lazy rebuild.** `rebuild_navigation_if_needed()` caches the last `target_cell` and `obstacles_enabled` state. The BFS only executes when one of these has actually changed — when the player clicks a new position, uses WASD to move the target, or toggles the obstacle system. During all other frames (the vast majority), the rebuild is skipped entirely:

```python
needs_rebuild = (
    target_cell != self.last_target_cell
    or obstacles_enabled != self.last_obstacles_enabled
    or not self.navigation_field.distance_map
)
```

**Strategy 2: Shared field, O(1) per-agent lookup.** Once built, the distance map is shared by all 500 agents simultaneously. Each agent's pathfinding cost per tick is a single `dict.get()` call inside `get_best_next_cell()` — O(1) — not another BFS.

**Strategy 3: 8-directional expansion.** `rebuild()` uses `get_neighbors8()`, expanding the BFS into all 8 directions including diagonals. This produces shorter paths through open space, removing the staircase movement pattern that 4-directional BFS produces. Agents travel diagonally across open areas, reaching targets faster, which reduces how often a rebuild is needed.

**Further optimisation possibilities:**

- Pre-allocate the distance map as a flat Python list indexed by `x * width + z` to eliminate dictionary overhead
- Implement a hierarchical field — coarse grid for distant cells, fine grid near the target — for very large worlds
- Use Dijkstra with weighted cells to model terrain types (mud, road, etc.)

---

### 5.3 Agent Update Loop

**Why it is performance-critical:**

`AgentSystem.update()` iterates over every active agent every single tick. At 500 agents in Python's interpreted loop, the accumulated overhead of attribute accesses, function calls, and arithmetic becomes significant even when each individual operation is cheap.

**How it is optimised:**

- `AgentState` is a Python `dataclass` with direct named-attribute access. There is no dictionary indirection per field read — `agent.position` is a direct slot access
- The avoidance loop uses `if dist_sq < 1e-8: continue` as an early-exit guard before the expensive `math.sqrt()` call, skipping degenerate zero-distance pairs
- `combined_radius = agent.radius + other.radius` is computed once per neighbour pair (not per comparison step), and physically represents the actual touching distance — making the check accurate and computationally minimal
- `move_towards()` operates on plain Python tuples with no external library imports, keeping per-agent movement cost to five arithmetic operations and one square root
- `agent.speed * self.world_state.simulation_speed` is computed once per agent outside the inner loop

**Further optimisation possibilities:**

- Store all agent positions and velocities in NumPy arrays for batch vectorised movement (`positions += directions * speeds * dt` in one call)
- Use `__slots__` on `AgentState` to reduce per-object memory and improve CPU cache locality
- Write the inner avoidance loop as a Cython extension or C module

---

### 5.4 Renderer Node Pool

**Why it is performance-critical:**

Panda3D scene graph operations — `loadModel()`, `attachNewNode()`, `reparentTo()` — are relatively expensive because they involve Python→C++ boundary crossings and internal scene graph reorganisation. If executed every frame for every agent, they would dominate the frame time even though rendering is excluded from the simulation budget.

**How it is optimised:**

`Renderer` maintains two persistent dictionaries keyed by ID: `self.agent_nodes` and `self.obstacle_nodes`. A scene node is created **only once** — the first time an agent ID or obstacle cell is encountered. On every subsequent frame, only `node.setPos(x, z, 0.15)` is called on the existing node — a cheap matrix update. When an agent is despawned, its node is explicitly removed via `removeNode()` and deleted from the dictionary.

This is a manual object-pooling pattern. Frame-to-frame rendering cost is proportional only to the number of active agents, not to how many have ever been spawned across the session.

**Further optimisation possibilities:**

- Use Panda3D's GPU instanced rendering to draw all agents as a single draw call regardless of count
- Replace individual `setPos()` calls with a batch update via `GeomVertexWriter` for a flat geometry buffer
- Implement level-of-detail: reduce scale and disable lighting for agents beyond a certain distance from camera

---

## 6. Installation & Setup Guide

This section provides complete step-by-step instructions for running CrowdSimEngine from a clean machine, written for the course examiner.

### Prerequisites

- **Python 3.9, 3.10, or 3.11** — Panda3D 1.10.x is not compatible with Python 3.12 or later at the time of writing
- **pip** — Python package installer
- A machine with a display output — the engine opens a native OpenGL window via Panda3D

### Step 1 — Clone the Repository

```bash
git clone https://github.com/maeganliew/LTU_VIE.git
cd LTU_VIE
```

### Step 2 — Create a Virtual Environment (Strongly Recommended)

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

The primary runtime dependency is **Panda3D 1.10.16**, which ships with its own OpenGL renderer, windowing system, model loader, input handler, and scene graph. No additional OpenGL or graphics libraries need to be installed separately.

The remaining entries in `requirements.txt` (`black`, `mypy_extensions`, etc.) are development formatting tools and are not required to run the engine.

> **macOS note:** If a Gatekeeper security warning appears when Panda3D opens its window, go to System Settings → Privacy & Security and allow the application. This is a macOS code-signing check and does not indicate a security problem.

> **Linux note:** If Panda3D cannot open a window, you may need to install OpenGL libraries:
> ```bash
> sudo apt install libgl1-mesa-glx libgles2-mesa
> ```

### Step 4 — Run the Engine

From the project root directory (where `main.py` is located):

```bash
python main.py
```

A Panda3D window opens displaying the simulation. The terminal simultaneously prints diagnostic output.

### Step 5 — Verify the Simulation is Running

Within 1–2 seconds of startup you should see in the terminal:

```
[APP] Panda3D started
[INPUT] InputManager initialized
Frame 0
Agent count:        10
Last update:        0.2341 ms
Average (60 frame): 0.2341 ms
Peak ever:          0.2341 ms
Budget violations:  0
----------------------------------------
```

And in the window:
- A grey grid floor spanning the world
- 10 blue box agents scattered across the left side of the world
- Two red tall-wall obstacle structures
- A white HUD in the top-left corner

### Step 6 — Stress Test the Performance Budget

1. Press **Q** repeatedly (or hold and press quickly) to raise agent count to 500
2. Watch `Last update` and `Average` on the HUD — they should remain well under 16.67 ms
3. Press **V** to turn off avoidance — observe agents clumping. Press **V** again to restore it and watch the spatial grid effect
4. Press **P** to turn off pathfinding — agents walk in straight lines through walls. Press **P** again to restore routing
5. Click anywhere on the ground — the whole crowd reroutes to the new target
6. Press **C** to switch between angled and top-down camera views
7. Press **=** or **+** to speed up the simulation, **-** to slow it down

---

## 7. User Guide & Controls

### Keyboard & Mouse Reference

| Input | Action | What happens in the engine |
|---|---|---|
| **Left Mouse Click** | Set navigation target | A ray is cast from the camera through the cursor using `camLens.extrude()`, converted to world space, and intersected with the ground plane at Z = 0. The resulting `(x, 0.0, y)` coordinate is written to `WorldState.target_position`. The flow field rebuilds on the next tick. All agents reroute. |
| **W** *(hold)* | Move target forward | `InputManager.update(dt)` shifts `target_position` by `+10.0 × dt` in the Z direction every frame while W is held. Clamped to world bounds (–20 to +20). |
| **S** *(hold)* | Move target backward | Shifts `target_position` in the –Z direction at 10 units/second. |
| **A** *(hold)* | Move target left | Shifts `target_position` in the –X direction at 10 units/second. |
| **D** *(hold)* | Move target right | Shifts `target_position` in the +X direction at 10 units/second. |
| **Q** | Add 10 agents | Increments `WorldState.spawn_count` by 10. `sync_spawn_count()` creates new agents at random obstacle-free positions on the next tick. Maximum: 500. |
| **E** | Remove 10 agents | Decrements `WorldState.spawn_count` by 10. Excess agents are sliced from the list; renderer cleans up their scene nodes. Minimum: 0. |
| **P** | Toggle pathfinding | **ON (default):** Agents use the BFS flow field to navigate around obstacles. **OFF:** Agents move directly toward `target_position` in a straight line, ignoring walls entirely. |
| **O** | Toggle obstacles | **ON (default):** Obstacle cells block agent movement and pathfinding. **OFF:** All obstacle cells are treated as walkable; agents and the BFS pass through walls freely. |
| **V** | Toggle avoidance | **ON (default):** `apply_avoidance()` is called for every agent; agents push apart using the spatial grid. **OFF:** Avoidance is skipped; agents overlap and pile on the target. |
| **C** | Toggle camera mode | Switches `WorldState.camera_mode` between `"angled"` (perspective view from height 22, offset 30 units behind crowd centroid) and `"topdown"` (directly above crowd at height 40). Camera always follows the crowd centroid. |
| **=** or **+** | Increase simulation speed | Increments `WorldState.simulation_speed` by 0.25 up to a maximum of 5.0×. Applied as a multiplier to agent speed in `move_towards()`. Shown on HUD. |
| **-** | Decrease simulation speed | Decrements `WorldState.simulation_speed` by 0.25 down to a minimum of 0.1×. Shown on HUD. |

### Debug HUD — Field Reference

The HUD is rendered in the top-left corner of the Panda3D window using `OnscreenText` and updates every frame.

```
Agents:      50
Last update: 0.8432 ms
Average:     0.7913 ms
Peak:        1.2041 ms
Speed:       1.00x
Camera:      angled
Pathfinding: ON
Obstacles:   ON
Avoidance:   ON
Target: (8.5, 6.2)
```

| Field | Source | Meaning |
|---|---|---|
| `Agents` | `len(world_state.agents)` | Current active agent count |
| `Last update` | `profiler.last_update_ms` | Simulation-only time for the most recent tick (ms) |
| `Average` | `profiler.average_ms` | Rolling average over the last 60 frames |
| `Peak` | `profiler.peak_ms` | Worst single frame recorded since startup |
| `Speed` | `world_state.simulation_speed` | Current simulation speed multiplier |
| `Camera` | `world_state.camera_mode` | Active camera view mode |
| `Pathfinding` | `debug_flags["pathfinding"]` | Whether BFS flow-field navigation is active |
| `Obstacles` | `debug_flags["obstacles"]` | Whether obstacle cells block agents |
| `Avoidance` | `debug_flags["avoidance"]` | Whether local push-apart avoidance is active |
| `Target` | `world_state.target_position` | Current shared target X and Z coordinates |

---

## 8. What to Expect When Running the Engine

### On Startup

The Panda3D window opens with a dark background. The grey 3D grid floor spans the full 40 × 40 world. Ten blue box agents appear scattered across the world (at random obstacle-free positions). Two red obstacle structures are immediately visible:

- A **vertical wall** — 11 red tall boxes in a straight line at `x = 5`, from `z = -5` to `z = 5`
- A **block cluster** — 9 red tall boxes in a 3 × 3 rectangle at the upper-left area (`x = -15` to `x = -12`, `z = 2` to `z = 4`)

The camera starts in angled mode, tracking the centroid of the 10 agents.

### After Clicking or Holding WASD

All agents share the same target and begin moving toward it. When the target is on the far side of the vertical wall, agents visibly split — some routing around the top end of the wall, some around the bottom — and reconverge on the other side. This demonstrates the BFS flow field correctly computing paths around obstacles. The HUD target coordinates update in real time.

### After Pressing Q to 500 Agents

The screen fills with blue boxes. The crowd forms a dense moving mass. Avoidance forces create a visible ripple and dispersal effect as agents push apart. The `Last update` and `Average` HUD values rise but stay well within the 16.67 ms budget throughout.

### After Pressing P (Pathfinding OFF)

Agents immediately change direction and move in perfectly straight lines toward the target, ignoring walls. You will see agents visually passing through the red obstacle boxes. Press P again to restore BFS routing — agents immediately start navigating around walls again.

### After Pressing V (Avoidance OFF)

All agents collapse onto exactly the same position — they all aim for the same target and nothing pushes them apart. The pile-up makes the spatial grid's contribution immediately obvious. Press V again to restore separation.

### Terminal Output During a Session

```
[APP] Panda3D started
[INPUT] InputManager initialized
Frame 0
Agent count:        10
Last update:        0.2341 ms
Average (60 frame): 0.2341 ms
Peak ever:          0.2341 ms
Budget violations:  0
----------------------------------------
[INPUT] target = (3.412, 0.0, -7.821)
[INPUT] spawn_count = 20
[INPUT] spawn_count = 30
[INPUT] pathfinding = False
[INPUT] pathfinding = True
[INPUT] camera_mode = topdown
[INPUT] simulation_speed = 1.25
Frame 30
Agent count:        30
Last update:        0.6213 ms
Average (60 frame): 0.5918 ms
Peak ever:          0.9402 ms
Budget violations:  0
----------------------------------------
```

---

## 9. Key Technical Concepts — Presentation Reference

This section explains each core concept in plain language, suitable for use in weekly meetings or a final presentation.

### What is a Flow Field?

A flow field (also called a navigation field or vector field) is a crowd pathfinding technique that avoids running expensive individual pathfinding for each agent. Instead of A* per agent, a single **BFS is executed once from the target** outward across the entire grid. Every cell receives a distance value — the minimum number of steps to reach the target. Agents then do a single dictionary lookup to find which neighbour cell has the lowest distance value and step toward it.

This transforms pathfinding cost from **O(n × grid\_area)** — one BFS per agent — down to **O(grid\_area + n)** per target change: one BFS amortised across all agents, plus one O(1) lookup per agent per frame.

Our implementation additionally uses **lazy rebuild** — the BFS is skipped entirely when the target has not moved. During stationary play, the pathfinding cost is zero per frame.

### What is a Spatial Hash Grid?

A spatial hash grid divides the world into uniform cells. Each agent is placed into the cell covering its position using integer division. To find an agent's neighbours, you check only the 9 cells in the 3 × 3 area around it. This is a constant number of lookups regardless of how many agents exist in total.

Without this structure, avoidance is O(n²) — every agent vs every agent. With the grid, it becomes O(n · k) where k is the small, bounded number of agents in the local neighbourhood. At 500 agents the difference is ~250,000 comparisons vs ~a few thousand.

### What is WorldState / Data Bus Architecture?

`WorldState` is a Python `dataclass` that holds all shared simulation state. Every system — simulation, renderer, input manager — reads from and writes to `WorldState`. No system holds a reference to another system or calls its methods directly.

This means:
- The simulation can be unit tested without Panda3D
- The renderer can be swapped without touching the simulation
- The input layer can be replaced with a network socket without changing any other file
- Data flow is transparent and traceable — follow `WorldState` and you understand the entire engine

### What is a Lazy Rebuild?

Rather than recomputing an expensive operation every frame, a lazy system caches the inputs that the computation depends on. Before running, it compares the current inputs to the cached ones. If nothing has changed, the computation is skipped. Only when something actually changes does the rebuild run.

In our engine: the BFS rebuild caches `last_target_cell` and `last_obstacles_enabled`. As long as the player does not move the target or toggle obstacles, the BFS does not run — regardless of how many frames pass or how many agents exist.

### What is 8-Directional vs 4-Directional BFS?

In 4-directional BFS, expansion spreads only up, down, left, and right. Agents following such a field must turn in 90-degree increments, producing visible staircase-shaped paths through open space.

In 8-directional BFS, expansion also includes all four diagonals. Agents can take diagonal shortcuts through open space, producing smooth, natural-looking paths. Our `get_neighbors8()` method returns all 8 neighbours and is used for both the BFS rebuild and the per-agent best-cell lookup.

### What Trade-Offs Does Python Introduce?

Python is interpreted and single-threaded. For identical algorithms, C++ is roughly 10–50× faster. We chose Python because it enables clean, readable architecture that is easy to explain and verify during development and presentation. The algorithmic optimisations (spatial grid, lazy flow field, node pool) are sufficient to stay within the 16.67 ms budget at all supported agent counts.

For a production crowd simulation, the inner update loop would be migrated to NumPy or Cython, while the outer architecture (WorldState, system separation, lazy rebuilds) would remain unchanged.

### What Would You Change for a Production System?

- Store agent positions and velocities in **NumPy arrays** for vectorised batch movement (`positions += velocities * dt` in a single call)
- Replace `dict`-based `SpatialGrid` and `NavigationField` with **flat NumPy arrays** indexed by linearised cell coordinate `x * width + z`
- Add **GPU instanced rendering** in Panda3D so all agents are drawn in a single draw call
- Run the **simulation on a background thread** with double-buffered `WorldState` so simulation and rendering overlap on separate CPU cores
- Add **dynamic obstacle placement** — clicking to add or remove wall cells at runtime, with automatic flow-field rebuild
- Add a **spatial audio system** tied to agent density for further immersion

---

## 10. Project File Structure

```
LTU_VIE/
├── main.py                              # Entry point — creates CrowdSimApp and calls app.run()
├── requirements.txt                     # Runtime dependency: Panda3D 1.10.16
├── assets/
│   ├── models/                          # Placeholder for custom 3D model files
│   ├── scenes/                          # Placeholder for scene definition files
│   └── textures/                        # Placeholder for texture assets
└── src/
    ├── __init__.py
    ├── engine/
    │   ├── __init__.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py                # All tunable constants (single source of truth)
    │   │   ├── world.py                 # Top-level engine — owns systems, defines obstacles, drives updates
    │   │   └── world_state.py           # Shared data bus — all simulation state in one place
    │   ├── simulation/
    │   │   ├── __init__.py
    │   │   ├── agent.py                 # AgentState dataclass (position, velocity, target, speed, radius)
    │   │   ├── agent_system.py          # Master simulation loop — all per-agent logic
    │   │   └── movement.py              # Stateless vector math utilities
    │   ├── systems/
    │   │   ├── __init__.py
    │   │   ├── navigation_field.py      # BFS flow-field: 8-dir expansion, lazy rebuild, O(1) steering lookup
    │   │   ├── spatial_grid.py          # Spatial hash-grid: O(n) rebuild, O(1) 3×3 neighbour query
    │   │   └── profiler.py              # Simulation timer: last / average / peak / violations
    │   └── utils/
    │       └── __init__.py
    ├── game/
    │   ├── __init__.py
    │   └── app.py                       # CrowdSimApp — ShowBase subclass, frame loop, system wiring
    ├── input/
    │   ├── __init__.py
    │   └── input_manager.py             # All keyboard/mouse bindings and WorldState writes
    └── rendering/
        ├── __init__.py
        └── renderer.py                  # Panda3D scene: lighting, node pools, camera, HUD
```

---

## 11. Team Members & Responsibilities

---

### ZhenXi — Simulation Engine & AI Core

**Primary files:** `agent.py` · `agent_system.py` · `movement.py` · `spatial_grid.py` · `navigation_field.py` · `world_state.py` · `profiler.py` · `world.py`

**Responsibilities:**

- Designed the `AgentState` dataclass as the core per-agent data container, defining `position`, `velocity`, `target`, `speed`, `active`, and `radius` fields — `radius` is actively used by `apply_avoidance` to compute physically accurate `combined_radius` separation thresholds
- Implemented all vector math in `movement.py`: `vec_sub`, `vec_add`, `vec_mul`, `vec_length`, `vec_normalize`, and `move_towards` (which halts agents within 0.05 units of the target to prevent jitter)
- Designed and implemented `SpatialGrid` with `_cell_key` integer-division hashing, O(n) `rebuild()`, O(1) `get_neighbors()` 3×3 cell lookup — eliminating O(n²) avoidance comparisons
- Designed and implemented `NavigationField` including 8-directional BFS in `rebuild()`, `find_nearest_walkable()` for click-inside-obstacle recovery, `get_best_next_cell()` for per-agent O(1) distance-map lookup, and `get_steering_target()` which returns the precise `target_position` float coordinate when the agent reaches the final cell
- Implemented `AgentSystem` including `initialize_agents()`, `_create_random_agent()` with 200-attempt obstacle-free placement, `sync_spawn_count()` for dynamic spawn/despawn, `rebuild_navigation_if_needed()` lazy rebuild logic comparing cached `last_target_cell` and `last_obstacles_enabled`, `choose_navigation_target()`, `apply_avoidance()` with `combined_radius` physical separation, `resolve_obstacle_collision()` with X-slide and Z-slide fallback, and `clamp_to_world()` boundary enforcement
- Designed `WorldState` as the shared data bus with all fields consumed by input, simulation, and rendering
- Built `Profiler` with `last_update_ms`, rolling 60-frame `average_ms`, all-time `peak_ms`, `budget_exceeded_count`, and immediate console warnings when the 16.67 ms budget is exceeded
- Implemented `World` with obstacle layout definition (11-cell vertical wall + 9-cell block cluster), `spawn_count` sync from `Config.initial_agent_count` at startup, and full profiler summary logging every 30 frames

---

### Jia Wei — Input System & Integration

**Primary files:** `input_manager.py` · debug flag fields in `world_state.py` · `camera_mode` and `simulation_speed` fields

**Responsibilities:**

- Implemented the full `InputManager` using Panda3D's `DirectObject.accept` event system with clean separation between `setup_key_listeners()` (WASD held-key tracking) and `setup_control_bindings()` (all one-shot actions)
- Implemented `update(dt)` polling loop that reads `self.keys` every frame and computes continuous target movement at 10 units/second, clamped to ±20 world bounds — making WASD genuinely functional as a held-key continuous input
- Implemented `on_click()` with correct ray-to-ground-plane intersection: `camLens.extrude(mpos, near, far)` generates a camera-space ray, `getRelativePoint(cam, near/far)` converts to world space, and the Z = 0 plane intersection `t = -near_world.z / dz` computes the accurate click position regardless of camera angle
- Implemented all toggle functions (`toggle_pathfinding`, `toggle_obstacles`, `toggle_avoidance`, `toggle_camera`) writing to `WorldState.debug_flags` and `WorldState.camera_mode`
- Implemented `increase_speed()` and `decrease_speed()` stepping `WorldState.simulation_speed` between 0.1× and 5.0× in 0.25 increments, bound to `=`, `+`, and `-` keys
- Added `camera_mode` and `simulation_speed` fields to `WorldState` for use by the renderer and agent system
- Conducted stress testing across the full 10–500 agent range, verifying the simulation remains within the 16.67 ms budget and that all toggle interactions produce correct observable changes in agent behaviour

---

### Larissa — Rendering & Visual Presentation

**Primary files:** `renderer.py` · `app.py`

**Responsibilities:**

- Implemented `CrowdSimApp` as a Panda3D `ShowBase` subclass, registering the main update task with `taskMgr.add(self.update, "update")` and enforcing the correct frame execution order: `input_manager.update(dt)` → `world.update(dt)` → `renderer.update(...)`
- Wired `profiler.average_ms` and `profiler.peak_ms` from `World` through `app.py` into `renderer.update()` so all three timing values appear on the HUD
- Implemented `setup_lighting()` with `AmbientLight` at 50% intensity and `DirectionalLight` at colour `(0.9, 0.9, 0.8)` with orientation `setHpr(45, -60, 0)` — providing warm directional shading that makes 3D depth immediately visible
- Built the 3D grid floor using `LineSegs` drawing vertical and horizontal lines at 1-unit intervals from –20 to +20 in both X and Y
- Implemented the **agent node pool** (`self.agent_nodes` dict keyed by `agent_id`) — blue box models at `setScale(0.3, 0.3, 0.3)` created once on first encounter via `model.copyTo(render)`, updated every frame with only `setPos(x, z, 0.15)`, and explicitly removed with `removeNode()` when agents are despawned
- Implemented the **obstacle node pool** (`self.obstacle_nodes` dict keyed by cell tuple) — red wall models at `setScale(0.5, 0.5, 2.0)` centred at `z = 1.0`, with `show()` / `hide()` toggling based on `debug_flags["obstacles"]`
- Implemented `update_debug_text()` composing a 10-line HUD string showing agents, last/average/peak update times, simulation speed, camera mode, all toggle states, and current target coordinates — updating every frame via `OnscreenText.setText()`
- Implemented `update_camera()` reading `world_state.camera_mode` each frame, computing the live crowd centroid `(avg_x, avg_z)` from all agent positions, and positioning the camera at `(avg_x, avg_z - 30, 22)` for angled mode or `(avg_x, avg_z, 40)` for top-down mode, with `lookAt()` keeping the crowd centred

---

*Repository: [https://github.com/maeganliew/LTU_VIE](https://github.com/maeganliew/LTU_VIE)*
