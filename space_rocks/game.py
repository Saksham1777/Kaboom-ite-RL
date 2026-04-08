import pygame
import random
import numpy as np
import sys
from pygame.math import Vector2
from utils import load_sprite, get_random_velocity, get_formatted_time, get_toroidal_distance,get_toroidal_vector
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
        self.last_ast_spawn_time = 0
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

        # bullet
        self.last_shot_time = 0
        self.shoot_cooldown = 300
        self.ep_shot_fired = 0
        self.ep_asteroids_hit = 0

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
        self.last_ast_spawn_time = self.start_time
        self.ast_spawn_interval = 3000
        self.asteroid_min_speed = 1
        self.asteroid_max_speed = 3
        
        self.power_up_expiry = 0
        self.last_power_up_spawn_time = 0
        self.active_powerup_type = ""
        
        self.score = 0
        self.last_shot_time = 0
        self.ep_shot_fired = 0
        self.ep_asteroids_hit = 0
        
        # spawn initial asteroids
        for _ in range(10):
            while True:
                position = Vector2(random.randrange(800), random.randrange(600))
                if position.distance_to(self.spaceship.position) > self.MIN_ASTEROID_DISTANCE:
                    break       
        
            velocity = get_random_velocity(self.asteroid_min_speed, self.asteroid_max_speed)
            self.asteroids.append(Asteroid(position, velocity))
        

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
            'destroyed': 0,
            #'shield_hit': 0,
            #'powerup': 0,
            'died': False,
            'fired': False
        }
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Apply AI Action (if ship is alive)
        if not self.done and self.spaceship:
            if action == self.spaceship.ACTION_SHOOT:
                # post cooldown time post last shot
                if current_time > self.last_shot_time + self.shoot_cooldown:
                    # bullet can be considered
                    bullet = self.spaceship.apply_action(action, current_time, self.start_time)
                    if bullet:
                        self.ep_shot_fired += 1
                        self.last_shot_time = current_time
                        self.bullets.append(bullet)
                        self.current_events['fired'] = True
                        
            else:    
                self.spaceship.apply_action(action, current_time, self.start_time)

        # Run Physics and Collisions
        self._process_game_logic(current_time)

        # Check step limits
        self.current_step += 1
        if self.current_step >= self.max_steps:
            self.truncated = True
            self.done = True

        # Calculate results
        reward = self._calculate_reward(action)
        obs = self._get_obs()

        survival_time_ms = current_time - self.start_time
        info = {
            'survival_time_ms': survival_time_ms,
            'score': self.score,
            'died': self.current_events['died'],
            'reward_components': self.last_reward_components,
            'ep_shots_fired': self.ep_shot_fired,     
            'ep_asteroids_hit': self.ep_asteroids_hit  
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
                    self.current_events['destroyed'] += 1 
                    self.ep_asteroids_hit += 1
                    
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
                        self.current_events['died'] = True # 
                        break
                    else:
                        self.asteroids.remove(asteroid)
                        # self.current_events['shield_hit'] += 1 
                        # can add small incentive to crash into some asteroids... 

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
            if current_time - self.last_ast_spawn_time > self.ast_spawn_interval:
                if elapsed_ms < 4000:
                    spawn_count = 1
                else:
                    spawn_count = 1 + (elapsed_ms // 20000)

                spawn_count = min(spawn_count, 10)
                
                for _ in range(spawn_count):
                    self.add_asteroid()
                
                self.last_ast_spawn_time = current_time

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
            ship_vel_x = self.spaceship.velocity.x / 12
            ship_vel_y = self.spaceship.velocity.y / 12
            ship_sin, ship_cos = self.spaceship.get_angle_obs()
            ship_ang_vel = self.spaceship.angular_velocity / 0.5
        else:
            ship_vel_x, ship_vel_y, ship_sin, ship_cos, ship_ang_vel = 0.0, 0.0, 0.0, 0.0, 0.0

        # --- Sort asteroids FIRST so we can use sorted_asteroids everywhere below ---
        asteroid_obs = []
        alignment_to_closest = 0.0
        dist_to_closest = 1.0

        if self.asteroids and self.spaceship:
            sorted_asteroids = sorted(
                self.asteroids[:],
                key=lambda ast: get_toroidal_distance(self.spaceship.position, ast.position)
            )

            # Alignment + distance to closest asteroid
            closest_vec = get_toroidal_vector(self.spaceship.position, sorted_asteroids[0].position)
            dist_to_closest = get_toroidal_distance(
                self.spaceship.position, sorted_asteroids[0].position
            ) / 1000.0

            if closest_vec.length() > 0:
                alignment_to_closest = self.spaceship.get_direction().dot(closest_vec.normalize())
            else:
                alignment_to_closest = 0.0

            # 3 closest asteroids
            for i in range(3):
                if i < len(sorted_asteroids):
                    ast = sorted_asteroids[i]

                    px_rel_x = ast.position.x - self.spaceship.position.x
                    px_rel_y = ast.position.y - self.spaceship.position.y

                    if px_rel_x > 400:  px_rel_x -= 800
                    elif px_rel_x < -400: px_rel_x += 800

                    if px_rel_y > 300:  px_rel_y -= 600
                    elif px_rel_y < -300: px_rel_y += 600

                    asteroid_obs.extend([
                        px_rel_x / 800.0,
                        px_rel_y / 600.0,
                        ast.velocity.x / 10.0,
                        ast.velocity.y / 10.0
                    ])
                else:
                    asteroid_obs.extend([0.0, 0.0, 0.0, 0.0])
        else:
            asteroid_obs = [0.0] * 12

        # Bullet observations
        bullet_obs = []
        max_bullets_to_track = 3
        if self.spaceship and self.bullets:
            for i in range(max_bullets_to_track):
                if i < len(self.bullets):
                    b = self.bullets[i]
                    b_wrapped_vec = get_toroidal_vector(self.spaceship.position, b.position)
                    bullet_obs.extend([
                        b_wrapped_vec.x / 800,
                        b_wrapped_vec.y / 600,
                        b.velocity.x / 12,
                        b.velocity.y / 12
                    ])
                else:
                    bullet_obs.extend([0.0, 0.0, 0.0, 0.0])
        else:
            bullet_obs = [0.0] * (max_bullets_to_track * 4)

        ship_obs = [
            ship_vel_x, ship_vel_y,
            ship_sin, ship_cos,
            ship_ang_vel,
            alignment_to_closest,
            dist_to_closest
        ]

        obs = ship_obs + asteroid_obs + bullet_obs
        return np.array(obs, dtype=np.float32)  # shape: (29,)


    def _calculate_reward(self, action):
        """Returns the points earned (or lost) on this specific frame."""
        # Initialize components
        comp = {
            "survival": 0.0, 
            "death": 0.0, 
            "distance": 0.0, 
            #"movement_penalty": 0.0, 
            #"escape_reward": 0.0,
            "hit_reward" : 0.0,
            #"shoot_penalty" : 0.0,
            "aim_reward" : 0.0,
            "tracking_reward" : 0.0,
            "spin_penalty" : 0.0,
            "center_reward" : 0.0,
            "movement_reward" : 0.0
        }

        # 1. Death Penalty
        if self.current_events['died']:
            comp["death"] = -70.0
            self.last_reward_components = comp
            return -70.0

        if self.spaceship and not self.done:
            # 2. Base Survival 
            comp["survival"] = 0.02

            #if action in [self.spaceship.ACTION_FORWARD, self.spaceship.ACTION_BACKWARD]:
            #    comp["movement_penalty"] = -0.001
            #else:
            #    comp["movement_penalty"] = 0.0

            # 3. Center Bias Reward
            center_x, center_y = 400, 300
            center_pos = pygame.math.Vector2(center_x, center_y)
            dist_from_center = get_toroidal_distance(self.spaceship.position, center_pos)
            max_dist = 200  # approx corner distance
            comp["center_reward"] = max(0, (1 - dist_from_center / max_dist)) * 0.04
                        
            # 4. Destroying Asteroid Reward
            comp["hit_reward"] = self.current_events.get('destroyed', 0) * 7.0
            
            #comp["powerup_reward"] = self.current_events.get('powerup', 0) * 15.0

            comp['spin_penalty'] = -0.08 * abs(self.spaceship.angular_velocity)

            #speed = self.spaceship.velocity.length()
            #if speed > 1.0 and speed < 4.0: 
                #comp["movement_reward"] = 0.005
            
            
            if self.asteroids:
                
                sorted_asteroids = sorted(
                    self.asteroids, 
                     key=lambda ast: get_toroidal_distance(self.spaceship.position, ast.position)
                )[:3]

                ship_dir = self.spaceship.get_direction()

                closest = sorted_asteroids[0]
                closest_vec = get_toroidal_vector(self.spaceship.position, closest.position)
                closest_dist = get_toroidal_distance(self.spaceship.position, closest.position)
                if closest_vec.length() > 0:
                    alignment_to_closest = ship_dir.dot(closest_vec.normalize())
                    #comp["tracking_reward"] = alignment_to_closest * 0.005


                for i, ast in enumerate(sorted_asteroids):
                    # avoidance calculations
                    dist = get_toroidal_distance(self.spaceship.position, ast.position)
                    ast_to_ship_vec = get_toroidal_vector(self.spaceship.position, ast.position)

                    # float weights to closest asteroids
                    # 100% for 1st, 50% for 2nd, 33% for 3rd
                    w = 1.0 / (i + 1.0)

                    if dist < 200:
                        comp["distance"] -= ((200 - dist) / 200.0 ) * 0.2 * w
                    
                        # vector of rock to ship
                        #if ast_to_ship_vec.length() > 0: # Prevent division by zero
                        #    away_from_rock = ast_to_ship_vec.normalize()
                        #else:
                        #    away_from_rock = Vector2(0, 0)

                        # dot product of vel to see if it points away - reward for flying away
                        # +1 = perfectly opp, -1 = same direction
                        #escape_direction_score = self.spaceship.velocity.dot(away_from_rock)
                        #if escape_direction_score > 0:
                        #   comp["escape_reward"] += escape_direction_score * 0.1 * w
                                       
                # trigger discipline
                if self.current_events.get('fired', False):
                        if alignment_to_closest > 0.90:
                            comp['aim_reward'] = 1.5        # Perfect shot bonus
                            comp['shoot_penalty'] = 0.0     # Free shot
                        elif alignment_to_closest > 0.80:
                            comp['aim_reward'] = 0.6        # Good aim
                            comp['shoot_penalty'] = -0.4    # Small tax
                        elif alignment_to_closest > 0.65:
                            comp['aim_reward'] = 0.1        # Decent aim
                            comp['shoot_penalty'] = -0.9    # Moderate tax
                        else:
                            comp['aim_reward'] = 0.0
                            comp['shoot_penalty'] = -1.5    # Wild shot, full penalty
                                   
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
        while True:
            side = random.randint(0, 3)
            if side == 0: # Top
                position = Vector2(random.randrange(800), -40)
            elif side == 1: # Bottom
                position = Vector2(random.randrange(800), 640)
            elif side == 2: # Left
                position = Vector2(-40, random.randrange(600))
            else: # Right
                position = Vector2(840, random.randrange(600))

            # Ensure it doesn't wrap-spawn on top of the ship
            if get_toroidal_distance(self.spaceship.position, position) > self.MIN_ASTEROID_DISTANCE:
                break

            velocity = get_random_velocity(self.asteroid_min_speed, self.asteroid_max_speed)
            self.asteroids.append(Asteroid(position, velocity))