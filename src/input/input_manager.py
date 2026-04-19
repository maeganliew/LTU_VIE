from direct.showbase.DirectObject import DirectObject
from panda3d.core import WindowProperties

class InputManager(DirectObject):
    def __init__(self, base, world_state):
        super().__init__()

        print("BASE TYPE:", type(base))

        self.world_state = world_state
        self.base = base

        print("[INPUT] InputManager initialized")

        # Store state
        self.keys = {}
        self.mouse_click = None

        # Setup listeners
        self.setup_key_listeners()
        self.setup_mouse_listeners()

        # Bind keys, q means 10 more agents, e means 10 less agents
        self.base.accept("q", self.spawn_more)
        self.base.accept("e", self.spawn_less)

        # can click to set target position
        self.base.accept("mouse1", self.on_click)

    def setup_key_listeners(self):
        # Example keys
        self.accept("w", self.on_key_down, ["w"])
        self.accept("s", self.on_key_down, ["s"])
        self.accept("a", self.on_key_down, ["a"])
        self.accept("d", self.on_key_down, ["d"])

        # Key release
        self.accept("w-up", self.on_key_up, ["w"])
        self.accept("s-up", self.on_key_up, ["s"])
        self.accept("a-up", self.on_key_up, ["a"])
        self.accept("d-up", self.on_key_up, ["d"])

    def setup_mouse_listeners(self):
        self.accept("mouse1", self.on_mouse_click)

    def on_key_down(self, key):
        self.keys[key] = True
        print(f"[INPUT] Key pressed: {key}")

    def on_key_up(self, key):
        self.keys[key] = False
        print(f"[INPUT] Key released: {key}")

    def on_mouse_click(self):
        if base.mouseWatcherNode.hasMouse():
            mouse_pos = base.mouseWatcherNode.getMouse()
            self.mouse_click = (mouse_pos.getX(), mouse_pos.getY())

            print(f"[INPUT] Mouse clicked at: {self.mouse_click}")

    def spawn_more(self):
        # max 500 agents
        self.world_state.spawn_count = min(500, self.world_state.spawn_count + 10)
        print("[INPUT] spawn_count =", self.world_state.spawn_count)

    def spawn_less(self):
        # prevent agent reduce to negative value
        self.world_state.spawn_count = max(0, self.world_state.spawn_count - 10)
        print("[INPUT] spawn_count =", self.world_state.spawn_count)

    def setup_mouse(self):
        self.base.accept("mouse1", self.on_click)

    def on_click(self):
        print("[MOUSE] click detected")
        if not self.base.mouseWatcherNode.hasMouse():
            return

        mpos = self.base.mouseWatcherNode.getMouse()

        # simple world mapping (top-down plane assumption)
        x = mpos.x * 20
        z = mpos.y * 20

        self.world_state.target_position = (x, 0.0, z)

        print("[INPUT] target =", self.world_state.target_position)