import math
from typing import Tuple


# vector a - vector b , direction = target - position
def vec_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


# vector a + vector b , new_position = old_position + movement
def vec_add(a: Tuple[float, float, float], b: Tuple[float, float, float]):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


# vector * number , movement = velocity * dt
def vec_mul(v: Tuple[float, float, float], scalar: float):
    return (v[0] * scalar, v[1] * scalar, v[2] * scalar)


# length of a vector to determine how far target/other agent is
def vec_length(v: Tuple[float, float, float]):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


# converts vector into a unit vector with length 1 for direction only
def vec_normalize(v: Tuple[float, float, float]):
    length = vec_length(v)
    if length < 1e-6:
        return (0.0, 0.0, 0.0)
    return (v[0] / length, v[1] / length, v[2] / length)


# next position and velocity of an agent moving toward a target
def move_towards(position, target, speed, dt):
    direction = vec_sub(target, position)
    distance = vec_length(direction)

    # agent is already close to the target, stop moving
    if distance < 0.05:
        return position, (0.0, 0.0, 0.0)

    direction = vec_normalize(direction)
    
    # convert direction into actual velocity
    velocity = vec_mul(direction, speed)
    
    new_position = vec_add(position, vec_mul(velocity, dt))
    return new_position, velocity