from direct.showbase.ShowBase import ShowBase
from src.engine.core.world import World

class CrowdSimApp(ShowBase):
    def __init__(self):
        super().__init__()

        self.world = World()

        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()

        self.world.update(dt)

        return task.cont