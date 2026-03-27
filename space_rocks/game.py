import pygame
import random
import numpy as np
import sys
from pygame.math import Vector2
from utils import load_sprite, get_random_velocity, get_formatted_time
from models import Spaceship, Asteroid, PowerUp

class SpaceRocks:
    MIN_ASTEROID_DISTANCE = 250 

    def __init__(self, render_mode=False):
        self.init_pygame()
        self.screen = pygame.display.set_mode((800,600))
        self.font = pygame.font.SysFont("arial.ttf", 64)
        self.ui_font = pygame.font.SysFont("arial.ttf", 20)
        self.clock = pygame.time.Clock()

        # background image
        og_background = load_sprite("space_bck", False)
        self.background = pygame.transform.scale(og_background, (800, 600))
        
        # Start the game in a "Waiting" state 
        self.message = ""
        self.start_time = 0
        self.virtual_time = 0.0 # rl train time
        self.score = 0
        self.spaceship = None
        self.bullets = []
        self.max_steps = 10000

        # asteroid
        self.asteroids = []
        self.last_ast_spwan_time = 0
        self.ast_spawn_interval = 3000
        self.asteroid_min_speed = 1
        self.asteroid_max_speed = 3

        # power up
        self.power_up = []
        self.active_powerup_type = ""
        self.power_up_expiry = 0
        self.last_power_up_spawn_time = 0
        self.power_up_spawn_interval = 10000
        self.power_up_lasts_interval = 5000

        # RL Episode Management
        self.max_steps = 3000  # 3000 frames = ~50 seconds at 60fps
        self.current_step = 0
        self.done = False
        self.truncated = False

        self.render_mode = render_mode
        if render_mode:
            self.screen = pygame.display.set_mode((800, 600))
        else:
            self.screen = pygame.Surface((800, 600))


    def init_pygame(self):
        pygame.init()
        pygame.display.set_caption("Space Rocks")

    def reset(self):
        """Resets the environment for a new episode and returns initial observation."""

        self.spaceship = Spaceship((400,300), (0,0))
        self.bullets = []
        self.asteroids = []
        self.power_up = []
        
        self.start_time = 0
        self.virtual_time = 0

        # rl
        self.current_step = 0
        self.done = False
        self.truncated = False
        # self.closest_clean_dist = 25 use?

        # reset
        self.last_ast_spwan_time = self.start_time
        self.ast_spawn_interval = 3000
        self.asteroid_min_speed = 1
        self.asteroid_max_speed = 3
        self.power_up_expiry = 0
        self.last_power_up_spawn_time = 0
        self.score = 0
        self.active_powerup_type = ""
        
        # spawn initial asteroids
        for _ in range(10):
            while True:
                position = Vector2(random.randrange(800), random.randrange(600))
                if position.distance_to(self.spaceship.position) > self.MIN_ASTEROID_DISTANCE:
                    break       
        
            velocity = get_random_velocity(self.asteroid_min_speed, self.asteroid_max_speed)
            self.asteroids.append(Asteroid(position, velocity))
        
        self.prev_ship_pos = Vector2(self.spaceship.position)
        self.frames_still = 0
        if self.asteroids:
            closest_ast = min(self.asteroids, key=lambda a: self.spaceship.position.distance_to(a.position))
            self.prev_closest_dist = self.spaceship.position.distance_to(closest_ast.position)
        else:
            self.prev_closest_dist = float('inf')

        return self._get_obs()

    def step(self, action):
        """Takes an action, advances the game one frame, and returns results."""
        
        self.virtual_time += 1000 / 60.0
        current_time = int(self.virtual_time)

        # Initialize frame events for the reward calculator
        self.current_events = {
            #'destroyed': 0,
            #'shield_hit': 0,
            #'powerup': 0,
            'died': False,
            #'fired': False
        }
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Apply AI Action (if ship is alive)
        if not self.done and self.spaceship:
            self.spaceship.apply_action(action, current_time, self.start_time)

        # Run Physics and Collisions
        self._process_game_logic(current_time)

        # Check step limits
        self.current_step += 1
        if self.current_step >= self.max_steps:
            self.truncated = False
            self.done = True

        # Calculate results
        reward = self._calculate_reward()
        obs = self._get_obs()

        survival_time_ms = current_time - self.start_time
        info = {
            'survival_time_ms': survival_time_ms,
            'score': self.score,
            'died': self.current_events['died'],
            'reward_components': self.last_reward_components
        }

        # standard rl tuple : (observation, reward, done, info)
        return obs, reward, self.done, info


    def _process_game_logic(self, current_time:int):

        # Bullet movement and removal
        for bullet in self.bullets[:]:
            bullet.move(self.screen)
            storage_rect = self.screen.get_rect().inflate(100, 100)
            if not storage_rect.collidepoint(bullet.position):
                self.bullets.remove(bullet)
        
        # Asteroid movement
        for asteroid in self.asteroids:
            asteroid.move(self.screen)
        
        # Power-up spawn and despawn disabled to focus RL on survival
        
        # if current_time > self.last_power_up_spawn_time + self.power_up_lasts_interval:
        #     self.power_up.clear()

        # if current_time > self.last_power_up_spawn_time + self.power_up_spawn_interval:
        #     powerup_postion = Vector2(random.randint(100, 700), random.randint(100, 500))
        #     types = ['penetration', 'shield']
        #     selected_type = random.choice(types)
        #     self.power_up.append(PowerUp(powerup_postion, selected_type))
        #     self.last_power_up_spawn_time = current_time
        

        # Bullet-Asteroid collision
        for asteroid in self.asteroids[:]:
            for bullet in self.bullets[:]:
                if bullet.position.distance_to(asteroid.position) < asteroid.radius:
                    self.score += 1
                    # shooting not defined yet for base rl
                    #self.current_events['destroyed'] += 1 # LOG EVENT
                    self.asteroids.remove(asteroid)
                    
                    is_penetrating = (self.active_powerup_type == "penetration" and current_time < self.power_up_expiry)
                    
                    if not is_penetrating:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                    break
        
        # Spaceship-Asteroid Collision 
        if not self.done and self.spaceship:
            for asteroid in self.asteroids[:]:
                if asteroid.collision_with(self.spaceship):
                    
                    is_shield_active = (self.active_powerup_type == "shield" and current_time < self.power_up_expiry)

                    if not is_shield_active:
                        self.done = True # Set flag instead of destroying spaceship
                        self.current_events['died'] = True # LOG EVENT
                        break
                    else:
                        self.asteroids.remove(asteroid)
                        self.current_events['shield_hit'] += 1 # LOG EVENT
                        # Allowing multi hit shield

        # Spaceship-PowerUp Collision 
        
        # Disabled power-up collision detection
        
        # if not self.done and self.spaceship: 
        #     for p in self.power_up[:]:
        #         if self.spaceship.collision_with(p):
        #             self.active_powerup_type = p.type 
        #             self.power_up_expiry = current_time + self.power_up_lasts_interval
        #             self.current_events['powerup'] += 1 # LOG EVENT
        #             self.power_up.remove(p)

        
        # Spaceship logic (Only if it exists)
        if not self.done and self.spaceship:
            self.spaceship.update()
            self.spaceship.move(self.screen)

            # Asteroid Scaling
            elapsed_ms = current_time - self.start_time
            if current_time - self.last_ast_spwan_time > self.ast_spawn_interval:
                if elapsed_ms < 4000:
                    spawn_count = 1
                else:
                    spawn_count = 1 + (elapsed_ms // 20000)

                spawn_count = min(spawn_count, 10)
                
                for _ in range(spawn_count):
                    self.add_asteroid()
                
                self.last_ast_spwan_time = current_time

                # Gradually increase difficulty
                if self.ast_spawn_interval > 1200:
                    self.ast_spawn_interval -= 100
                
                # allowing max update of seed to be 10
                if self.asteroid_max_speed < 10: 
                    self.asteroid_min_speed += 0.05
                    self.asteroid_max_speed += 0.1 
    
    def _get_obs(self):
        """Returns the state of the game for the AI to 'see'."""
        
        if self.spaceship:
            ship_x = self.spaceship.position.x / 800
            ship_y = self.spaceship.position.y / 600

            # base max speed is 10 but allowed to increase to 12 in 50 sec
            ship_vel_x = self.spaceship.velocity.x / 12
            ship_vel_y = self.spaceship.velocity.y / 12

            ship_sin, ship_cos = self.spaceship.get_angle_obs()
        else:
            ship_x, ship_y, ship_vel_x, ship_vel_y, ship_sin, ship_cos = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        if self.asteroids and self.spaceship:
            # TO DO
            # can be made better to 3 closest soon
            closest_ast = min(self.asteroids, key=lambda ast: self.spaceship.position.distance_to(ast.position))

            rel_x = (closest_ast.position.x - self.spaceship.position.x) / 800
            rel_y = (closest_ast.position.y - self.spaceship.position.y) / 600

            ast_vel_x = closest_ast.velocity.x / 10 
            ast_vel_y = closest_ast.velocity.y / 10
        else:
            # If no asteroids or ship is dead
            rel_x, rel_y, ast_vel_x, ast_vel_y = 0.0, 0.0, 0.0, 0.0
        
        obs = [
            ship_x, ship_y,
            ship_vel_x, ship_vel_y,
            ship_sin, ship_cos,
            rel_x, rel_y,
            ast_vel_x, ast_vel_y
        ]

        # rl req float32
        return np.array(obs, dtype = np.float32)


    def _calculate_reward(self):
        """Returns the points earned (or lost) on this specific frame."""
        # Initialize components
        comp = {"survival": 0.0, "death": 0.0, "distance": 0.0, "still_penalty": 0.0}
        
        reward = 0.0

        if not self.done:
            comp["survival"] = 0.02

        #comp["hit_reward"] = self.current_events.get('destroyed', 0) * 10.0
        #comp["powerup_reward"] = self.current_events.get('powerup', 0) * 15.0

        if self.current_events['died']:
            comp["death"] = -50.0
            self.last_reward_components = comp
            return -50.0
        
        #if self.current_events.get('fired', False):
        #   comp["shooting_penalty"] = -0.1  

        if self.spaceship and not self.done:            
            if self.frames_still > 60: 
                comp["still_penalty"] = -0.5

            self.prev_ship_pos = Vector2(self.spaceship.position)
        
            if self.asteroids:
                closest_ast = min(self.asteroids, key=lambda a: self.spaceship.position.distance_to(a.position))
                curr_dist = self.spaceship.position.distance_to(closest_ast.position)

                if curr_dist < 150:
                    comp["distance"] = -(150 - curr_dist) / 1000.0
        
        self.last_reward_components = comp
        return sum(comp.values()) 

    def render(self):
        self.screen.blit(self.background, (0,0))

        # Only if player is alive
        if self.spaceship:
            self.spaceship.draw(self.screen)

            current_time = int(self.virtual_time)
            time_str = get_formatted_time(current_time, self.start_time)
            text_time = self.ui_font.render(f"Time: {time_str}", True, (255, 255, 255))
            text_score = self.ui_font.render(f"Score: {self.score}", True, (255, 255, 255))
            
            status = "None"
            if current_time < self.power_up_expiry:
                status = self.active_powerup_type
            
            power_up_str = self.ui_font.render(f"Active: {status}", True, (255, 255, 255))
            
            self.screen.blit(text_time, (10, 10))
            self.screen.blit(text_score, (10, 40))
            self.screen.blit(power_up_str, (650, 10))
         
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        for p in self.power_up:
            p.draw(self.screen) 
        
        # Render message text
        if self.message:
            text_surface = self.font.render(self.message, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(400, 300))
            self.screen.blit(text_surface, text_rect)

        pygame.display.flip()
        self.clock.tick(60)

    def add_asteroid(self):
        side = random.randint(0, 3)
        if side == 0: # Top
            position = Vector2(random.randrange(800), -40)
        elif side == 1: # Bottom
            position = Vector2(random.randrange(800), 640)
        elif side == 2: # Left
            position = Vector2(-40, random.randrange(600))
        else: # Right
            position = Vector2(840, random.randrange(600))

        velocity = get_random_velocity(self.asteroid_min_speed, self.asteroid_max_speed)
        self.asteroids.append(Asteroid(position, velocity))