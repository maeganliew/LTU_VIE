from direct.showbase.ShowBase import ShowBase
from src.engine.core.world import World
from src.rendering.renderer import Renderer
from src.input.input_manager import InputManager


class CrowdSimApp(ShowBase):
    def __init__(self):
        super().__init__()

        print("[APP] Panda3D started")

        self.world = World()
        self.input_manager = InputManager(self, self.world.world_state)
        self.renderer = Renderer(self)

        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()

        # update held-key input (WASD target movement, etc.)
        self.input_manager.update(dt)

        # run simulation tick (profiled internally)
        self.world.update(dt)

        # update the 3D scene from world state
        self.renderer.update(
            self.world.world_state.agents,
            self.world.world_state,
            self.world.profiler.last_update_ms,
            self.world.profiler.average_ms,
            self.world.profiler.peak_ms,
        )

        return task.cont