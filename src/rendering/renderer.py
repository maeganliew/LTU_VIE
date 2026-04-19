from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, LineSegs, NodePath, CardMaker

class Renderer:
    def __init__(self, base):
        self.base = base
        self.render = base.render
        self.loader = base.loader
        self.camera = base.camera
        
        # Lighting
        ambient = AmbientLight("ambient")
        ambient.setColor((0.5, 0.5, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(ambient))
        
        directional = DirectionalLight("directional")
        directional.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(directional)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)
        
        # Grid
        lines = LineSegs()
        lines.setColor(0.5, 0.5, 0.5, 1)
        for i in range(-20, 21, 2):
            lines.moveTo(i, -20, 0)
            lines.drawTo(i, 20, 0)
            lines.moveTo(-20, i, 0)
            lines.drawTo(20, i, 0)
        grid = NodePath(lines.create())
        grid.reparentTo(self.render)
        
        self.camera.setPos(10, -20, 10)
        self.camera.lookAt(45, 0, 0)
        self.agent_nodes = {}

    # read positions, move cubes visually
    def update(self, agents):

        # print(f"[RENDER] Rendering {len(agents)} agents")
        
        # ZX change update() to key self.agent_nodes by agent.agent_id instead of the enumerate index i
        # The index is unstable when agents are added, removed, or reordered, so nodes can get mismatched to the wrong agent
        # i also remove nodes for agent IDs that no longer exist in the current frame.
    
        # track which agent IDs still exist this frame
        active_agent_ids = set()


        # create/update cubes using stable agent_id
        for agent in agents:
            agent_id = agent.agent_id
            active_agent_ids.add(agent_id)

            if agent_id not in self.agent_nodes:
                node = self.loader.loadModel("models/box")
                node.reparentTo(self.render)
                node.setScale(1.2)
                node.setColor(1, 0, 0, 1)
                node.setTwoSided(True)
                self.agent_nodes[agent_id] = node

            node = self.agent_nodes[agent_id]
            node.setPos(agent.position[0], agent.position[2], 0)

        # remove cubes for agents that no longer exist
        existing_ids = set(self.agent_nodes.keys())
        removed_ids = existing_ids - active_agent_ids

        for agent_id in removed_ids:
            self.agent_nodes[agent_id].removeNode()
            del self.agent_nodes[agent_id]

        # update camera once, not inside the loop
        if agents:
            xs = [a.position[0] for a in agents]
            zs = [a.position[2] for a in agents]
            center_x = sum(xs) / len(xs)
            center_z = sum(zs) / len(zs)
            self.camera.setPos(center_x, -60, center_z + 20)
            self.camera.lookAt(center_x, 0, center_z)
            
            # DEBUG - debug lines
            # print("loaded node:", node)
            # print("agent pos:", agent.position)
            # print("camera:", self.camera.getPos())
            # print("agent sample:", agents[0].position)