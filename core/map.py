import pygame, os,csv

from OpenGL.GL import *
from OpenGL.GLU import *

class Map():
    def __init__(self, game):
        self.game = game
        self.grid_x, self.grid_y = 8,8
        self.grid_size = 64
        self.map_file_name = 'level.csv'
        self.player_spawn = None
        self.load_world()

    

    def load_world(self):
        # Loads the world from a csv file
        with open(os.path.join(self.game.dir, "maps",self.map_file_name)) as data:
            data = csv.reader(data,delimiter = ',')
            self.map_grid = []
            for row in data:
                self.map_grid.append(list(row))
            
            # Find player spawn and convert to int
            for y, row in enumerate(self.map_grid):
                for x, tile in enumerate(row):
                    if tile == 'P':
                        # Store spawn position (center of tile)
                        self.player_spawn = (x * self.grid_size + self.grid_size // 2, 
                                            y * self.grid_size + self.grid_size // 2)
                        # Replace 'P' with empty space (0)
                        self.map_grid[y][x] = 0
                    else:
                        # Convert string to int
                        self.map_grid[y][x] = int(tile)