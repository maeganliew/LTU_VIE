from direct.showbase.ShowBase import ShowBase
from src.engine.core.world import World
from src.input.input_manager import InputManager

class CrowdSimApp(ShowBase):
    def __init__(self):
        super().__init__()

        print("[APP] Panda3D started")

        self.world = World()
        self.input_manager = InputManager()

        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()

        self.world.update(dt)

        return task.cont