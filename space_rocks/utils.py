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


def get_random_velocity(min_speed, max_speed):
    speed = random.uniform(min_speed, max_speed)
    angle = random.randrange(0, 360)
    return Vector2(speed, 0).rotate(angle)

def get_formatted_time(current_time, start_time):
    """Calculates elapsed time and returns a string in MM:SS format"""
    total_milliseconds = current_time - start_time
    total_seconds = total_milliseconds // 1000
    
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    return f"{minutes:02}:{seconds:02}"