from panda3d.core import AmbientLight, DirectionalLight, LineSegs, NodePath


class Renderer:
    def __init__(self, base, world_state):
        self.base = base
        self.world_state = world_state
        self.render = base.render
        self.loader = base.loader
        self.camera = base.camera

        self.agent_nodes = {}
        self.obstacle_nodes = {}

        self.setup_lighting()
        self.setup_grid()
        self.setup_camera()
        self.build_obstacles()

    def setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor((0.5, 0.5, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        directional = DirectionalLight("directional")
        directional.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(directional)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

    def setup_grid(self):
        lines = LineSegs()
        lines.setColor(0.5, 0.5, 0.5, 1)

        for i in range(-20, 21, 2):
            lines.moveTo(i, -20, 0)
            lines.drawTo(i, 20, 0)
            lines.moveTo(-20, i, 0)
            lines.drawTo(20, i, 0)

        grid = NodePath(lines.create())
        grid.reparentTo(self.render)

    def setup_camera(self):
        self.camera.setPos(0, -60, 20)
        self.camera.lookAt(0, 0, 0)

    def build_obstacles(self):
        # Remove any old obstacle nodes first
        for node in self.obstacle_nodes.values():
            node.removeNode()
        self.obstacle_nodes.clear()

        for cell in self.world_state.obstacles:
            cell_x, cell_z = cell

            node = self.loader.loadModel("models/box")
            node.reparentTo(self.render)
            node.setScale(1.0, 1.0, 1.0)
            node.setColor(0.2, 0.2, 1.0, 1.0)  # blue obstacles
            node.setPos(cell_x, cell_z, 0.5)   # raise slightly above ground
            node.setTwoSided(True)

            self.obstacle_nodes[cell] = node

    def update(self, agents):
        active_agent_ids = set()

        for agent in agents:
            agent_id = agent.agent_id
            active_agent_ids.add(agent_id)

            if agent_id not in self.agent_nodes:
                node = self.loader.loadModel("models/box")
                node.reparentTo(self.render)
                node.setScale(1.0)
                node.setColor(1, 0, 0, 1)  # red agents
                node.setTwoSided(True)
                self.agent_nodes[agent_id] = node

            node = self.agent_nodes[agent_id]
            node.setPos(agent.position[0], agent.position[2], 0.5)

        existing_ids = set(self.agent_nodes.keys())
        removed_ids = existing_ids - active_agent_ids

        for agent_id in removed_ids:
            self.agent_nodes[agent_id].removeNode()
            del self.agent_nodes[agent_id]

        if agents:
            xs = [a.position[0] for a in agents]
            zs = [a.position[2] for a in agents]
            center_x = sum(xs) / len(xs)
            center_z = sum(zs) / len(zs)

            self.camera.setPos(center_x, -60, center_z + 20)
            self.camera.lookAt(center_x, 0, center_z)