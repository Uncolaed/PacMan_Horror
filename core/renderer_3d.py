import math
import pygame as pg
from OpenGL.GL import *
from OpenGL.GLU import * 
from typing import TYPE_CHECKING
from core.raycaster import RayCaster

if TYPE_CHECKING:
    from core.engine import Engine
    from main import Game
    from core.map import Map
    from textures.texture_manager import TextureManager, TextureID


class Renderer3D:
    def __init__(self, engine):
        self.engine = engine
        self.player = engine.player
        self.game: Game = engine.game
        self.width = self.game.WINDOW_WIDTH
        self.height = self.game.WINDOW_HEIGHT
        self.map: Map = engine.map
        self.textureManger: TextureManager = engine.texture_manager
        self.raycaster = RayCaster(engine)
        # Initialize the screen buffer (RGB values for each pixel)
        self.buffer = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]

    def draw3D(self):
        self.clear_buffer()
        self.render_walls()
        self.draw_buffer()

    def clear_buffer(self):
        for y in range(self.height):
            for x in range(self.width):
                if y < self.height // 2:
                    # Ceiling color (dark gray)
                    self.buffer[y][x] = (50, 50, 50)
                else:
                    # Floor color (darker gray)
                    self.buffer[y][x] = (30, 30, 30)

    def draw_buffer(self):
        glBegin(GL_POINTS)
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.buffer[y][x]
                glColor3f(r / 255.0, g / 255.0, b / 255.0)
                glVertex2f(x, y)
        glEnd()

    def render_walls(self):
        from textures.texture_manager import TextureID
        
        texWidth = self.textureManger.width
        texHeight = self.textureManger.height

        for ray_data in self.raycaster.cast_rays():
            x = ray_data['x']
            perpWallDist = ray_data['perpWallDist']
            side = ray_data['side']
            mapX = ray_data['mapX']
            mapY = ray_data['mapY']
            wallX = ray_data['wallX']
            rayDirX = ray_data['rayDirX']
            rayDirY = ray_data['rayDirY']

            # Calculate distance to wall
            lineHeight = int(self.height / perpWallDist)   

            drawStart = -lineHeight // 2 + self.height // 2
            if drawStart < 0:
                drawStart = 0
            drawEnd = lineHeight // 2 + self.height // 2
            if drawEnd >= self.height:
                drawEnd = self.height - 1

            # Start texturing
            texNum = self.map.map_grid[mapY][mapX] - 1
            
            texX = int(wallX * texWidth)
            if side == 0 and rayDirX > 0:
                texX = texWidth - texX - 1
            if side == 1 and rayDirY < 0:
                texX = texWidth - texX - 1

            step = 1.0 * texHeight / lineHeight

            texPos = (drawStart - self.height / 2 + lineHeight / 2) * step
            
            for y in range(drawStart, drawEnd):
                texY = int(texPos) & (texHeight - 1)                    
                texPos += step

                color = self.textureManger.get_pixel(TextureID.BRICK, texX, texY)
                r, g, b = color

                # Darken Y-side walls for depth perception
                if side == 1:
                    r = r // 2
                    g = g // 2
                    b = b // 2

                self.buffer[y][x] = (r, g, b)