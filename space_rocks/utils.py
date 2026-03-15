import random
import pygame
import sys
import os
from pygame.math import Vector2

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # If running as an EXE, use the PyInstaller temp folder
        base_path = sys._MEIPASS
    except Exception:
        # If running normally, get the folder ABOVE 'space_rocks'
        # Since utils.py is in 'space_rocks', we go up one level
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, ".."))

    return os.path.join(base_path, relative_path)

def load_sprite(name, with_alpha=True):
    path = resource_path(os.path.join("space_rocks", "assets", "sprites", f"{name}.png"))
    try:
        surface = pygame.image.load(path)
    except pygame.error:
        print(f"Error: Could not find image at {path}")
        raise SystemExit()

    if with_alpha:
        return surface.convert_alpha()
    return surface.convert()

def load_sound(name):
    """Loads a sound file. Checks for .wav first, then .mp3"""
    path_wav = resource_path(os.path.join("space_rocks", "assets", "sounds", f"{name}.wav"))
    path_mp3 = resource_path(os.path.join("space_rocks", "assets", "sounds", f"{name}.mp3"))
    
    if os.path.exists(path_wav):
        return pygame.mixer.Sound(path_wav)
    elif os.path.exists(path_mp3):
        return pygame.mixer.Sound(path_mp3)
    else:
        print(f"Error: Could not find audio file {name} as .wav or .mp3")
        # Return a dummy sound so the game doesn't crash immediately
        return pygame.mixer.Sound(buffer=b'')

# Fix for the ImportError: This makes load_sounds do the same thing as load_sound
load_sounds = load_sound

def get_random_velocity(min_speed, max_speed):
    speed = random.uniform(min_speed, max_speed)
    angle = random.randrange(0, 360)
    return Vector2(speed, 0).rotate(angle)

def get_formatted_time(start_time):
    """Calculates elapsed time and returns a string in MM:SS format"""
    total_milliseconds = pygame.time.get_ticks() - start_time
    total_seconds = total_milliseconds // 1000
    
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    return f"{minutes:02}:{seconds:02}"