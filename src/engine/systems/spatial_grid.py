from collections import defaultdict


class SpatialGrid:
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        
        # make a dictionary where each cell maps to a list of agents
        self.cells = defaultdict(list)

    # removes all cell contents. used before rebuilding the grid each update
    def clear(self):
        self.cells.clear()

    # convert a world position into a grid cell coordinate
    def _cell_key(self, position):
        x, _, z = position
        return int(x // self.cell_size), int(z // self.cell_size)

    # find cell where the agent belongs and store it there
    def insert(self, agent):
        key = self._cell_key(agent.position)
        self.cells[key].append(agent)

    # each update, clear grid and insert active agent into correct cell
    def rebuild(self, agents):
        self.clear()
        for agent in agents:
            if agent.active:
                self.insert(agent)

    def get_neighbors(self, position):
        cx, cz = self._cell_key(position)
        neighbors = []

        # check the 3x3 area around the cell (left, center, right)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                neighbors.extend(self.cells.get((cx + dx, cz + dz), []))

        return neighbors