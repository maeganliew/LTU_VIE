from src.engine.simulation.agent import Agent
import math
import random

from src.engine.simulation.agent import AgentState
from src.engine.simulation.movement import move_towards
from src.engine.systems.spatial_grid import SpatialGrid

class AgentSystem:
    def __init__(self, world_state, config):
        self.world_state = world_state
        self.config = config
        self.grid = SpatialGrid(config.cell_size)
        self.next_id = 1

    # use default initial num form config if no count provided
    def initialize_agents(self, count=None):
        if count is None:
            count = self.config.initial_agent_count

        self.world_state.agents.clear()

        for _ in range(count):
            self.world_state.agents.append(self._create_random_agent())


    def _create_random_agent(self):
        x = random.uniform(0, self.config.world_width - 1)
        z = random.uniform(0, self.config.world_height - 1)

        agent = AgentState(
            agent_id=self.next_id,
            position=(x, 0.0, z),
            target=self.world_state.target_position,
            speed=self.config.move_speed,
        )
        self.next_id += 1
        return agent


    def sync_spawn_count(self):
        desired = self.world_state.spawn_count
        current = len(self.world_state.agents)

        if desired > current:
            for _ in range(desired - current):
                if len(self.world_state.agents) < self.config.max_agents:
                    self.world_state.agents.append(self._create_random_agent())
        elif desired < current:
            self.world_state.agents = self.world_state.agents[:desired]
            
    def spawn_agents(self, count):
        for _ in range(count):
            self.agents.append(Agent((
                random.uniform(-20, 20),
                0,
                random.uniform(-20, 20),
            )))

    def update(self, dt):
        # ensure world has correct number of agent
        self.sync_spawn_count()
        
        # rebuild grid using current agent position
        self.grid.rebuild(self.world_state.agents)

        # loop through every agent and update it
        for agent in self.world_state.agents:
            agent.target = self.world_state.target_position

            new_position, velocity = move_towards(
                agent.position,
                agent.target,
                agent.speed * self.world_state.simulation_speed,
                dt,
            )

            # adjust to new position by pushing away from nearby agents
            if self.world_state.debug_flags.get("avoidance", True):
                new_position = self.apply_avoidance(agent, new_position)

            agent.position = self.clamp_to_world(new_position)
            agent.velocity = velocity


    def apply_avoidance(self, agent, proposed_position):
        px, py, pz = proposed_position
        push_x = 0.0
        push_z = 0.0

        neighbors = self.grid.get_neighbors(agent.position)

        for other in neighbors:
            if other.agent_id == agent.agent_id or not other.active:
                continue

            dx = px - other.position[0]
            dz = pz - other.position[2]
            dist_sq = dx * dx + dz * dz

            if dist_sq < 1e-8:
                continue

            distance = math.sqrt(dist_sq)
            if distance < self.config.neighbor_radius:
                strength = (
                    self.config.neighbor_radius - distance
                ) / self.config.neighbor_radius
                
                # push away from the neighbor in the outwards direction
                push_x += (dx / distance) * strength * self.config.avoidance_strength
                push_z += (dz / distance) * strength * self.config.avoidance_strength

        return (px + push_x * 0.03, py, pz + push_z * 0.03)

    def clamp_to_world(self, position):
        x, y, z = position
        x = max(0.0, min(x, self.config.world_width - 1))
        z = max(0.0, min(z, self.config.world_height - 1))
        return (x, y, z)