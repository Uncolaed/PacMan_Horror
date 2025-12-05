import math
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine import Engine
    from main import Game
    from core.map import Map


class RayCaster:
    def __init__(self, engine):
        self.engine = engine
        self.player = engine.player
        self.game: Game = engine.game
        self.width = self.game.WINDOW_WIDTH
        self.height = self.game.WINDOW_HEIGHT
        self.map: Map = engine.map

    def cast_rays(self):
        """Cast rays and return wall intersection data"""
        posX = self.player.position.x
        posY = self.player.position.y

        dirX, dirY = self.player.dir
        
        planeX, planeY = self.player.plane

        for x in range(self.width):

            # cameraX is the value is 1 on the right side of the screen and -1 on the left side and 0 in the center
            cameraX = 2 * x / self.width - 1

            rayDirX = dirX + planeX * cameraX
            rayDirY = dirY + planeY * cameraX
            rayDir = pg.Vector2(rayDirX, rayDirY)

            mapX = int(posX)
            mapY = int(posY)


            deltaDistX = abs(1 / rayDirX) if rayDirX != 0 else float("inf")
            deltaDistY = abs(1 / rayDirY) if rayDirY != 0 else float("inf")


            if rayDirX < 0:  # if player is looking left
                stepX = -1
                sideDistX = (posX - mapX) * deltaDistX
            else:  # player is looking right
                stepX = 1
                sideDistX = (mapX + 1.0 - posX) * deltaDistX
            if rayDirY < 0:  # if player is looking up
                stepY = -1
                sideDistY = (posY - mapY) * deltaDistY
            else:  # player is looking down
                stepY = 1
                sideDistY = (mapY + 1.0 - posY) * deltaDistY
            
            hit = False
            side = 0  # 0 -> hit on X side, 1 -> hit on Y side

            while not hit:
                if sideDistX < sideDistY:
                    sideDistX += deltaDistX
                    mapX += stepX
                    side = 0
                else:
                    sideDistY += deltaDistY
                    mapY += stepY
                    side = 1
                # Bounds check
                if (
                    mapX < 0 or mapX >= self.map.grid_x or
                    mapY < 0 or mapY >= self.map.grid_y
                ):
                    hit = True
                    break

                # Wall hit
                if self.map.map_grid[mapY][mapX] > 0:
                    hit = True

                if not hit:
                    continue
                
                if side == 0:
                    perpWallDist = (sideDistX - deltaDistX  );                
                else:
                    perpWallDist = (sideDistY - deltaDistY);

                #avoid division by zero or extremely small distances
                if perpWallDist <= 1e-6:
                    perpWallDist = 1e-6

                # Return ray data for rendering
                yield {
                    'x': x,
                    'perpWallDist': perpWallDist,
                    'side': side
                }


