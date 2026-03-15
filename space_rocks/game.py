import pygame
import random
import sys
from pygame.math import Vector2
from utils import load_sprite, get_random_velocity, get_formatted_time, load_sounds
from models import Spaceship, Asteroid, Bullet

class SpaceRocks:
    MIN_ASTEROID_DISTANCE = 250

    def __init__(self):
        self.init_pygame()
        self.screen = pygame.display.set_mode((800,600))
        self.font = pygame.font.SysFont("arial.ttf", 64)
        self.ui_font = pygame.font.SysFont("arial.ttf", 20)
        self.clock = pygame.time.Clock()

        # background image
        og_background = load_sprite("space_bck", False)
        self.background = pygame.transform.scale(og_background, (800, 600))
        
        # Start the game in a "Waiting" state
        self.spaceship = None
        self.asteroids = []
        self.bullets = []
        self.message = "Press ENTER to Start"
        self.start_time = 0
        self.last_spwan_time = 0
        self.score = 0
        self.spawn_interval = 3000
        self.asteroid_min_speed = 1
        self.asteroid_max_speed = 3
        self.start_sound = load_sounds("igotthis")
        self.diss_sound = load_sounds("disappointed")
        self.die_sound = load_sounds("fahh")
        self.bruh_sound = load_sounds("bruh")
        self.wow_sound = load_sounds("wow")
        self.gun_sound = load_sounds("gun")
        self.blast_sound = load_sounds("blast")
        self.blast_sound.set_volume(0.7)


    def init_pygame(self):
        pygame.init()
        pygame.display.set_caption("Space Rocks")

    def _start_game(self):
        """Initializes or resets the game state"""
        if self.start_sound:
            self.start_sound.play()

        self.spaceship = Spaceship((400,300), (0,0))
        self.message = ""
        self.bullets = []
        self.asteroids = []
        self.start_time = pygame.time.get_ticks()

        # reset
        self.last_spwan_time = self.start_time
        self.spawn_interval = 3000
        self.asteroid_min_speed = 1
        self.asteroid_max_speed = 3
        self.score = 0
        
        for _ in range(10):
            while True:
                position = Vector2(random.randrange(800), random.randrange(600))
                if position.distance_to(self.spaceship.position) > self.MIN_ASTEROID_DISTANCE:
                    break       
        
            velocity = get_random_velocity(self.asteroid_min_speed, self.asteroid_max_speed)
            self.asteroids.append(Asteroid(position, velocity))

    def main_loop(self):
        while True:
            self._handle_input()
            self._process_game_logic()
            self._draw()

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle Enter to start or restart
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not self.spaceship:
                    self._start_game()

            # Only shoot if spaceship exists
            if self.spaceship and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.gun_sound.play()
                self.bullets.append(self.spaceship.shoot())

        # Movement input check
        if self.spaceship:
            is_key_pressed = pygame.key.get_pressed()
            current_time = pygame.time.get_ticks()
            move_dir = Vector2(0, 0)

            if is_key_pressed[pygame.K_w]: move_dir.y -= 1
            if is_key_pressed[pygame.K_s]: move_dir.y += 1
            if is_key_pressed[pygame.K_a]: move_dir.x -= 1
            if is_key_pressed[pygame.K_d]: move_dir.x += 1

            if move_dir.length() > 0:
                self.spaceship.accelerate(move_dir.normalize(), current_time, self.start_time)

    def _process_game_logic(self):
        # Bullet movement and removal
        for bullet in self.bullets[:]:
            bullet.move(self.screen)
            storage_rect = self.screen.get_rect().inflate(100, 100)
            if not storage_rect.collidepoint(bullet.position):
                self.bullets.remove(bullet)
        
        # Asteroid movement
        for asteroid in self.asteroids:
            asteroid.move(self.screen)

        # Bullet-Asteroid collision
        for asteroid in self.asteroids[:]:
            for bullet in self.bullets[:]:
                if bullet.position.distance_to(asteroid.position) < asteroid.radius:
                    self.score += 1
                    self.blast_sound.play()
                    if self.score > 20 and self.score % 5 == 0:
                        self.wow_sound.play()
                    if asteroid in self.asteroids: self.asteroids.remove(asteroid)
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    break
        
        # Spaceship logic (Only if it exists)
        if self.spaceship:
            self.spaceship.rotate_to_mouse()
            self.spaceship.update()
            self.spaceship.move(self.screen)

            current_ticks = pygame.time.get_ticks()
            elapsed_ms = current_ticks - self.start_time
            
            if current_ticks - self.last_spwan_time > self.spawn_interval:
                if elapsed_ms < 4000:
                    spawn_count = 1
                else:
                    spawn_count = 1 + (elapsed_ms // 20000)

                spawn_count = min(spawn_count, 10)
                
                for _ in range(spawn_count):
                    self.add_asteroid()
                
                self.last_spwan_time = current_ticks

                # increase spawn rate
                if self.spawn_interval > 1200:
                    self.spawn_interval -= 100
                
                if self.asteroid_max_speed < 10:
                    self.asteroid_min_speed += 0.05
                    self.asteroid_max_speed += 0.1

            # Spaceship-asteroid collision
            for asteroid in self.asteroids:
                if asteroid.collision_with(self.spaceship):
                    i = random.randint(1,3)
                    print(f"Random sound chosen: {i}")
                    if i == 1:
                        self.diss_sound.play()
                    elif i == 2: 
                        self.die_sound.play()
                    else :
                        self.bruh_sound.play()

                    final_time = get_formatted_time(self.start_time)
                    self.spaceship = None
                    self.message = f"GAME OVER! Score: {self.score} | Time: {final_time}"
                    break

    def _draw(self):
        self.screen.blit(self.background, (0,0))

        # Only draw player if alive
        if self.spaceship:
            self.spaceship.draw(self.screen)

            time_str = get_formatted_time(self.start_time)
            text_time = self.ui_font.render(f"Time: {time_str}", True, (255, 255, 255))
            text_score = self.ui_font.render(f"Score: {self.score}", True, (255, 255, 255))
            self.screen.blit(text_score, (10, 40))
            self.screen.blit(text_time, (10, 10))
         
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
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