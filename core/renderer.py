from OpenGL.GL import *
from OpenGL.GLU import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine import Engine

class Renderer():
    def __init__(self, engine: 'Engine'):
        self.engine = engine
        self.PLAYER_POS = self.engine.player.position
        self.PLAYER_POS_DELTA = self.engine.player.position_delta
        
        # Minimap settings
        self.minimap_scale = 0.15  # 15% of screen size
        self.minimap_padding = 10  # Pixels from edge
    
    def draw2D(self):
        # Save current matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        
        # Calculate minimap dimensions while maintaining aspect ratio
        map_width = self.engine.map.grid_x * self.engine.map.grid_size
        map_height = self.engine.map.grid_y * self.engine.map.grid_size
        map_aspect = map_width / map_height
        
        minimap_size = min(self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT) * self.minimap_scale
        minimap_width = minimap_size * map_aspect
        minimap_height = minimap_size
        
        # Set viewport for minimap (top-left corner)
        glViewport(
            self.minimap_padding, 
            self.engine.game.WINDOW_HEIGHT - int(minimap_height) - self.minimap_padding,
            int(minimap_width), 
            int(minimap_height)
        )
        
        # Set orthographic projection for the map size
        gluOrtho2D(0, map_width, map_height, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw minimap content
        self.engine.map.draw()
        self.draw_2d_player()
        
        # Restore matrices and viewport
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        # Reset viewport to full screen
        glViewport(0, 0, self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT)
        
    def draw_2d_player(self):
        glPushMatrix()

        glColor3f(1.0, 1.0, 0.0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(self.PLAYER_POS.x, self.PLAYER_POS.y)
        glEnd()

        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(self.PLAYER_POS.x, self.PLAYER_POS.y)
        glVertex2f(self.PLAYER_POS.x + self.PLAYER_POS_DELTA.x * 5, self.PLAYER_POS.y + self.PLAYER_POS_DELTA.y * 5)
        glEnd()

        glPopMatrix()
