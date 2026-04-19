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
        
        # Cube (3D box)
        cube = self.loader.loadModel("models/box")
        if cube is None:
            # Fallback: build cube from cards
            cm = CardMaker("face")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            for pos, hpr in [
                ((0,0,0.5), (0,0,0)), ((0,0,-0.5), (0,0,0)),
                ((0,0.5,0), (0,90,0)), ((0,-0.5,0), (0,-90,0)),
                ((0.5,0,0), (0,0,90)), ((-0.5,0,0), (0,0,-90))
            ]:
                face = self.render.attachNewNode(cm.generate())
                face.setPos(pos)
                face.setHpr(hpr)
                face.setColor(0.2, 0.6, 1, 1)
                face.setTwoSided(True)
        else:
            cube.reparentTo(self.render)
            cube.setScale(1, 1, 1)
            cube.setColor(0.2, 0.6, 1, 1)
            cube.setPos(0, 0, 0)
        
        #self.camera.setPos(10, -15, 10)
        self.camera.setPos(0, -50, 50)
        self.camera.lookAt(0, 0, 0)
        self.agent_nodes = {}

    def update(self, agents):

        print(f"[RENDER] Rendering {len(agents)} agents")

        # create cubes if needed
        for i, agent in enumerate(agents):

            if i not in self.agent_nodes:
                node = self.loader.loadModel("models/box")
                node.reparentTo(self.render)
                node.setScale(1.0,1.0,1.0)
                node.setColor(1,0,0,1)

                # use index here instead of Agent object, Agent object may not be hashable
                self.agent_nodes[i] = node

            # update position
            node = self.agent_nodes[i]
            node.setPos(agent.position[0], 0, agent.position[2]+0.5)