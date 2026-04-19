from direct.showbase.ShowBase import ShowBase
from src.engine.core.world import World
from src.rendering.renderer import Renderer

class CrowdSimApp(ShowBase):
    def __init__(self):
        super().__init__()

        self.world = World()

        self.renderer = Renderer(self)

        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()

        self.world.update(dt)

        self.renderer.update(self.world.agent_system.agents)

        return task.cont