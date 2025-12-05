from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.engine import Engine
    from core.map import Map

from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Renderer2D:
    def __init__(self, engine):
        self.engine: Engine = engine
        self.minimap_scale = 0.2
        self.minimap_padding = 10
        
        # Pre-rendered minimap display list
        self.minimap_display_list = None
        self._create_minimap_display_list()
        
    def _create_minimap_display_list(self):
        """Pre-compile minimap tiles into a display list"""
        map: Map = self.engine.map
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT
        
        # Calculate minimap dimensions
        map_w = map.grid_x * map.grid_size
        map_h = map.grid_y * map.grid_size
        aspect_ratio = map_w / map_h
        
        mini_size = min(W, H) * self.minimap_scale
        mini_w = mini_size * aspect_ratio
        mini_h = mini_size
        
        # Calculate tile size in minimap
        tile_w = mini_w / map.grid_x
        tile_h = mini_h / map.grid_y
        
        # Position of minimap (top-left with padding)
        mini_x = self.minimap_padding
        mini_y = self.minimap_padding
        
        # Create display list
        self.minimap_display_list = glGenLists(1)
        glNewList(self.minimap_display_list, GL_COMPILE)
        
        # Draw map tiles
        for y in range(map.grid_y):
            for x in range(map.grid_x):
                tile_val = map.map_grid[y][x]
                
                # Calculate tile position on screen
                tile_screen_x = mini_x + x * tile_w
                tile_screen_y = mini_y + y * tile_h
                
                # Draw tile based on value
                if tile_val == 0:  # Empty space
                    glColor3f(0.2, 0.2, 0.2)  # Dark gray
                elif tile_val == 1:  # Wall
                    glColor3f(0.8, 0.8, 0.8)  # Light gray
                else:
                    glColor3f(0.5, 0.5, 0.5)  # Medium gray
                
                # Draw filled rectangle for tile
                glBegin(GL_QUADS)
                glVertex2f(tile_screen_x, tile_screen_y)
                glVertex2f(tile_screen_x + tile_w, tile_screen_y)
                glVertex2f(tile_screen_x + tile_w, tile_screen_y + tile_h)
                glVertex2f(tile_screen_x, tile_screen_y + tile_h)
                glEnd()
                
                # Draw tile border
                glColor3f(0.4, 0.4, 0.4)
                glLineWidth(1)
                glBegin(GL_LINE_LOOP)
                glVertex2f(tile_screen_x, tile_screen_y)
                glVertex2f(tile_screen_x + tile_w, tile_screen_y)
                glVertex2f(tile_screen_x + tile_w, tile_screen_y + tile_h)
                glVertex2f(tile_screen_x, tile_screen_y + tile_h)
                glEnd()
        
        glEndList()
        
    def draw3D(self):
        pass
    
    def draw2D(self):
        """Set up 2D orthographic projection and render scene"""
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT
        
        # Set up 2D orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, W, H, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw pre-compiled minimap
        glCallList(self.minimap_display_list)
        
        # Draw dynamic player indicator
        self._draw_player_on_minimap()
        
        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def _draw_player_on_minimap(self):
        """Calculate player position on minimap and draw player indicator"""
        map: Map = self.engine.map
        player = self.engine.player
        
        # Get player world position
        player_x = player.position.x
        player_y = player.position.y
        player_angle = player.player_angle
        
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
        
        # Draw player direction indicator
        line_length = 8
        glColor3f(1.0, 0.0, 0.0)  # Red
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(scaled_px, scaled_py)
        glVertex2f(scaled_px + line_length * math.cos(player_angle), 
                  scaled_py + line_length * math.sin(player_angle))
        glEnd()



