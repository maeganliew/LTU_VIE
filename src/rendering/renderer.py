from panda3d.core import AmbientLight, DirectionalLight, LineSegs, TextNode
from direct.gui.OnscreenText import OnscreenText


class Renderer:
    def __init__(self, base):
        self.base = base
        self.agent_nodes = {}
        self.obstacle_nodes = {}
        self.camera_mode = "angled"

        self.setup_lighting()
        self.create_grid()
        self.create_debug_text()

    def setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor((0.6, 0.6, 0.6, 1))
        ambient_np = self.base.render.attachNewNode(ambient)
        self.base.render.setLight(ambient_np)

        directional = DirectionalLight("directional")
        directional.setColor((0.8, 0.8, 0.8, 1))
        directional_np = self.base.render.attachNewNode(directional)
        directional_np.setHpr(45, -45, 0)
        self.base.render.setLight(directional_np)

    def create_grid(self, size=20, step=1):
        lines = LineSegs()
        lines.setThickness(1.0)
        lines.setColor(0.8, 0.8, 0.8, 1)

        # Ground plane should be X-Y plane, with Z fixed at 0
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
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )

    def update_debug_text(self, world_state, sim_update_ms):
        pathfinding = world_state.debug_flags.get("pathfinding", False)
        obstacles = world_state.debug_flags.get("obstacles", False)
        avoidance = world_state.debug_flags.get("avoidance", False)

        target = world_state.target_position
        agent_count = len(world_state.agents)

        debug_message = (
            f"Agents: {agent_count}\n"
            f"Simulation update: {sim_update_ms:.4f} ms\n"
            f"Pathfinding: {'ON' if pathfinding else 'OFF'}\n"
            f"Obstacles: {'ON' if obstacles else 'OFF'}\n"
            f"Avoidance: {'ON' if avoidance else 'OFF'}\n"
            f"Target: ({target[0]:.2f}, {target[1]:.2f}, {target[2]:.2f})"
        )

        self.debug_text.setText(debug_message)

    def draw_obstacles(self, obstacles, show_obstacles=True):
        existing_keys = set(self.obstacle_nodes.keys())
        obstacle_keys = set(obstacles)

        for key in existing_keys - obstacle_keys:
            self.obstacle_nodes[key].removeNode()
            del self.obstacle_nodes[key]

        for cell in obstacles:
            if cell not in self.obstacle_nodes:
                model = self.base.loader.loadModel("models/box")
                model.setScale(0.5, 0.5, 0.5)
                model.setColor(1, 0, 0, 1)
                model.reparentTo(self.base.render)
                self.obstacle_nodes[cell] = model

            cx, cz = cell
            node = self.obstacle_nodes[cell]

            # Map simulation cell (x, z) onto Panda ground plane (x, y)
            node.setPos(cx + 0.5, cz + 0.5, 0.25)

            if show_obstacles:
                node.show()
            else:
                node.hide()

    def update(self, agents, world_state=None, sim_update_ms=0.0):
        active_ids = set()

        for agent in agents:
            agent_id = agent.agent_id
            active_ids.add(agent_id)

            if agent_id not in self.agent_nodes:
                model = self.base.loader.loadModel("models/box")
                model.setScale(0.3, 0.3, 0.3)
                model.setColor(0.2, 0.7, 1.0, 1)
                node = model.copyTo(self.base.render)
                self.agent_nodes[agent_id] = node

            node = self.agent_nodes[agent_id]
            x, _, z = agent.position

            # Map simulation (x, z) to Panda (x, y), keep z as height
            node.setPos(x, z, 0.15)

        existing_ids = set(self.agent_nodes.keys())
        for stale_id in existing_ids - active_ids:
            self.agent_nodes[stale_id].removeNode()
            del self.agent_nodes[stale_id]

        if world_state is not None:
            show_obstacles = True
            self.draw_obstacles(world_state.obstacles, show_obstacles=show_obstacles)
            self.update_debug_text(world_state, sim_update_ms)

        self.update_camera(agents)

    def update_camera(self, agents):
        if not agents:
            return

        avg_x = sum(agent.position[0] for agent in agents) / len(agents)
        avg_z = sum(agent.position[2] for agent in agents) / len(agents)

        if self.camera_mode == "angled":
            # Better angled view: behind and above the crowd
            self.base.camera.setPos(avg_x, avg_z - 28, 18)
            self.base.camera.lookAt(avg_x, avg_z, 0)

        elif self.camera_mode == "topdown":
            self.base.camera.setPos(avg_x, avg_z, 35)
            self.base.camera.lookAt(avg_x, avg_z, 0)