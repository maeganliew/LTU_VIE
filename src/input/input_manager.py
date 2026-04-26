from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point3, Plane, Vec3


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
        
        
    # Cast a ray from the camera through the mouse cursor and find where it hits the ground plane (Z = 0 in Panda3D world space).
    def on_click(self):
        #   Panda3D X  →  simulation X  (left/right)
        #   Panda3D Y  →  simulation Z  (forward/back, since agents use setPos(x, z, h))
        #   Panda3D Z  →  height (always 0 for ground plane)

        if not self.base.mouseWatcherNode.hasMouse():
            return

        mpos = self.base.mouseWatcherNode.getMouse()

        # extrude mouse position through the camera lens
        # near and far are in camera-local coordinate space
        near = Point3()
        far = Point3()
        self.base.camLens.extrude(mpos, near, far)

        # convert from camera-local space to world (render) space
        near_world = self.base.render.getRelativePoint(self.base.cam, near)
        far_world  = self.base.render.getRelativePoint(self.base.cam, far)

        # intersect the ray with the ground plane at Panda3D Z = 0
        # Vec3(0, 0, 1) = normal pointing straight up (Z axis)
        # Point3(0, 0, 0) = plane passes through the world origin
        ground_plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        hit = Point3()

        if not ground_plane.intersectsLine(hit, near_world, far_world):
            # ray is exactly parallel to the ground, extremely rare, just ignore
            print("[INPUT] click ray parallel to ground, ignoring")
            return

        # map Panda3D coordinates to simulation coordinates
        # Panda3D X = simulation X, Panda3D Y = simulation Z
        sim_x = hit.x
        sim_z = hit.y

        # if click lands outside the world entirely, ignore it
        # prevents the target from being permanently clamped to a world edge
        half_w = 20.0
        half_h = 20.0
        if abs(sim_x) > half_w or abs(sim_z) > half_h:
            print(f"[INPUT] click outside world bounds ({sim_x:.1f}, {sim_z:.1f}), ignoring")
            return

        self.world_state.target_position = (sim_x, 0.0, sim_z)
        print(f"[INPUT] target = ({sim_x:.2f}, 0.0, {sim_z:.2f})")


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