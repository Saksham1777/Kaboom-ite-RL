import random
import pygame
from pygame.math import Vector2
from pygame.transform import rotozoom
from utils import load_sprite

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
        distance_bw = self.position.distance_to(other_obj.position)
        return distance_bw < self.radius + other_obj.radius
    
class Spaceship(GameObject):
    
    _base_sprite = None
    

    def __init__(self, position, velocity):
        if Spaceship._base_sprite is None:
            Spaceship._base_sprite = pygame.transform.scale(
                load_sprite("spaceship"), (50, 50)
            )
        super().__init__(position, Spaceship._base_sprite, velocity)
        self.angle = 0
        self.base_acc = 0.4
        self.friction = 0.94
        self.max_base_speed = 10
    
    def rotate_to_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        diff = Vector2(mouse_pos) - self.position
        self.angle = Vector2(0,-1).angle_to(diff)
    
    def draw(self, surface):
        rotated_surface = pygame.transform.rotozoom(self.sprite, -self.angle, 1.0)
        rotated_rect = rotated_surface.get_rect(center=self.position)
        surface.blit(rotated_surface, rotated_rect)
    
    def accelerate(self, direction_vector, current_time, start_time):
        self.velocity += direction_vector * self.base_acc

        # gradually increase max speed over time
        elapsed_ms = current_time - start_time
        speed_growth = elapsed_ms / 25000   # grows every 25 seconds

        max_speed = self.max_base_speed + speed_growth

        if self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)
    
    def update(self):
        self.velocity *= self.friction

    def shoot(self):
        bullet_velocity = Vector2(0,-1).rotate(self.angle) * 12
        bullet_position = self.position # start at spaceship position
        return Bullet(bullet_position, bullet_velocity)

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
