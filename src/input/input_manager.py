from direct.showbase.DirectObject import DirectObject

class InputManager(DirectObject):
    def __init__(self):
        super().__init__()

        print("[INPUT] InputManager initialized")

        # Store state
        self.keys = {}
        self.mouse_click = None

        # Setup listeners
        self.setup_key_listeners()
        self.setup_mouse_listeners()

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