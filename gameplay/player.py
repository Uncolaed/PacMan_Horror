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
            
        self.position_delta = pg.Vector2()
        self.speed = 150
        self.player_angle = 1
        self.mouse_sensitivity = 0.003
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
            # Remove the (60 * dt) - it's redundant without FPS cap
            self.player_angle += dx * self.mouse_sensitivity

            if self.player_angle > 2 * math.pi: 
                self.player_angle -= 2 * math.pi
            if self.player_angle < 0: 
                self.player_angle += 2 * math.pi

            self.rotate_player()
            self.actions["mouse_x"] = 0

        if self.actions["up"]: self.move_player(1)
        if self.actions["down"]: self.move_player(-1)
        if self.actions["left"]: self.strafe_player(-1)
        if self.actions["right"]: self.strafe_player(1)
        
    def is_colliding(self, x, y):
        rel_x = int(x) >> 6
        rel_y = int(y) >> 6
        return self.engine.map.map_grid[rel_y][rel_x]
    
    def rotate_player(self):
        # This can stay as-is for direction vector
        self.position_delta.x = math.cos(self.player_angle)
        self.position_delta.y = math.sin(self.player_angle)

    def move_player(self, direction):
        # Use consistent speed calculation
        speed = self.speed * self.game.dt
        newx = self.position.x + self.position_delta.x * speed * direction
        newy = self.position.y + self.position_delta.y * speed * direction
        if not self.is_colliding(newx, newy):
            self.position.x = newx
            self.position.y = newy

    def strafe_player(self, direction):
        strafe_angle = self.player_angle + math.pi / 2
        strafe_x = math.cos(strafe_angle)
        strafe_y = math.sin(strafe_angle)
        
        speed = self.speed * self.game.dt
        newx = self.position.x + strafe_x * speed * direction
        newy = self.position.y + strafe_y * speed * direction
        
        if not self.is_colliding(newx, newy):
            self.position.x = newx
            self.position.y = newy