from collections import defaultdict


class SpatialGrid:
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        self.cells = defaultdict(list)

    def clear(self):
        self.cells.clear()

    def _cell_key(self, position):
        x, _, z = position
        return int(x // self.cell_size), int(z // self.cell_size)

    def insert(self, agent):
        key = self._cell_key(agent.position)
        self.cells[key].append(agent)

    def rebuild(self, agents):
        self.clear()
        for agent in agents:
            if agent.active:
                self.insert(agent)

    def get_neighbors(self, position):
        cx, cz = self._cell_key(position)
        neighbors = []

        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                neighbors.extend(self.cells.get((cx + dx, cz + dz), []))

        return neighbors