import math
import random
import time

from src.engine.simulation.agent import AgentState,AgentBehavior
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
        
        self.last_obstacles_enabled = None
        
        # remembers the previous global target POSITION
        self.last_global_target = None
        
        # per-subsystem timing 
        self.timing = {
            "grid_rebuild_ms": 0.0,   # time to bucket all agents into cells
            "nav_rebuild_ms":  0.0,   # time to run the BFS (0 on most frames)
            "agent_loop_ms":   0.0,   # time for the full per-agent update loop
        }

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
        print("[AGENT_SYSTEM] WARNING: could not find free spawn position, using origin")
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
            
    def get_active_obstacles(self):
        # return the obstacle set only if obstacles are currently enabled
        if self.world_state.debug_flags.get("obstacles", True):
            return self.world_state.obstacles
        return set()

    # checks pathfinding enabled, target cell change? field empty? then rebuild the navigation field
    def rebuild_navigation_if_needed(self):
        if not self.world_state.debug_flags.get("pathfinding", True):
            return

        target_cell = self.navigation_field.position_to_cell(
            self.world_state.target_position
        )
        obstacles_enabled = self.world_state.debug_flags.get("obstacles", True)
        active_obstacles = self.get_active_obstacles()

        needs_rebuild = (
            target_cell != self.last_target_cell
            or obstacles_enabled != self.last_obstacles_enabled
            or not self.navigation_field.distance_map
        )

        if needs_rebuild:
            self.navigation_field.rebuild(
                self.world_state.target_position,
                active_obstacles,
            )
            self.last_target_cell = self.navigation_field.target_cell
            self.last_obstacles_enabled = obstacles_enabled
            
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
    

    def _pick_wander_target(self, agent):
        """
        Pick a random free position within wander_radius of the agent.
        Uses polar coordinates (angle + distance) so all directions are
        equally likely — uniform x/z ranges would bias toward corners.
        Tries up to 50 times then falls back to current position.
        """
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(1.0, self.config.wander_radius)
            wx = agent.position[0] + math.cos(angle) * r
            wz = agent.position[2] + math.sin(angle) * r

            # clamp to world bounds
            wx = max(
                -self.config.world_width  / 2,
                min(self.config.world_width  / 2, wx)
            )
            wz = max(
                -self.config.world_height / 2,
                min(self.config.world_height / 2, wz)
            )

            candidate = (wx, 0.0, wz)
            if not self.is_blocked(candidate):
                return candidate

        # fallback: stay at current position
        return agent.position
    
    def _update_agent_behavior(self, agent, dt):
        """
        Run the agent behaviour state machine for one tick.
        Returns the steering target the agent should move toward this frame.

        States:
          NAVIGATING → moves toward global target via flow field
                       transitions to ARRIVED when within arrival_radius
          ARRIVED    → stays still, increments arrived_timer
                       transitions to WANDERING when timer >= wander_delay
          WANDERING  → moves toward a random wander_target
                       picks a new wander_target when it arrives there
                       transitions back to NAVIGATING if global target changes
        """
        global_target = self.world_state.target_position

        if agent.behavior == AgentBehavior.NAVIGATING:
            # check if close enough to be considered arrived
            dx = agent.position[0] - global_target[0]
            dz = agent.position[2] - global_target[2]
            dist = math.sqrt(dx * dx + dz * dz)

            if dist <= self.config.arrival_radius:
                # transition: NAVIGATING → ARRIVED
                agent.behavior = AgentBehavior.ARRIVED
                agent.arrived_timer = 0.0
                return agent.position   # stop moving this frame

            # still navigating — use flow field
            return self.choose_navigation_target(agent)

        elif agent.behavior == AgentBehavior.ARRIVED:
            agent.arrived_timer += dt

            if agent.arrived_timer >= self.config.wander_delay:
                # waited long enough — pick a wander destination and start roaming
                agent.wander_target = self._pick_wander_target(agent)
                # transition: ARRIVED → WANDERING
                agent.behavior = AgentBehavior.WANDERING

            # stay still while waiting
            return agent.position

        elif agent.behavior == AgentBehavior.WANDERING:
            # check if the wander destination has been reached
            dx = agent.position[0] - agent.wander_target[0]
            dz = agent.position[2] - agent.wander_target[2]
            dist = math.sqrt(dx * dx + dz * dz)

            if dist < 0.5:
                # reached the wander point — pick a new one and keep roaming
                agent.wander_target = self._pick_wander_target(agent)

            # move toward the current wander point (bypass flow field)
            return agent.wander_target

        # fallback
        return global_target

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
            
            # use the actual physical size of both agents to decide when to push
            # combined_radius = how close they can be before touching
            combined_radius = agent.radius + other.radius
            
            if distance < combined_radius:
                # stronger push when agents are closer
                strength = (combined_radius - distance) / combined_radius
                
                # push away from the neighbor in the outwards direction
                push_x += (dx / distance) * strength * self.config.avoidance_strength
                push_z += (dz / distance) * strength * self.config.avoidance_strength
        
        # 0.03 damping prevents violent jitter from competing push forces
        return (px + push_x * 0.03, py, pz + push_z * 0.03)

    def clamp_to_world(self, position):
        # keep agents inside world boundaries
        x, y, z = position
        x = max(-self.config.world_width / 2, min(x, self.config.world_width / 2))
        z = max(-self.config.world_height / 2, min(z, self.config.world_height / 2))
        return (x, y, z)
    
    
    def update(self, dt):
        """
        One simulation tick. Called every frame by World via the Profiler.

        Order:
          1. sync_spawn_count    — make sure right number of agents exist
          2. grid rebuild        — bucket agents into spatial hash cells
          3. nav rebuild         — BFS only if target or obstacles changed
          4. global target check — wake ARRIVED/WANDERING agents if target moved
          5. per-agent loop      — behavior → steer → move → avoid → collide → clamp
        """

        self.sync_spawn_count()

        # spatial grid rebuild (timed separately)
        t0 = time.perf_counter()
        self.grid.rebuild(self.world_state.agents)
        self.timing["grid_rebuild_ms"] = (time.perf_counter() - t0) * 1000.0

        # navigation field rebuild (timed separately) 
        t0 = time.perf_counter()
        self.rebuild_navigation_if_needed()
        self.timing["nav_rebuild_ms"] = (time.perf_counter() - t0) * 1000.0

        # check if global target changed 
        # if the player moved the target, wake all ARRIVED / WANDERING agents
        current_global_target = self.world_state.target_position
        if current_global_target != self.last_global_target:
            for agent in self.world_state.agents:
                if agent.behavior != AgentBehavior.NAVIGATING:
                    agent.behavior = AgentBehavior.NAVIGATING
                    agent.arrived_timer = 0.0
            self.last_global_target = current_global_target

        # per-agent loop (timed separately) 
        t0 = time.perf_counter()

        for agent in self.world_state.agents:
            # always keep agent.target in sync with the global target
            agent.target = self.world_state.target_position

            # decide where this agent should move based on its behaviour state
            steering_target = self._update_agent_behavior(agent, dt)

            # move toward the steering target at the agent's speed
            new_position, velocity = move_towards(
                agent.position,
                steering_target,
                agent.speed * self.world_state.simulation_speed,
                dt,
            )

            # push away from nearby agents (spatial grid used internally)
            if self.world_state.debug_flags.get("avoidance", True):
                new_position = self.apply_avoidance(agent, new_position)

            # prevent walking through wall cells
            new_position = self.resolve_obstacle_collision(
                agent.position, new_position
            )

            # keep inside world bounds
            agent.position = self.clamp_to_world(new_position)
            agent.velocity = velocity

            # safety net: if avoidance pushed agent inside a wall, relocate it
            # this is now actually called — previously it was dead code
            self.relocate_if_inside_obstacle(agent)

        self.timing["agent_loop_ms"] = (time.perf_counter() - t0) * 1000.0