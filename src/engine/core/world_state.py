class WorldState:
    def __init__(self):
        self.agents = []
        self.spawn_count = 0
        self.target_position = None
        self.grid_size = 1.0