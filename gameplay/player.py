import math
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine import Engine
    from main import Game
    from core.map import Map


class Player:
    def __init__(self, engine):
        self.engine: Engine = engine
        self.game: Game = engine.game
        self.map: Map = engine.map

        # ------------------------------
        # TILE-BASED SPAWN COORDINATES
        # ------------------------------
        if self.map.player_spawn:
            self.position = pg.Vector2(*self.map.player_spawn)
        else:
            self.position = pg.Vector2(1.5, 1.5)

        print(f"[Player] Spawned at tile coordinates: {self.position}")

        # ------------------------------
        # VIEW SETTINGS
        # ------------------------------
        self.fov = 66
        self.dir = pg.Vector2(-1.0, 0.0)   # Facing west
        self.plane = self.compute_plane(self.dir.x, self.dir.y, self.fov)

        # ------------------------------
        # MOVEMENT SETTINGS
        # ------------------------------
        self.speed = 1.5                  # tiles / second
        self.mouse_sensitivity = 0.001
        self.radius = 0.15                # collision padding

        # ------------------------------
        # INPUT STATE
        # ------------------------------
        self.actions = {
            "left": False, "right": False,
            "up": False, "down": False,
            "mouse_x": 0
        }

        # Mouse movement uses standard FPS convention (no inversion needed)
        # pygame.mouse.get_rel() returns positive when moving right

    # ----------------------------------------------------------
    # COMPUTE CAMERA PLANE
    # ----------------------------------------------------------
    @staticmethod
    def compute_plane(dirX, dirY, fov_degrees):
        plane_length = math.tan(math.radians(fov_degrees / 2))
        perpX = -dirY
        perpY = dirX
        length = math.hypot(perpX, perpY)
        return pg.Vector2(perpX / length * plane_length,
                          perpY / length * plane_length)

    # ----------------------------------------------------------
    # INPUT HANDLING
    # ----------------------------------------------------------
    def get_actions(self):
        keys = pg.key.get_pressed()
        self.actions["left"] = keys[pg.K_a]
        self.actions["right"] = keys[pg.K_d]
        self.actions["up"] = keys[pg.K_w]
        self.actions["down"] = keys[pg.K_s]

        mx, _ = pg.mouse.get_rel()
        # Use standard FPS mouse behavior: positive = move right = rotate right
        self.actions["mouse_x"] = mx

    # ----------------------------------------------------------
    # MAIN UPDATE
    # ----------------------------------------------------------
    def update(self):
        dt = self.game.dt

        # Rotate camera
        if self.actions["mouse_x"] != 0:
            angle = self.actions["mouse_x"] * self.mouse_sensitivity
            self.rotate(angle)

        # Move forward/back
        if self.actions["up"]:
            self.move(self.dir.x, self.dir.y, dt)
        if self.actions["down"]:
            self.move(-self.dir.x, -self.dir.y, dt)

        # Strafe left/right
        if self.actions["left"]:
            self.move(self.dir.y, -self.dir.x, dt)   # left = perpendicular counter-clockwise
        if self.actions["right"]:
            self.move(-self.dir.y, self.dir.x, dt)   # right = perpendicular clockwise

    # ----------------------------------------------------------
    # MOVEMENT WITH COLLISION
    # ----------------------------------------------------------
    def move(self, dx, dy, dt):
        speed = self.speed * dt

        new_x = self.position.x + dx * speed
        new_y = self.position.y + dy * speed

        # X-axis collision
        if not self.is_wall(new_x, self.position.y):
            self.position.x = new_x

        # Y-axis collision
        if not self.is_wall(self.position.x, new_y):
            self.position.y = new_y

    def is_wall(self, x, y):
        """Check if tile at (x, y) is solid."""
        tile_x = int(x)
        tile_y = int(y)

        if tile_x < 0 or tile_x >= self.map.grid_x:
            return True
        if tile_y < 0 or tile_y >= self.map.grid_y:
            return True

        return self.map.map_grid[tile_y][tile_x] > 0

    # ----------------------------------------------------------
    # ROTATION
    # ----------------------------------------------------------
    def rotate(self, angle):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Rotate direction vector
        old_x = self.dir.x
        self.dir.x = old_x * cos_a - self.dir.y * sin_a
        self.dir.y = old_x * sin_a + self.dir.y * cos_a

        # Rotate camera plane
        old_px = self.plane.x
        self.plane.x = old_px * cos_a - self.plane.y * sin_a
        self.plane.y = old_px * sin_a + self.plane.y * cos_a
