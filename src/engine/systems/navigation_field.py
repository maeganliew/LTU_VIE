from collections import deque
import math


class NavigationField:
    def __init__(self, config):
        self.config = config
        
        # cell → shortest number of grid steps to the target 
        self.distance_map = {}
        
        self.target_cell = None

        self.min_cell_x = math.floor((-self.config.world_width / 2) / self.config.cell_size)
        self.max_cell_x = math.ceil((self.config.world_width / 2) / self.config.cell_size) - 1
        self.min_cell_z = math.floor((-self.config.world_height / 2) / self.config.cell_size)
        self.max_cell_z = math.ceil((self.config.world_height / 2) / self.config.cell_size) - 1

    def clear(self):
        self.distance_map.clear()
        self.target_cell = None

    # turns world coordinate into a grid cell 
    def position_to_cell(self, position):
        x, _, z = position
        return (
            math.floor(x / self.config.cell_size),
            math.floor(z / self.config.cell_size),
        )

    def cell_to_position(self, cell):
        cx, cz = cell
        half = self.config.cell_size * 0.5
        return (
            cx * self.config.cell_size + half,
            0.0,
            cz * self.config.cell_size + half,
        )

    def in_bounds(self, cell):
        cx, cz = cell
        return (
            self.min_cell_x <= cx <= self.max_cell_x
            and self.min_cell_z <= cz <= self.max_cell_z
        )

    def is_walkable(self, cell, obstacles):
        return self.in_bounds(cell) and cell not in obstacles

    def get_neighbors4(self, cell):
        cx, cz = cell
        return [
            (cx + 1, cz),
            (cx - 1, cz),
            (cx, cz + 1),
            (cx, cz - 1),
        ]

    def get_neighbors8(self, cell):
        cx, cz = cell
        return [
            (cx + 1, cz),
            (cx - 1, cz),
            (cx, cz + 1),
            (cx, cz - 1),
            (cx + 1, cz + 1),
            (cx + 1, cz - 1),
            (cx - 1, cz + 1),
            (cx - 1, cz - 1),
        ]

    def find_nearest_walkable(self, start_cell, obstacles):
        if self.is_walkable(start_cell, obstacles):
            return start_cell

        queue = deque([start_cell])
        visited = {start_cell}

        while queue:
            cell = queue.popleft()

            for neighbor in self.get_neighbors8(cell):
                if neighbor in visited:
                    continue
                visited.add(neighbor)

                if self.is_walkable(neighbor, obstacles):
                    return neighbor

                if self.in_bounds(neighbor):
                    queue.append(neighbor)

        return None

    def rebuild(self, target_position, obstacles):
        self.clear()

        raw_target_cell = self.position_to_cell(target_position)
        target_cell = self.find_nearest_walkable(raw_target_cell, obstacles)

        if target_cell is None:
            return

        self.target_cell = target_cell
        self.distance_map[target_cell] = 0

        queue = deque([target_cell])

        while queue:
            current = queue.popleft()
            current_distance = self.distance_map[current]

            for neighbor in self.get_neighbors4(current):
                if neighbor in self.distance_map:
                    continue
                if not self.is_walkable(neighbor, obstacles):
                    continue

                self.distance_map[neighbor] = current_distance + 1
                queue.append(neighbor)

    def get_best_next_cell(self, current_cell):
        if not self.distance_map:
            return None

        current_distance = self.distance_map.get(current_cell, float("inf"))

        if current_cell == self.target_cell:
            return current_cell

        best_cell = None
        best_distance = current_distance

        for neighbor in self.get_neighbors4(current_cell):
            neighbor_distance = self.distance_map.get(neighbor, float("inf"))
            if neighbor_distance < best_distance:
                best_distance = neighbor_distance
                best_cell = neighbor

        if best_cell is not None:
            return best_cell

        if current_cell in self.distance_map:
            return current_cell

        for neighbor in self.get_neighbors8(current_cell):
            neighbor_distance = self.distance_map.get(neighbor, float("inf"))
            if neighbor_distance < float("inf"):
                return neighbor

        return None

    # upgrades simulation from direct steering only to grid-guided navigation
    def get_steering_target(self, current_position, final_target_position):
        if not self.distance_map or self.target_cell is None:
            return final_target_position

        current_cell = self.position_to_cell(current_position)
        next_cell = self.get_best_next_cell(current_cell)

        if next_cell is None:
            return current_position

        if next_cell == self.target_cell:
            return final_target_position

        return self.cell_to_position(next_cell)