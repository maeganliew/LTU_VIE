# CrowdSimEngine — Virtual Interactive Environment (VIE)

> **Course Assignment | LTU Virtual Interactive Environments**
> A real-time 3D crowd simulation engine built with Python and Panda3D, demonstrating autonomous agent navigation, flow-field pathfinding, spatial acceleration structures, and a clean data-driven architecture.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [How Assignment Requirements Are Met](#3-how-assignment-requirements-are-met)
4. [Performance Analysis](#4-performance-analysis)
5. [System Setup & Installation Guide (For the Professor)](#5-system-setup--installation-guide-for-the-professor)
6. [User Guide & Controls](#6-user-guide--controls)
7. [What to Expect When Running the Engine](#7-what-to-expect-when-running-the-engine)
8. [Key Technical Concepts (Presentation Reference)](#8-key-technical-concepts-presentation-reference)
9. [Project File Structure](#9-project-file-structure)
10. [Team Members & Responsibilities](#10-team-members--responsibilities)

---

## 1. Project Overview

**CrowdSimEngine** is a 3D Virtual Interactive Environment that simulates a crowd of autonomous agents navigating around obstacles toward a player-defined target in real time. The project is built using:

- **Python 3.x** — primary language
- **Panda3D 1.10.16** — 3D rendering engine and game loop framework
- **Custom simulation engine** — written entirely from scratch on top of Panda3D

The "game" is a crowd navigation sandbox: you click anywhere in the 3D world to set a target, and all agents (visualised as blue 3D boxes) autonomously navigate toward that point using a **flow-field pathfinding system** (BFS-based), while avoiding each other using a **spatial hash grid** for efficient neighbour lookup. Red boxes represent static obstacles that agents must route around.

The simulation is intentionally kept simple in terms of game design — the focus of this assignment is the **underlying engine technology**: how it is structured, how it performs under load, and how it meets the 16.67 ms simulation budget.

---

## 2. Architecture Overview

The engine is split into three completely independent layers that communicate only through a single shared data container called `WorldState`. This makes the simulation, rendering, and input systems fully decoupled.

```
┌─────────────────────────────────────────────────────────────┐
│                        CrowdSimApp                          │
│              (Panda3D ShowBase – main loop)                 │
└───────────┬───────────────────┬────────────────────────────-┘
            │                   │                   │
     ┌──────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
     │    World    │   │  InputManager   │  │  Renderer   │
     │  (engine)   │   │  (input layer)  │  │  (display)  │
     └──────┬──────┘   └────────┬────────┘  └──────┬──────┘
            │                   │                   │
            └──────────────┐    │    ┌──────────────┘
                           ▼    ▼    ▼
                        ┌─────────────┐
                        │ WorldState  │  ← single shared data bus
                        │  (agents,   │
                        │  target,    │
                        │  obstacles, │
                        │  flags)     │
                        └─────────────┘
            ┌──────────────────────────────────┐
            │           AgentSystem            │
            │  ┌──────────────────────────┐    │
            │  │     NavigationField      │    │
            │  │  (BFS flow-field, lazy   │    │
            │  │   rebuild on change)     │    │
            │  └──────────────────────────┘    │
            │  ┌──────────────────────────┐    │
            │  │      SpatialGrid         │    │
            │  │  (hash-grid for O(1)     │    │
            │  │   neighbour lookup)      │    │
            │  └──────────────────────────┘    │
            └──────────────────────────────────┘
```

### Data Flow Each Frame

1. **InputManager** reads keyboard/mouse → writes intent into `WorldState` (target, spawn count, flags)
2. **World.update()** calls `AgentSystem.update()` which reads `WorldState`, runs simulation, writes updated agent positions back into `WorldState`
3. **Renderer.update()** reads `WorldState.agents` → updates Panda3D scene nodes (no simulation logic)
4. **Profiler** wraps the simulation update call and measures elapsed milliseconds

> The rendering layer **never modifies** simulation state. The simulation layer **never calls** Panda3D functions. These boundaries are enforced by design.

---

## 2.1 Module Breakdown

| Module | File | Purpose |
|---|---|---|
| `Config` | `src/engine/core/config.py` | All tunable constants (world size, agent count, speeds, radii) |
| `WorldState` | `src/engine/core/world_state.py` | Shared data bus — agents list, target, spawn count, debug flags, obstacles |
| `World` | `src/engine/core/world.py` | Top-level engine: owns `AgentSystem`, `Profiler`, defines obstacle layout |
| `AgentState` | `src/engine/simulation/agent.py` | Per-agent data: position, velocity, target, speed, radius, path |
| `AgentSystem` | `src/engine/simulation/agent_system.py` | Master simulation loop: spawn sync, grid rebuild, nav rebuild, move, avoidance, clamp |
| `movement.py` | `src/engine/simulation/movement.py` | Pure vector math helpers and `move_towards` |
| `NavigationField` | `src/engine/systems/navigation_field.py` | BFS flow-field pathfinding — lazily rebuilt only when target or obstacles change |
| `SpatialGrid` | `src/engine/systems/spatial_grid.py` | Hash-grid spatial acceleration for O(1) neighbour lookup during avoidance |
| `Profiler` | `src/engine/systems/profiler.py` | High-precision `time.perf_counter` wrapper — measures simulation tick time in ms |
| `Renderer` | `src/rendering/renderer.py` | Panda3D scene: lighting, grid, agent/obstacle nodes, camera, debug HUD |
| `InputManager` | `src/input/input_manager.py` | Keyboard and mouse bindings via Panda3D's `DirectObject.accept` |
| `CrowdSimApp` | `src/game/app.py` | Panda3D `ShowBase` subclass — wires everything together, runs the task loop |

---

## 3. How Assignment Requirements Are Met

### Requirement 1 — 3D Graphical Representations of Objects ✅

All objects in the simulation are rendered using **Panda3D's 3D scene graph**. The engine loads Panda3D's built-in `models/box` primitive and uses it for both agent representations and obstacle blocks. The scene includes:

- A **3D grid floor** drawn with `LineSegs` across the X-Y plane, providing spatial depth reference
- **Blue scaled boxes** (`setScale(0.3, 0.3, 0.3)`) representing each autonomous agent, positioned in 3D world space
- **Red boxes** (`setScale(0.5, 0.5, 0.5)`) representing static wall obstacles
- **Ambient + Directional lighting** configured via `AmbientLight` and `DirectionalLight` for proper shading depth
- A **camera** that tracks the centroid of the crowd in either angled or top-down view mode

All positions are true 3D coordinates using the `(x, y, z)` tuple format. The simulation uses a flat XZ plane (`y = 0`) but the world, rendering, and coordinate system are fully three-dimensional.

---

### Requirement 2 — Autonomous Agents That You Can Interact With ✅

Every agent is an instance of `AgentState` and is driven by a two-layer autonomous navigation system:

**Layer 1 — Flow-Field Pathfinding (NavigationField)**

A single **BFS (Breadth-First Search) distance map** is computed across the entire grid whenever the player clicks a new target. Every cell in the grid receives a value representing the minimum number of steps to the target. On each simulation tick, every agent queries this map to get its next best grid cell — moving it around walls and obstacles without any per-agent A* cost.

**Layer 2 — Local Avoidance (SpatialGrid)**

After flow-field steering, each agent checks its neighbours using the spatial hash grid. If another agent is within `neighbor_radius`, a push-away force is applied proportional to how close the two agents are. This prevents overlap and produces natural crowd-dispersal behaviour.

**Player Interaction** happens via:

- **Left Mouse Click** — sets the shared `target_position` in `WorldState`, which triggers a flow-field rebuild on the next simulation tick. All agents immediately begin navigating toward the new target.
- **Q / E keys** — dynamically spawns or removes agents in groups of 10 (up to 500), changing the crowd density in real time.
- **P / O / V keys** — toggle pathfinding, obstacle collision, and avoidance systems to observe their individual effects on agent behaviour.

---

### Requirement 3 — Amount of Objects Is Configurable and Dynamic ✅

The system supports dynamic agent population changes at runtime:

- Agent count starts at the value set in `Config.initial_agent_count` (default: **10**)
- Press **Q** to add 10 agents (up to maximum of **500**)
- Press **E** to remove 10 agents (down to **0**)
- `AgentSystem.sync_spawn_count()` is called every tick and reconciles the actual agent list against `WorldState.spawn_count`
- New agents are **spawned at random non-obstacle positions** within the world bounds
- Removed agents are culled from the tail of the list and their Panda3D `NodePath` objects are cleaned up by the renderer
- World dimensions, initial count, max agents, speeds, and radii are all configured centrally in `Config` — changing a single value affects the whole simulation without touching any other file
- Obstacle layout is defined in `World.__init__()` and can be freely edited (a vertical wall + a small block cluster are defined by default)

---

### Requirement 4 — Simulation Update Time < 16.67 ms (Excluding Rendering) ✅

The `Profiler` class wraps the `AgentSystem.update()` call using `time.perf_counter()` (nanosecond-precision timer) and records the elapsed time in milliseconds as `last_update_ms`.

Every 30 frames, the console prints:
```
Frame 90
Agent count: 50
Simulation update time: 0.8432 ms
----------------------------------------
```

The simulation update time is **displayed live** on the debug HUD in the top-left corner of the 3D window. Under typical loads (50–200 agents), the simulation consistently runs well under the 16.67 ms target. At the maximum of 500 agents the simulation remains within budget thanks to the spatial grid optimisation.

> **Important:** The profiler wraps only `AgentSystem.update()` — the simulation logic. Panda3D rendering is completely excluded from this measurement, matching the requirement exactly.

---

## 4. Performance Analysis

### 4.1 Performance-Critical Part 1 — Agent Neighbour Lookup (SpatialGrid)

**Why it is critical:**
Without spatial partitioning, the avoidance system would need to compare every agent against every other agent — an O(n²) operation. At 500 agents this is 250,000 comparisons per tick, which would immediately break the 16.67 ms budget.

**How we optimised it:**
The `SpatialGrid` divides the world into uniform cells of size `cell_size` (default 1.0 unit). Each tick, every agent is bucketed into its corresponding cell using integer division. During avoidance, each agent only checks the 9 cells in its 3×3 neighbourhood — a constant-time lookup regardless of total agent count.

```
Without SpatialGrid:  O(n²)  →  500 agents = 250,000 checks/tick
With SpatialGrid:     O(n·k)  →  500 agents ≈ 500 × ~9 cells ≈ a few thousand checks/tick
```

The grid is rebuilt from scratch every tick (`grid.rebuild(agents)`), which is O(n) — this is acceptable and much cheaper than a naive O(n²) approach.

**Further optimisation possibilities:**
- Use a flat array instead of a Python dict for cell storage (eliminates dict hashing overhead)
- Skip the full rebuild and use incremental insert/remove when agents move small distances
- Use NumPy arrays for vectorised distance calculations

---

### 4.2 Performance-Critical Part 2 — Flow-Field Pathfinding (NavigationField)

**Why it is critical:**
A BFS over the full grid (40×40 = 1,600 cells by default) is expensive. If it ran every frame for every agent, it would dominate the simulation budget completely.

**How we optimised it:**
The `NavigationField` is **lazily rebuilt** — it only recomputes the distance map when the target cell actually changes (player clicks a new position) or when the obstacle toggle flag changes. The `AgentSystem` caches the last target cell and compares it before triggering a rebuild:

```python
needs_rebuild = (
    target_cell != self.last_target_cell
    or obstacles_enabled != self.last_obstacles_enabled
    or not self.navigation_field.distance_map
)
```

Once built, the flow field is shared by **all agents** — each agent just calls `get_steering_target()`, which is a simple dictionary lookup (O(1)) rather than running its own pathfinding. A single BFS amortised across hundreds of agents per tick costs essentially nothing per agent.

**Further optimisation possibilities:**
- Pre-allocate the distance map as a flat array indexed by `(x * width + z)` to avoid dictionary overhead
- Limit BFS to a radius around the target if the world is much larger
- Use Dijkstra with weighted cells for more realistic movement costs

---

### 4.3 Performance-Critical Part 3 — Agent Update Loop

**Why it is critical:**
The main `AgentSystem.update()` loop iterates over every active agent each tick. At 500 agents, Python's interpreted loop overhead itself becomes visible.

**How we optimised it:**
- All per-agent data is stored in plain `dataclass` objects with direct attribute access (no dictionary indirection)
- The avoidance force uses early exits (`if dist_sq < 1e-8: continue`) to skip degenerate cases
- The movement math (`movement.py`) uses simple tuple operations with no external library calls, keeping per-agent overhead minimal
- The navigation field lookup is a single dict `.get()` call per agent

**Further optimisation possibilities:**
- Migrate the agent position and velocity arrays to NumPy for vectorised update in a single operation
- Use `__slots__` on `AgentState` to reduce per-object memory overhead and improve cache locality
- Implement a C extension or use Cython for the inner avoidance loop

---

### 4.4 Performance-Critical Part 4 — Renderer Node Management

**Why it is critical:**
Panda3D's scene graph operations (creating `NodePath` objects, calling `setPos`) are relatively expensive. If node creation happened every frame for every agent the renderer would become the bottleneck.

**How we optimised it:**
The renderer uses an **agent node pool** (`self.agent_nodes` dict keyed by `agent_id`). Nodes are only **created** when an agent ID is first seen, and only **destroyed** when an agent is removed. Every other frame, only `node.setPos()` is called, which is a cheap matrix update on an existing node. This is a manual object-pooling pattern applied to Panda3D scene nodes.

**Further optimisation possibilities:**
- Use Panda3D's `InstancedNode` to render all agents as a single draw call
- Replace the box model with a simpler billboard sprite at high agent counts
- Implement level-of-detail: use simpler geometry for agents far from camera

---

## 5. System Setup & Installation Guide (For the Professor)

This section provides step-by-step instructions for running the CrowdSimEngine from a fresh machine.

### Prerequisites

- **Python 3.9, 3.10, or 3.11** (Panda3D 1.10.x does not support Python 3.12+ at the time of writing)
- **pip** package manager
- A machine with a display (the engine opens a 3D window via Panda3D)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/maeganliew/LTU_VIE.git
cd LTU_VIE
```

### Step 2 — (Recommended) Create a Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS / Linux:
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

The main dependency is **Panda3D 1.10.16**, which bundles its own OpenGL renderer, model loader, and windowing system. All other packages are linting/formatting tools that are optional for running the engine.

> **macOS note:** If you encounter a code-signing warning when Panda3D opens a window, you may need to go to System Preferences → Security & Privacy and allow the application to run.

> **Linux note:** You may need to install `libgl1-mesa-glx` or equivalent OpenGL libraries if they are not already present.

### Step 4 — Run the Engine

From the project root directory:

```bash
python main.py
```

A Panda3D window will open displaying a 3D grid world populated with 10 blue agent boxes and two obstacle structures (a vertical red wall and a small red block cluster).

### Step 5 — Verifying Performance Output

While the simulation runs, the console will print performance data every 30 frames:

```
Frame 0
Agent count: 10
Simulation update time: 0.2341 ms
----------------------------------------
Frame 30
Agent count: 10
Simulation update time: 0.1892 ms
```

The debug HUD in the top-left of the window shows live values for agent count, simulation update time, and the current state of all toggleable systems.

### Step 6 — Stress Testing

To observe the performance optimisations under load:
1. Press **Q** repeatedly to bring the agent count up to 500
2. Watch the simulation update time on the HUD — it should remain well under 16.67 ms
3. Press **V** to toggle avoidance off and on to observe the spatial grid's impact
4. Press **P** to toggle pathfinding off and observe agents moving in a straight line vs navigating around walls
5. Left-click anywhere on the world to redirect the entire crowd

---

## 6. User Guide & Controls

### Complete Keyboard & Mouse Reference

| Input | Action | Effect |
|---|---|---|
| **Left Mouse Click** | Set navigation target | All agents immediately begin pathfinding toward the clicked world position. A BFS flow-field is rebuilt on the next simulation tick. |
| **Q** | Spawn +10 agents | Adds 10 new agents at random free positions within the world. Capped at 500 agents total. |
| **E** | Remove –10 agents | Removes 10 agents from the crowd. Minimum is 0. |
| **P** | Toggle pathfinding | **ON (default):** Agents use the BFS flow-field to navigate around obstacles. **OFF:** Agents move directly toward the target in a straight line, ignoring walls. |
| **O** | Toggle obstacles | **ON (default):** Obstacle collision is active — agents cannot walk through red wall cells. **OFF:** Agents pass through obstacles freely. |
| **V** | Toggle avoidance | **ON (default):** Agents push away from neighbours to avoid overlap. **OFF:** Agents ignore each other, resulting in clumping and overlap. |
| **W / A / S / D** | (Registered — logged) | Key events are captured and logged to the console. Camera movement via WASD can be extended from this binding. |

> **Note on camera:** The camera automatically follows the centroid of the entire crowd. It does not require manual control. As agents spread out toward the target, the camera pans to keep the crowd centred.

### Debug HUD (Top-Left of Window)

The debug overlay displays live information at all times:

```
Agents: 50
Simulation update: 0.8432 ms
Pathfinding: ON
Obstacles: ON
Avoidance: ON
Target: (8.50, 0.00, 6.20)
```

---

## 7. What to Expect When Running the Engine

### On Startup
- A Panda3D window opens (default 800×600, Panda3D title bar)
- A grey grid floor appears on a dark background
- 10 blue boxes (agents) are scattered randomly across the grid, avoiding the two obstacle structures
- Two obstacle structures appear in red: a vertical wall at `x = 5` (cells from `z = -5` to `z = 5`) and a small block cluster at the top-left

### After Clicking
- All agents receive a new target
- The flow-field is rebuilt (BFS from the clicked cell outward across the grid)
- Agents begin moving as a crowd toward the target
- Agents flowing around the red wall obstacle is clearly visible — they reroute around the wall rather than walking through it
- The crowd disperses naturally due to avoidance forces — agents don't pile up on top of each other

### After Pressing Q Multiple Times
- Agent count increases in the HUD and on screen
- The simulation update time increases but should remain comfortably under 16.67 ms even at 500 agents
- The crowd becomes dense and avoidance behaviour becomes more active

### Console Output
The terminal window (where you ran `python main.py`) prints diagnostic information every 30 frames, including the exact simulation update time in milliseconds. Input events (key presses, mouse clicks) are also logged with `[INPUT]` and `[MOUSE]` prefixes.

---

## 8. Key Technical Concepts (Presentation Reference)

This section summarises the concepts most likely to be discussed in a presentation or weekly meeting.

### What is a Flow Field?

A flow field (also called a vector field or navigation field) is a technique used in crowd simulation where **a single BFS is run once from the target cell**, computing the minimum number of steps from every cell in the grid to that target. Instead of running A* for every agent every frame, each agent just looks up its current cell in the pre-computed map and moves to the neighbouring cell with the lowest distance value. This reduces pathfinding cost from **O(n × grid_area)** to **O(grid_area + n)** per target change.

In our engine, `NavigationField.rebuild()` runs the BFS. `NavigationField.get_steering_target()` performs the per-agent lookup.

### What is a Spatial Hash Grid?

A spatial hash grid divides the world into uniform cells. Each entity is "bucketed" into the cell it occupies. To find neighbours of an agent, you only check the 9 cells in the immediate 3×3 area. This reduces neighbour lookup from O(n²) to approximately O(n) overall, because each agent checks only the constant number of nearby cells, not the entire agent list.

In our engine, `SpatialGrid.rebuild()` places all agents into cells each tick. `SpatialGrid.get_neighbors()` returns the agents in the surrounding 3×3 cell area.

### What is WorldState / Data-Oriented Design?

Instead of objects calling methods on each other directly, all shared simulation data is stored in a single `WorldState` object. Each system (simulation, renderer, input) reads from and writes to `WorldState` independently. This makes each system independently testable, makes the data flow transparent, and avoids tight coupling between systems.

### Why Panda3D?

Panda3D is an open-source, production-grade 3D game engine with a Python API, developed by Carnegie Mellon University and Disney. It provides a full scene graph, window management, input handling, model loading, and rendering — allowing us to focus engineering effort on the simulation layer rather than OpenGL boilerplate.

### Why Python?

Python allows rapid development and clean, readable code that makes the architecture easy to understand and present. The primary trade-off is raw performance — a C++ engine would be significantly faster. We address this within Python's constraints using algorithmic optimisations (spatial grid, lazy flow-field rebuild) rather than language-level optimisation.

### What Would You Change for a Production System?

- Migrate the simulation inner loop to **NumPy** or **Cython** for vectorised agent updates
- Replace the Python `dict`-based spatial grid with a flat **NumPy array** indexed by linearised cell coordinates
- Implement **instanced rendering** in Panda3D to draw all agents in a single GPU draw call
- Add **multi-threading**: run simulation on a background thread, rendering on the main thread
- Support **dynamic obstacle addition/removal** at runtime (clicking to place/remove walls)

---

## 9. Project File Structure

```
LTU_VIE/
├── main.py                          # Entry point — instantiates and runs CrowdSimApp
├── requirements.txt                 # Python dependencies (Panda3D 1.10.16)
├── assets/
│   ├── models/                      # Placeholder for custom 3D models
│   ├── scenes/                      # Placeholder for scene definitions
│   └── textures/                    # Placeholder for textures
└── src/
    ├── engine/
    │   ├── core/
    │   │   ├── config.py            # All configurable constants (world size, speeds, counts)
    │   │   ├── world.py             # Top-level engine: owns systems, defines obstacle layout
    │   │   └── world_state.py       # Shared data bus passed between all systems
    │   ├── simulation/
    │   │   ├── agent.py             # AgentState dataclass (position, velocity, target, etc.)
    │   │   ├── agent_system.py      # Master simulation loop (spawn, move, avoidance, pathfinding)
    │   │   └── movement.py          # Pure vector math: add, sub, mul, normalize, move_towards
    │   ├── systems/
    │   │   ├── navigation_field.py  # BFS flow-field pathfinding system
    │   │   ├── spatial_grid.py      # Hash-grid spatial acceleration structure
    │   │   └── profiler.py          # High-precision simulation tick timer
    │   └── utils/                   # Utility placeholder
    ├── game/
    │   └── app.py                   # CrowdSimApp: Panda3D ShowBase subclass, wires all systems
    ├── input/
    │   └── input_manager.py         # Keyboard/mouse bindings and WorldState updates
    └── rendering/
        └── renderer.py              # Panda3D scene: lighting, grid, agent nodes, camera, HUD
```

---

## 10. Team Members & Responsibilities

---

### ZhenXi — Simulation & AI Core

**Primary systems:** `AgentSystem`, `AgentState`, `movement.py`, `SpatialGrid`, `NavigationField`, `WorldState`

**Responsibilities:**
- Designed and implemented the `AgentState` dataclass and the full `AgentSystem` simulation loop
- Implemented `move_towards` and all vector math utilities in `movement.py`
- Built the `SpatialGrid` spatial hash structure for O(1) neighbour lookup during avoidance
- Designed and implemented the `NavigationField` BFS flow-field pathfinding system, including lazy rebuild logic, cell-to-world coordinate mapping, and per-agent steering target queries
- Implemented the local avoidance system (`apply_avoidance`) using spatial grid neighbour forces
- Implemented obstacle collision resolution (`resolve_obstacle_collision`) with axis-sliding fallback
- Implemented dynamic spawn/despawn via `sync_spawn_count()` and random free-position placement
- Designed the `WorldState` shared data bus and `Config` parameter system

---

### Jia Wei — Input, Control & Stress Testing

**Primary systems:** `InputManager`, `WorldState` integration, stress testing, debug flags

**Responsibilities:**
- Implemented the full `InputManager` using Panda3D's `DirectObject.accept` event system
- Defined and wired all keyboard bindings: Q/E (spawn), P (pathfinding), O (obstacles), V (avoidance)
- Implemented left-click mouse picking and world coordinate projection for target setting
- Implemented `spawn_more()` and `spawn_less()` with clamping to valid range (0–500 agents)
- Implemented the `debug_flags` dictionary in `WorldState` and all toggle functions
- Conducted stress testing across agent counts from 10 to 500, validating the 16.67 ms simulation budget
- Verified that all input changes propagate correctly through `WorldState` to both simulation and rendering layers
- Designed the simulation speed multiplier (`world_state.simulation_speed`) for future time-control features

---

### Larissa — Visualisation & Rendering

**Primary systems:** `Renderer`, `CrowdSimApp`, Panda3D scene setup

**Responsibilities:**
- Set up the Panda3D `ShowBase` application in `CrowdSimApp` and wired the main update task
- Implemented `Renderer` class including ambient and directional lighting setup
- Built the 3D grid floor using Panda3D `LineSegs` for spatial reference
- Implemented agent rendering using Panda3D's built-in box model with node pooling (`self.agent_nodes` dict) to avoid per-frame node creation overhead
- Implemented obstacle rendering with dynamic show/hide toggle linked to the obstacles debug flag
- Implemented the debug HUD overlay using `OnscreenText` showing live agent count, simulation time, flag states, and target position
- Implemented crowd-tracking camera with angled and top-down modes that automatically follows the centroid of all agents
- Ensured rendering layer reads exclusively from `WorldState` without modifying any simulation data

---

*Repository: [https://github.com/maeganliew/LTU_VIE](https://github.com/maeganliew/LTU_VIE)*
