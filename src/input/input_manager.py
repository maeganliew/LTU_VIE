from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point3


class InputManager(DirectObject):
    def __init__(self, base, world_state):
        super().__init__()

        self.world_state = world_state
        self.base = base

        # tracks which keys are currently held down
        self.keys = {}

        # units per second the target moves when WASD is held
        self.target_move_speed = 10.0

        print("[INPUT] InputManager initialized")

        self.setup_key_listeners()
        self.setup_control_bindings()

    def setup_key_listeners(self):
        # WASD — held keys that move the target position each frame
        for key in ("w", "s", "a", "d"):
            self.accept(key, self.on_key_down, [key])
            self.accept(f"{key}-up", self.on_key_up, [key])

    def setup_control_bindings(self):
        # crowd size
        self.accept("q", self.spawn_more)
        self.accept("e", self.spawn_less)

        # left click sets target via ray cast
        self.accept("mouse1", self.on_click)

        # feature toggles
        self.accept("p", self.toggle_pathfinding)
        self.accept("o", self.toggle_obstacles)
        self.accept("v", self.toggle_avoidance)

        # simulation speed  (= and + both increase, - decreases)
        self.accept("=", self.increase_speed)
        self.accept("+", self.increase_speed)
        self.accept("-", self.decrease_speed)

        # camera view toggle
        self.accept("c", self.toggle_camera)


    # called every frame from CrowdSimApp.update() — handles held keys
    def update(self, dt):
        tx, ty, tz = self.world_state.target_position
        spd = self.target_move_speed * dt

        if self.keys.get("w"):
            tz += spd
        if self.keys.get("s"):
            tz -= spd
        if self.keys.get("a"):
            tx -= spd
        if self.keys.get("d"):
            tx += spd

        # clamp to world bounds (world is 40x40, so -20 to 20)
        tx = max(-20.0, min(20.0, tx))
        tz = max(-20.0, min(20.0, tz))

        self.world_state.target_position = (tx, ty, tz)


    # key state tracking
    def on_key_down(self, key):
        self.keys[key] = True

    def on_key_up(self, key):
        self.keys[key] = False


    # crowd size
    def spawn_more(self):
        self.world_state.spawn_count = min(500, self.world_state.spawn_count + 10)
        print("[INPUT] spawn_count =", self.world_state.spawn_count)

    def spawn_less(self):
        self.world_state.spawn_count = max(0, self.world_state.spawn_count - 10)
        print("[INPUT] spawn_count =", self.world_state.spawn_count)
        
    # mouse click — ray cast onto the Z=0 ground plane
    def on_click(self):
        if not self.base.mouseWatcherNode.hasMouse():
            return

        mpos = self.base.mouseWatcherNode.getMouse()

        # build a ray from the camera through the mouse cursor
        near = Point3()
        far = Point3()
        self.base.camLens.extrude(mpos, near, far)

        # convert ray endpoints from camera space into world space
        near_world = self.base.render.getRelativePoint(self.base.cam, near)
        far_world = self.base.render.getRelativePoint(self.base.cam, far)

        # intersect the ray with the ground plane (Z = 0 in Panda3D)
        dz = far_world.z - near_world.z
        if abs(dz) < 1e-6:
            return  # ray is parallel to the ground, no intersection

        t = -near_world.z / dz
        world_x = near_world.x + t * (far_world.x - near_world.x)
        world_y = near_world.y + t * (far_world.y - near_world.y)

        # renderer maps simulation (sim_x, sim_z) → Panda3D (x, y, height)
        # so Panda3D X = simulation X, Panda3D Y = simulation Z
        self.world_state.target_position = (world_x, 0.0, world_y)
        print("[INPUT] target =", self.world_state.target_position)


    # feature toggles
    def toggle_pathfinding(self):
        current = self.world_state.debug_flags.get("pathfinding", True)
        self.world_state.debug_flags["pathfinding"] = not current
        print("[INPUT] pathfinding =", self.world_state.debug_flags["pathfinding"])

    def toggle_obstacles(self):
        current = self.world_state.debug_flags.get("obstacles", True)
        self.world_state.debug_flags["obstacles"] = not current
        print("[INPUT] obstacles =", self.world_state.debug_flags["obstacles"])

    def toggle_avoidance(self):
        current = self.world_state.debug_flags.get("avoidance", True)
        self.world_state.debug_flags["avoidance"] = not current
        print("[INPUT] avoidance =", self.world_state.debug_flags["avoidance"])

    def toggle_camera(self):
        if self.world_state.camera_mode == "angled":
            self.world_state.camera_mode = "topdown"
        else:
            self.world_state.camera_mode = "angled"
        print("[INPUT] camera_mode =", self.world_state.camera_mode)

    def increase_speed(self):
        self.world_state.simulation_speed = min(5.0, self.world_state.simulation_speed + 0.25)
        print("[INPUT] simulation_speed =", self.world_state.simulation_speed)

    def decrease_speed(self):
        self.world_state.simulation_speed = max(0.1, self.world_state.simulation_speed - 0.25)
        print("[INPUT] simulation_speed =", self.world_state.simulation_speed)