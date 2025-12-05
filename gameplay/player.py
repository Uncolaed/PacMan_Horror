import pygame as pg
import math
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.engine import Engine
class Player:
    def __init__(self,engine):
        self.engine:Engine = engine
        self.game = self.engine.game
        
        # Set player position from map spawn or default
        if self.engine.map.player_spawn:
            self.position = pg.Vector2(self.engine.map.player_spawn)
        else:
            self.position = pg.Vector2(50, 50)
            
        # Direction vector pointing forward
        self.dir = pg.Vector2(1, 0)
        self.speed = 150
        self.mouse_sensitivity = 0.0008
        self.actions = {"left": False, "right": False, "up": False, "down": False, "mouse_x": 0}
        
    def get_actions(self):
        keys = pg.key.get_pressed()
        self.actions['left'] = keys[pg.K_a]
        self.actions['right'] = keys[pg.K_d]
        self.actions['up'] = keys[pg.K_w]
        self.actions['down'] = keys[pg.K_s]
        
        mouse_rel = pg.mouse.get_rel()
        self.actions['mouse_x'] = mouse_rel[0]
                    
    def update(self):
        if self.actions["mouse_x"] != 0:
            dx = self.actions["mouse_x"]
            # Rotate direction vector based on mouse movement
            angle_delta = dx * self.mouse_sensitivity
            self.rotate_direction(angle_delta)
            self.actions["mouse_x"] = 0

        if self.actions["up"]: self.move_player(1)
        if self.actions["down"]: self.move_player(-1)
        if self.actions["left"]: self.strafe_player(-1)
        if self.actions["right"]: self.strafe_player(1)
        
    def is_colliding(self, x, y):
        rel_x = int(x) >> 6
        rel_y = int(y) >> 6
        return self.engine.map.map_grid[rel_y][rel_x]
    
    def rotate_direction(self, angle_delta):
        """Rotate the direction vector by the given angle (in radians)"""
        # Apply 2D rotation matrix: [cos(θ)  -sin(θ)] [x]
        #                          [sin(θ)   cos(θ)] [y]
        cos_a = math.cos(angle_delta)
        sin_a = math.sin(angle_delta)
        
        new_x = self.dir.x * cos_a - self.dir.y * sin_a
        new_y = self.dir.x * sin_a + self.dir.y * cos_a
        
        self.dir.x = new_x
        self.dir.y = new_y

    def move_player(self, direction):
        # Use consistent speed calculation
        speed = self.speed * self.game.dt
        newx = self.position.x + self.dir.x * speed * direction
        newy = self.position.y + self.dir.y * speed * direction
        if not self.is_colliding(newx, newy):
            self.position.x = newx
            self.position.y = newy

    def strafe_player(self, direction):
        # Strafe perpendicular to direction vector (rotated 90 degrees)
        strafe_x = -self.dir.y
        strafe_y = self.dir.x
        
        speed = self.speed * self.game.dt
        newx = self.position.x + strafe_x * speed * direction
        newy = self.position.y + strafe_y * speed * direction
        
        if not self.is_colliding(newx, newy):
            self.position.x = newx
            self.position.y = newy

    def _draw_player_on_minimap(self):
        """Calculate player position on minimap and draw player indicator"""
        map: Map = self.engine.map
        player = self.engine.player
        
        # Get player world position
        player_x = player.position.x
        player_y = player.position.y
        player_dir = player.dir  # Get direction vector
        
        # Calculate world dimensions
        map_w = map.grid_x * map.grid_size
        map_h = map.grid_y * map.grid_size
        
        # Calculate minimap dimensions
        mini_size = min(self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT) * self.minimap_scale
        aspect_ratio = map_w / map_h
        mini_w = mini_size * aspect_ratio
        mini_h = mini_size
        
        # Position of minimap (top-left with padding)
        mini_x = self.minimap_padding
        mini_y = self.minimap_padding
        
        # Scale player position to minimap coordinates
        scaled_px = mini_x + (player_x / map_w) * mini_w
        scaled_py = mini_y + (player_y / map_h) * mini_h
        
        # Draw player as a small circle
        glColor3f(0.0, 1.0, 0.0)  # Green
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(scaled_px, scaled_py)
        radius = 4
        for i in range(21):
            angle = 2 * math.pi * i / 20
            glVertex2f(scaled_px + radius * math.cos(angle), 
                      scaled_py + radius * math.sin(angle))
        glEnd()
        
        # Draw player direction indicator using direction vector
        line_length = 8
        glColor3f(1.0, 0.0, 0.0)  # Red
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(scaled_px, scaled_py)
        glVertex2f(scaled_px + player_dir.x * line_length, 
                  scaled_py + player_dir.y * line_length)
        glEnd()