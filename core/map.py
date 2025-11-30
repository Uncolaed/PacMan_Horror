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

    def draw(self):
        y = 0
        for layer in self.map_grid:
            x = 0
            for tile in layer:
                x_off, y_off = x * self.grid_size, y * self.grid_size
                # Empty space, do nothing
                if tile == 1: glColor3f(1,1,1)
                else: glColor3f(0,0,0)
                glBegin(GL_QUADS)
                glVertex2i(x_off, y_off)
                glVertex2i(x_off, y_off + self.grid_size)
                glVertex2i(x_off + self.grid_size, y_off + self.grid_size)
                glVertex2i(x_off + self.grid_size, y_off)
                glEnd()
                
                # Draw grid lines
                glColor3f(0.5, 0.5, 0.5)
                glLineWidth(1)
                glBegin(GL_LINE_LOOP)
                glVertex2i(x_off, y_off)
                glVertex2i(x_off, y_off + self.grid_size)
                glVertex2i(x_off + self.grid_size, y_off + self.grid_size)
                glVertex2i(x_off + self.grid_size, y_off)
                glEnd()
                
                x +=1
            y+=1

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