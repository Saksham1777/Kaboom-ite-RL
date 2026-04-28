import random
import pygame
from pygame.math import Vector2
from pygame.transform import rotozoom
from utils import load_sprite, get_toroidal_distance
import math

UP = Vector2(0, -1)

# parent class
class GameObject:
    def __init__(self, postion, sprite, velocity):
        self.position = Vector2(postion)
        self.sprite = sprite
        self.radius = sprite.get_width() / 2
        self.velocity = Vector2(velocity)

    def draw(self, surface):
        # Centers the sprite
        blit_position = self.position - Vector2(self.radius)
        surface.blit(self.sprite, blit_position)

    def move(self, surface):
        self.position += self.velocity

        width = surface.get_width()
        height = surface.get_height()
        buffer = 50

        # Wrap X-axis
        if self.position.x > width + buffer:
            self.position.x = - buffer
        elif self.position.x < - buffer:
            self.position.x = width + buffer
        
        # Wrap Y-axis
        if self.position.y > height + buffer:
            self.position.y = -buffer
        elif self.position.y < -buffer:
            self.position.y = height + buffer
    
    def collision_with(self, other_obj):
        distance_bw = get_toroidal_distance(self.position, other_obj.position)
        return distance_bw < self.radius + other_obj.radius
    
class Spaceship(GameObject):
   
    _base_sprite = None

    #ROTATE_SMALL = math.radians(2)
    ROTATE_BIG = math.radians(1.5)

    # action id mapping
    ACTION_NOOP      = 0
    ACTION_FORWARD   = 1
    ACTION_BACKWARD  = 2 
    #ACTION_ROT_L_SM  = 3
    #ACTION_ROT_R_SM  = 4
    ACTION_ROT_L_BG  = 3
    ACTION_ROT_R_BG  = 4
    ACTION_SHOOT     = 5  
    N_ACTIONS        = 6

    
    def __init__(self, position, velocity):
        if Spaceship._base_sprite is None:
            Spaceship._base_sprite = pygame.transform.scale(
                load_sprite("spaceship"), (50, 50)
            )
        super().__init__(position, Spaceship._base_sprite, velocity)
        
        self.angle_rad = 0.0
        self.angular_velocity = 0.0

        # physics constants
        self.base_acc = 0.4
        self.friction = 0.94
        self.angular_friction = 0.70 
        self.max_base_speed = 10
    
    
    def apply_action(self, action: int, current_time: int, start_time: int):
        if action == self.ACTION_NOOP:
            pass
        elif action == self.ACTION_FORWARD:
            self.apply_thrust(1,current_time, start_time)
        elif action == self.ACTION_BACKWARD:
            self.apply_thrust(-1, current_time, start_time)
        #elif action == self.ACTION_ROT_L_SM:
        #    self.rotate(-self.ROTATE_SMALL)        
        #elif action == self.ACTION_ROT_R_SM:
        #    self.rotate(+self.ROTATE_SMALL)         
        elif action == self.ACTION_ROT_L_BG:
            self.rotate(-self.ROTATE_BIG)           
        elif action == self.ACTION_ROT_R_BG:
            self.rotate(+self.ROTATE_BIG)           
        elif action == self.ACTION_SHOOT:
            return self.shoot()


    def rotate(self, angular_thrust: float):
        self.angular_velocity += angular_thrust

    def get_direction(self):
        # unit vector of curr dir - used by acc + shoot
        return Vector2(math.sin(self.angle_rad), -math.cos(self.angle_rad))
    
    def get_angle_obs(self):
        # tuple output for rl observer
        return math.sin(self.angle_rad), math.cos(self.angle_rad)
    
    def apply_thrust(self, factor, current_time, start_time):
        # acc - forward and backward combined code
        # +1 for forward, -1 for backward
        direction = self.get_direction()
        self.velocity += direction * (self.base_acc * factor)

        # dynamic speed logic
        elapsed_time = current_time - start_time
        max_speed = self.max_base_speed + elapsed_time / 25000

        if self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)

    def update(self):
        # engine of linear and rotationaly velocity - called every frame 
        # hence friction calculation must be here
        
        # linear phy
        self.velocity *= self.friction

        # angular phy
        dt = 1 # implicit delta time = 1
        self.angle_rad += self.angular_velocity * dt 
        self.angular_velocity *= self.angular_friction

        self.angle_rad = math.atan2(math.sin(self.angle_rad) , math.cos(self.angle_rad))

    def shoot(self):
        direction = self.get_direction()
        bullet_velocity = direction * 12
        bullet_position = self.position # start at spaceship position
        return Bullet(bullet_position, bullet_velocity)

    def draw(self, surface):
        angle_deg = math.degrees(self.angle_rad)
        rotated_surface = pygame.transform.rotozoom(self.sprite, -angle_deg, 1.0)
        rotated_rect = rotated_surface.get_rect(center=self.position)
        surface.blit(rotated_surface, rotated_rect)

class Asteroid(GameObject):

    _base_sprite = None

    def __init__(self, position, velocity):
        if Asteroid._base_sprite is None:
            Asteroid._base_sprite = pygame.transform.scale(
                load_sprite("asteroid"), (60, 60)
            )
        
        super().__init__(position, Asteroid._base_sprite, velocity)
        self.angle = 0
        self.rotation_speed = random.uniform(-5, 5)

    def draw(self, surface):
        self.angle += self.rotation_speed
        # Rotozoom is smoother than scale
        rotated_surface = rotozoom(self.sprite, self.angle, 1.0)
        # Force the center to stay put 
        rotated_rect = rotated_surface.get_rect(center=self.position)
        surface.blit(rotated_surface, rotated_rect)

class Bullet(GameObject):

    def __init__(self, position, velocity):
        sprite = pygame.transform.scale(
                load_sprite("bullet"), (10, 10)
            )
        super().__init__(position, sprite, velocity)

    def move(self, surface):
        self.position += self.velocity    

class PowerUp(GameObject):

    def __init__(self, position, type):
        sprite = pygame.transform.scale(
                load_sprite(f"powerup_{type}"), (20, 20)
            )
        super().__init__(position, sprite, Vector2(0, 1))

        self.type = type