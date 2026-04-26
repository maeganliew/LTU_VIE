from panda3d.core import AmbientLight, DirectionalLight, LineSegs, TextNode
from direct.gui.OnscreenText import OnscreenText
from src.engine.simulation.agent import AgentBehavior

# colours for each agent behaviour state
_COLOUR_NAVIGATING = (0.2, 0.6, 1.0, 1)   # blue
_COLOUR_ARRIVED    = (0.2, 0.9, 0.3, 1)   # green
_COLOUR_WANDERING  = (0.9, 0.8, 0.1, 1)   # yellow

class Renderer:
    def __init__(self, base):
        self.base = base
        self.agent_nodes = {}
        self.obstacle_nodes = {}

        # target marker: created once, repositioned every frame
        self.target_marker = None
        
        self.setup_lighting()
        self.create_grid()
        self.create_debug_text()

    def setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor((0.5, 0.5, 0.5, 1))
        ambient_np = self.base.render.attachNewNode(ambient)
        self.base.render.setLight(ambient_np)

        directional = DirectionalLight("directional")
        directional.setColor((0.9, 0.9, 0.8, 1))
        directional_np = self.base.render.attachNewNode(directional)
        directional_np.setHpr(45, -60, 0)
        self.base.render.setLight(directional_np)

    def create_grid(self, size=20, step=1):
        lines = LineSegs()
        lines.setThickness(1.0)
        lines.setColor(0.5, 0.5, 0.5, 1)

        for x in range(-size, size + 1, step):
            lines.moveTo(x, -size, 0)
            lines.drawTo(x, size, 0)

        for y in range(-size, size + 1, step):
            lines.moveTo(-size, y, 0)
            lines.drawTo(size, y, 0)

        node = lines.create()
        grid = self.base.render.attachNewNode(node)
        grid.setPos(0, 0, 0)

    def create_debug_text(self):
        self.debug_text = OnscreenText(
            text="Debug info loading...",
            pos=(-1.3, 0.95),
            scale=0.045,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        
        
    def _update_target_marker(self, target_position):
        
        # draw a bright green box at the current target position.
        # created once, repositioned every frame.
        # makes it obvious where the crowd is navigating toward.
        
        if self.target_marker is None:
            model = self.base.loader.loadModel("models/box")
            model.setScale(0.5, 0.5, 1.0)          # taller than agents so it's visible
            model.setColor(0.1, 1.0, 0.1, 1)       # bright green
            model.reparentTo(self.base.render)
            self.target_marker = model

        tx, _, tz = target_position
        # position the marker centred vertically above ground (half of 1.0 scale)
        self.target_marker.setPos(tx, tz, 0.5)
        
    # HUD
    def update_debug_text(self, world_state, sim_update_ms, avg_ms, peak_ms,
                          timing=None):
        pathfinding = world_state.debug_flags.get("pathfinding", False)
        obstacles   = world_state.debug_flags.get("obstacles",   False)
        avoidance   = world_state.debug_flags.get("avoidance",   False)
        target      = world_state.target_position

        # count agents in each behaviour state
        nav  = sum(1 for a in world_state.agents
                   if a.behavior == AgentBehavior.NAVIGATING)
        arr  = sum(1 for a in world_state.agents
                   if a.behavior == AgentBehavior.ARRIVED)
        wan  = sum(1 for a in world_state.agents
                   if a.behavior == AgentBehavior.WANDERING)

        subsystem_lines = ""
        if timing:
            subsystem_lines = (
                f"Grid rebuild: {timing['grid_rebuild_ms']:.3f} ms\n"
                f"Nav rebuild:  {timing['nav_rebuild_ms']:.3f} ms\n"
                f"Agent loop:   {timing['agent_loop_ms']:.3f} ms\n"
            )

        self.debug_text.setText(
            f"Agents: {len(world_state.agents)}  "
            f"[Nav:{nav} Arr:{arr} Wan:{wan}]\n"
            f"Last:    {sim_update_ms:.3f} ms\n"
            f"Avg:     {avg_ms:.3f} ms\n"
            f"Peak:    {peak_ms:.3f} ms\n"
            f"Speed:   {world_state.simulation_speed:.2f}x\n"
            f"Camera:  {world_state.camera_mode}\n"
            f"Path: {'ON' if pathfinding else 'OFF'}  "
            f"Obs: {'ON' if obstacles else 'OFF'}  "
            f"Avoid: {'ON' if avoidance else 'OFF'}\n"
            f"Target: ({target[0]:.1f}, {target[2]:.1f})\n"
            f"{subsystem_lines}"
            f"--- Legend: Blue=Nav  Green=Arr  Yellow=Wan ---\n"
            f"WASD:move  Q/E:agents  P:path  O:obs  V:avoid\n"
            f"C:camera   +/-:speed   Click:set target"
        )
        
        
    def draw_obstacles(self, obstacles, show_obstacles=True):
        existing_keys = set(self.obstacle_nodes.keys())
        obstacle_keys = set(obstacles)

        # remove nodes for obstacles that no longer exist
        for key in existing_keys - obstacle_keys:
            self.obstacle_nodes[key].removeNode()
            del self.obstacle_nodes[key]

        for cell in obstacles:
            if cell not in self.obstacle_nodes:
                model = self.base.loader.loadModel("models/box")
                # tall wall shape — makes the 3D scene look clearly 3-dimensional
                model.setScale(0.5, 0.5, 2.0)
                model.setColor(0.9, 0.2, 0.2, 1)
                model.reparentTo(self.base.render)
                self.obstacle_nodes[cell] = model

            cx, cz = cell
            node = self.obstacle_nodes[cell]
            # centre the wall cell at height 1.0 (half of the 2.0 scale)
            node.setPos(cx + 0.5, cz + 0.5, 1.0)

            if show_obstacles:
                node.show()
            else:
                node.hide()

    def update(self, agents, world_state=None, sim_update_ms=0.0,
               avg_ms=0.0, peak_ms=0.0, timing=None):
        active_ids = set()

        for agent in agents:
            agent_id = agent.agent_id
            active_ids.add(agent_id)

            # create node the first time we see this agent id
            if agent_id not in self.agent_nodes:
                model = self.base.loader.loadModel("models/box")
                model.setScale(0.3, 0.3, 0.3)
                model.setColor(*_COLOUR_NAVIGATING)
                node = model.copyTo(self.base.render)
                self.agent_nodes[agent_id] = node

            node = self.agent_nodes[agent_id]

            # update position
            x, _, z = agent.position
            node.setPos(x, z, 0.15)

            # update colour to reflect current behaviour state
            # blue=navigating, green=arrived, yellow=wandering
            if agent.behavior == AgentBehavior.NAVIGATING:
                node.setColor(*_COLOUR_NAVIGATING)
            elif agent.behavior == AgentBehavior.ARRIVED:
                node.setColor(*_COLOUR_ARRIVED)
            elif agent.behavior == AgentBehavior.WANDERING:
                node.setColor(*_COLOUR_WANDERING)

        # remove nodes for agents that were despawned
        for stale_id in set(self.agent_nodes.keys()) - active_ids:
            self.agent_nodes[stale_id].removeNode()
            del self.agent_nodes[stale_id]

        if world_state is not None:
            show_obstacles = world_state.debug_flags.get("obstacles", True)
            self.draw_obstacles(world_state.obstacles, show_obstacles=show_obstacles)
            self._update_target_marker(world_state.target_position)
            self.update_debug_text(
                world_state, sim_update_ms, avg_ms, peak_ms, timing
            )
            self.update_camera(agents, world_state.camera_mode)

    def update_camera(self, agents, camera_mode):
        if not agents:
            return

        avg_x = sum(a.position[0] for a in agents) / len(agents)
        avg_z = sum(a.position[2] for a in agents) / len(agents)

        if camera_mode == "angled":
            self.base.camera.setPos(avg_x, avg_z - 30, 22)
            self.base.camera.lookAt(avg_x, avg_z, 0)

        elif camera_mode == "topdown":
            self.base.camera.setPos(avg_x, avg_z, 40)
            self.base.camera.lookAt(avg_x, avg_z, 0)