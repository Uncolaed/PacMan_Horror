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
        self.game: Game = engine.game
        self.width = self.game.WINDOW_WIDTH
        self.height = self.game.WINDOW_HEIGHT
        self.map: Map = engine.map
        self.textureManger: TextureManager = engine.texture_manager
        self.raycaster = RayCaster(engine)
        
        # Use numpy array - contiguous memory layout
        self.buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Pre-calculate constants
        self.half_height = self.height // 2
        
        # Cache texture dimensions and convert textures to numpy
        self.tex_width = None
        self.tex_height = None
        self.tex_height_minus_1 = None
        self.numpy_textures = {}  # Cache numpy versions of textures
        
    def _convert_textures_to_numpy(self):
        """Convert PIL textures to numpy arrays once - HUGE speedup"""
        from textures.texture_manager import TextureID
        
        if not self.numpy_textures:
            for tex_id in TextureID:
                if tex_id in self.textureManger.textures:
                    # Convert list of lists to numpy array
                    texture_data = self.textureManger.textures[tex_id]
                    self.numpy_textures[tex_id] = np.array(texture_data, dtype=np.uint8)
        
    def draw3D(self):
        self.clear_buffer()
        self.render_walls()
        self.draw_buffer()
    
    def clear_buffer(self):
        # Numpy slice assignment
        self.buffer[:self.half_height] = (50, 50, 50)  # Ceiling
        self.buffer[self.half_height:] = (30, 30, 30)  # Floor
    
    def draw_buffer(self):
        # Use glDrawPixels - sends entire buffer at once
        glDrawPixels(self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE, 
                     np.flipud(self.buffer))
    
    def render_walls(self):
        from textures.texture_manager import TextureID
        
        # Initialize texture cache
        if self.tex_width is None:
            self.tex_width = self.textureManger.width
            self.tex_height = self.textureManger.height
            self.tex_height_minus_1 = self.tex_height - 1
            self._convert_textures_to_numpy()
        
        texWidth = self.tex_width
        texHeight = self.tex_height

        tex_height_m1 = self.tex_height_minus_1
        
        half_h = self.half_height
        height = self.height
        
        # Pre-fetch texture array (assuming BRICK for now)
        texture_np = self.numpy_textures[TextureID.BRICK]
        
        # Process each ray
        for ray_data in self.raycaster.cast_rays():
            x = ray_data['x']
            perpWallDist = ray_data['perpWallDist']
            
            # Skip if too close (avoid division issues)
            if perpWallDist < 0.01:
                continue
            
            side = ray_data['side']
            mapX = ray_data['mapX']
            mapY = ray_data['mapY']
            wallX = ray_data['wallX']
            rayDirX = ray_data['rayDirX']
            rayDirY = ray_data['rayDirY']
            
            # Calculate wall slice height
            lineHeight = int(height / perpWallDist)   
            drawStart = max(0, -lineHeight // 2 + half_h)
            drawEnd = min(height - 1, lineHeight // 2 + half_h)
            
            # Skip if nothing to draw
            if drawStart >= drawEnd:
                continue
            
            # Calculate texture X coordinate
            texX = int(wallX * texWidth)
            if side == 0 and rayDirX > 0:
                texX = texWidth - texX - 1
            if side == 1 and rayDirY < 0:
                texX = texWidth - texX - 1
            
            # Clamp texX just in case
            texX = max(0, min(texWidth - 1, texX))
            
            # Texture mapping setup
            step = texHeight / lineHeight
            texPos = (drawStart - half_h + lineHeight / 2) * step
            
            # Calculate all texY values at once using numpy
            num_pixels = drawEnd - drawStart
            texY_positions = texPos + np.arange(num_pixels) * step
            texY_indices = texY_positions.astype(np.int32) & tex_height_m1
            
            # Extract the entire column from texture in one operation
            column_colors = texture_np[texY_indices, texX]
            
            # Apply darkening for Y-side walls
            if side == 1:
                column_colors = column_colors >> 1
            
            # Write entire column to buffer at once
            self.buffer[drawStart:drawEnd, x] = column_colors