from direct.showbase.ShowBase import ShowBase
from src.engine.core.world import World
from src.rendering.renderer import Renderer
from src.input.input_manager import InputManager

class CrowdSimApp(ShowBase):
    def __init__(self):
        super().__init__()

        print("[APP] Panda3D started")

        self.world = World()
        self.input_manager = InputManager()

        self.renderer = Renderer(self)

        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()

        self.world.update(dt)

        self.renderer.update(self.world.world_state.agents)

        return task.cont