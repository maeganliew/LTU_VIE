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

        print(f"[RENDER] Rendering {len(agents)} agents")

        # create cubes if needed
        for i, agent in enumerate(agents):

            if i not in self.agent_nodes:
                node = self.loader.loadModel("models/box")
                node.reparentTo(self.render)
                node.setScale(1.2)
                node.setColor(1,0,0,1)
                node.setTwoSided(True)

                # use index here instead of Agent object, Agent object may not be hashable
                self.agent_nodes[i] = node

            # update position
            node = self.agent_nodes[i]
            node.setPos(agent.position[0], agent.position[2], 0)

            # DEBUG (moved camera here instead of in init)
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