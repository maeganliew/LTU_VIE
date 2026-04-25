import math
import random

from src.engine.simulation.agent import AgentState
from src.engine.simulation.movement import move_towards
from src.engine.systems.spatial_grid import SpatialGrid
from src.engine.systems.navigation_field import NavigationField

class AgentSystem:
    def __init__(self, world_state, config):
        
        # shared world state: agents, target, obstacles, spawn count, flags
        self.world_state = world_state
        
        self.config = config
        self.grid = SpatialGrid(config.cell_size)
        
        # creates a shared navigation field for the whole simulation
        self.navigation_field = NavigationField(config)
        
        self.next_id = 1
        
        # remembers the previous target cell so do not rebuild the navigation field every frame
        self.last_target_cell = None

    # use default initial num form config if no count provided
    def initialize_agents(self, count=None):
        if count is None:
            count = self.config.initial_agent_count

        self.world_state.agents.clear()

        # create the requested number of agents
        for _ in range(count):
            self.world_state.agents.append(self._create_random_agent())

    def _create_random_agent(self):
        # try multiple times to find a random free position
        # so agents do not spawn inside obstacle cells
        max_attempts = 200

        for _ in range(max_attempts):
            x = random.uniform(-self.config.world_width / 2, self.config.world_width / 2)
            z = random.uniform(-self.config.world_height / 2, self.config.world_height / 2)
            position = (x, 0.0, z)

            if not self.is_blocked(position):
                agent = AgentState(
                    agent_id=self.next_id,
                    position=position,
                    target=self.world_state.target_position,
                    speed=self.config.move_speed,
                )
                self.next_id += 1
                return agent

        # fallback if no free spot found
        agent = AgentState(
            agent_id=self.next_id,
            position=(0.0, 0.0, 0.0),
            target=self.world_state.target_position,
            speed=self.config.move_speed,
        )
        self.next_id += 1
        return agent
    
    def sync_spawn_count(self):
        # ensure the actual number of agents matches world_state.spawn_count
        desired = self.world_state.spawn_count
        current = len(self.world_state.agents)

        if desired > current:
            for _ in range(desired - current):
                if len(self.world_state.agents) < self.config.max_agents:
                    self.world_state.agents.append(self._create_random_agent())
        elif desired < current:
            self.world_state.agents = self.world_state.agents[:desired]
            

    # checks pathfinding enabled, target cell change? field empty? then rebuild the navigation field
    def rebuild_navigation_if_needed(self):
        if not self.world_state.debug_flags.get("pathfinding", True):
            return

        target_cell = self.navigation_field.position_to_cell(
            self.world_state.target_position
        )

        if target_cell != self.last_target_cell or not self.navigation_field.distance_map:
            self.navigation_field.rebuild(
                self.world_state.target_position,
                self.world_state.obstacles,
            )
            self.last_target_cell = self.navigation_field.target_cell
            
    # chooses what the agent should move toward this frame
    def choose_navigation_target(self, agent):
        
        if self.world_state.debug_flags.get("pathfinding", True):
            
            #do not aim directly at the final clicked target, ask the navigation field for the next steering point
            return self.navigation_field.get_steering_target(
                agent.position,
                self.world_state.target_position,
            )
            
        # move directly toward the world target as before
        return self.world_state.target_position

    def position_to_cell(self, position):
        # convert floating-point world position into integer grid cell
        x, _, z = position
        return int(math.floor(x / self.config.cell_size)), int(math.floor(z / self.config.cell_size))
    
    
    def is_blocked(self, position):
        if not self.world_state.debug_flags.get("obstacles", True):
            return False

        cell = self.position_to_cell(position)
        return cell in self.world_state.obstacles
    

    def resolve_obstacle_collision(self, current_position, proposed_position):
        if not self.world_state.debug_flags.get("obstacles", True):
            return proposed_position

        if not self.is_blocked(proposed_position):
            return proposed_position

        # try a simple slide instead of full pathfinding
        cx, cy, cz = current_position
        px, py, pz = proposed_position

        # try sliding along x only
        slide_x = (px, py, cz)
        if not self.is_blocked(slide_x):
            return slide_x

        # try sliding along z only
        slide_z = (cx, py, pz)
        if not self.is_blocked(slide_z):
            return slide_z

        # if both blocked, stay in place
        return current_position

            
    def relocate_if_inside_obstacle(self, agent):
        if not self.is_blocked(agent.position):
            return

        # relocate it to a free random position.
        max_attempts = 200
        for _ in range(max_attempts):
            x = random.uniform(-self.config.world_width / 2, self.config.world_width / 2)
            z = random.uniform(-self.config.world_height / 2, self.config.world_height / 2)
            candidate = (x, 0.0, z)

            if not self.is_blocked(candidate):
                agent.position = candidate
                return

    

    def update(self, dt):
        # ensure world has correct number of agent
        self.sync_spawn_count()
        
        # rebuild grid using current agent position
        self.grid.rebuild(self.world_state.agents)
        
        self.rebuild_navigation_if_needed()

        # loop through every agent and update it
        for agent in self.world_state.agents:
            agent.target = self.world_state.target_position
            
            steering_target = self.choose_navigation_target(agent)

            new_position, velocity = move_towards(
                agent.position,
                steering_target,
                agent.speed * self.world_state.simulation_speed,
                dt,
            )

            # adjust to new position by pushing away from nearby agents
            if self.world_state.debug_flags.get("avoidance", True):
                new_position = self.apply_avoidance(agent, new_position)

            # do not walk straight through blocked cells
            new_position = self.resolve_obstacle_collision(agent.position, new_position)

            agent.position = self.clamp_to_world(new_position)
            agent.velocity = velocity

        # keep logging only at controlled intervals in World.update
        # print("TARGET:", self.world_state.target_position)
        # print("AGENT0 TARGET:", self.world_state.agents[0].target)
        # print("AGENT0 POS:", self.world_state.agents[0].position)


    def apply_avoidance(self, agent, proposed_position):
        px, py, pz = proposed_position
        
        # accumulated push-away force from nearby neighbors
        push_x = 0.0
        push_z = 0.0

        neighbors = self.grid.get_neighbors(agent.position)

        for other in neighbors:
            if other.agent_id == agent.agent_id or not other.active:
                continue
            
            # compute difference from other agent
            dx = px - other.position[0]
            dz = pz - other.position[2]
            dist_sq = dx * dx + dz * dz

            if dist_sq < 1e-8:
                continue

            distance = math.sqrt(dist_sq)
            if distance < self.config.neighbor_radius:
                # stronger push when agents are closer
                strength = (
                    self.config.neighbor_radius - distance
                ) / self.config.neighbor_radius
                
                # push away from the neighbor in the outwards direction
                push_x += (dx / distance) * strength * self.config.avoidance_strength
                push_z += (dz / distance) * strength * self.config.avoidance_strength

        return (px + push_x * 0.03, py, pz + push_z * 0.03)

    def clamp_to_world(self, position):
        # keep agents inside world boundaries
        x, y, z = position
        x = max(-self.config.world_width / 2, min(x, self.config.world_width / 2))
        z = max(-self.config.world_height / 2, min(z, self.config.world_height / 2))
        return (x, y, z)