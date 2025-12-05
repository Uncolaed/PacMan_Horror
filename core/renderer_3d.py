import math
import numpy as np
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
        self.game = engine.game
        self.width = self.game.WINDOW_WIDTH
        self.height = self.game.WINDOW_HEIGHT
        self.map = engine.map
        self.textureManger = engine.texture_manager
        self.raycaster = RayCaster(engine)
        
        # Main render buffer
        self.buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.half_height = self.height // 2
        
        # Texture stuff - set up once, use forever
        self.tex_width = None
        self.tex_height = None
        self.numpy_textures = {}
        
        # Fog config
        self.fog_start = -5
        self.fog_end = 5
        self.fog_color = np.array([10, 10, 10], dtype=np.uint8)
        
    def _load_textures(self):
        """Convert textures to numpy arrays for faster access"""
        from textures.texture_manager import TextureID
        
        if self.numpy_textures:
            return
            
        for tex_id in TextureID:
            if tex_id in self.textureManger.textures:
                texture_data = self.textureManger.textures[tex_id]
                self.numpy_textures[tex_id] = np.array(texture_data, dtype=np.uint8)
        
    def draw3D(self):
        self.clear_buffer()
        self.render_walls()
        self.draw_buffer()
    
    def clear_buffer(self):
        self._render_floor_ceiling()
    
    def draw_buffer(self):
        glDrawPixels(self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE, 
                     np.flipud(self.buffer))
    
    def render_walls(self):
        from textures.texture_manager import TextureID
        
        # First time setup
        if self.tex_width is None:
            self.tex_width = self.textureManger.width
            self.tex_height = self.textureManger.height
            self._load_textures()
        
        texture_np = self.numpy_textures[TextureID.BRICK]
        
        for ray_data in self.raycaster.cast_rays():
            x = ray_data['x']
            dist = ray_data['perpWallDist']
            
            if dist < 0.01:
                continue
            
            # Wall height based on distance
            wall_height = int(self.height / dist)
            draw_start = max(0, -wall_height // 2 + self.half_height)
            draw_end = min(self.height - 1, wall_height // 2 + self.half_height)
            
            if draw_start >= draw_end:
                continue
            
            # Figure out which part of the texture to use
            wall_x = ray_data['wallX']
            tex_x = int(wall_x * self.tex_width)
            
            # Flip texture on certain sides
            if ray_data['side'] == 0 and ray_data['rayDirX'] > 0:
                tex_x = self.tex_width - tex_x - 1
            if ray_data['side'] == 1 and ray_data['rayDirY'] < 0:
                tex_x = self.tex_width - tex_x - 1
            
            tex_x = max(0, min(self.tex_width - 1, tex_x))
            
            # Map texture vertically
            step = self.tex_height / wall_height
            tex_start = (draw_start - self.half_height + wall_height / 2) * step
            
            num_pixels = draw_end - draw_start
            tex_positions = tex_start + np.arange(num_pixels) * step
            tex_indices = tex_positions.astype(np.int32) & (self.tex_height - 1)
            
            # Grab the whole column at once
            colors = texture_np[tex_indices, tex_x]
            
            # Darken walls facing different direction
            if ray_data['side'] == 1:
                colors = colors >> 1
            
            # Add fog
            fog = self._calc_fog(dist)
            if fog > 0:
                colors = self._blend_fog(colors, fog)
            
            self.buffer[draw_start:draw_end, x] = colors
    
    def _calc_fog(self, distance):
        """How much fog? 0 = none, 1 = thick"""
        if distance < self.fog_start:
            return 0.0
        elif distance > self.fog_end:
            return 1.0
        return (distance - self.fog_start) / (self.fog_end - self.fog_start)
    
    def _blend_fog(self, colors, fog_amount):
        """Mix wall color with fog"""
        return (colors * (1 - fog_amount) + self.fog_color * fog_amount).astype(np.uint8)
    
    def _render_floor_ceiling(self):
        """Draw floor and ceiling with distance fade"""
        ceiling = np.array([50, 50, 50], dtype=np.float32)
        floor = np.array([30, 30, 30], dtype=np.float32)
        
        # Draw from horizon down
        for y in range(self.half_height, self.height):
            p = y - self.half_height
            row_dist = (0.5 * self.height) / p if p != 0 else 0.001
            
            fog = self._calc_fog(row_dist)
            
            # Floor with fog
            if fog > 0:
                floor_color = floor * (1 - fog) + self.fog_color * fog
            else:
                floor_color = floor
            
            # Ceiling with fog (mirrored)
            ceiling_y = self.height - y - 1
            if fog > 0:
                ceiling_color = ceiling * (1 - fog) + self.fog_color * fog
            else:
                ceiling_color = ceiling
            
            self.buffer[y, :] = floor_color.astype(np.uint8)
            self.buffer[ceiling_y, :] = ceiling_color.astype(np.uint8)