from OpenGL.GL import *
from OpenGL.GLU import *
from typing import TYPE_CHECKING
from core.raycaster import RayCaster

if TYPE_CHECKING:
    from core.engine import Engine

class Renderer():
    def __init__(self, engine: 'Engine'):
        self.engine = engine
        self.raycaster:RayCaster = RayCaster(engine)
        
        # Minimap settings
        self.minimap_scale = 0.15  # 15% of screen size
        self.minimap_padding = 10  # Pixels from edge
    
    def draw3D(self):
        """Draw 3D view using raycasting data"""
        # Set up 2D projection for 3D view
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw background (ceiling and floor)
        # Ceiling
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex2i(0, 0)
        glVertex2i(self.engine.game.WINDOW_WIDTH, 0)
        glVertex2i(self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT // 2)
        glVertex2i(0, self.engine.game.WINDOW_HEIGHT // 2)
        glEnd()
        
        # Floor
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex2i(0, self.engine.game.WINDOW_HEIGHT // 2)
        glVertex2i(self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT // 2)
        glVertex2i(self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT)
        glVertex2i(0, self.engine.game.WINDOW_HEIGHT)
        glEnd()
        
        # Get player data
        pos = self.engine.player.position
        angle = self.engine.player.player_angle
        
        # Flatten map grid to 1D list
        flat_map = [tile for row in self.engine.map.map_grid for tile in row]
        
        # Cast rays and get 3D view data
        ray_data = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            flat_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )
        
        # Calculate width of each ray stripe
        ray_width = self.engine.game.WINDOW_WIDTH / self.raycaster.num_rays
        
        # Draw each wall slice
        for i, ray in enumerate(ray_data):
            distance = ray['distance']
            side = ray['side']
            
            # Avoid division by zero
            if distance <= 0:
                distance = 0.001
            
            # Calculate height of line to draw on screen
            line_height = int(min((self.engine.map.grid_size * self.engine.game.WINDOW_WIDTH) / distance,self.engine.game.WINDOW_WIDTH))
            
            # Calculate lowest and highest pixel to fill in current stripe
            draw_start = max(-line_height // 2 + self.engine.game.WINDOW_HEIGHT // 2, 0)
            draw_end = min(line_height // 2 + self.engine.game.WINDOW_HEIGHT // 2, self.engine.game.WINDOW_HEIGHT - 1)
            
            # Choose wall color based on side hit
            if side == 1:  # Horizontal wall
                glColor3f(0.7, 0.7, 0.7)
            else:  # Vertical wall
                glColor3f(0.9, 0.9, 0.9)
            
            # Draw the wall slice
            x_pos = i * ray_width
            glBegin(GL_QUADS)
            glVertex2f(x_pos, draw_start)
            glVertex2f(x_pos + ray_width, draw_start)
            glVertex2f(x_pos + ray_width, draw_end)
            glVertex2f(x_pos, draw_end)
            glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
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
        self.draw_2d_rays()
        self.draw_2d_player()
        
        # Restore matrices and viewport
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        # Reset viewport to full screen
        glViewport(0, 0, self.engine.game.WINDOW_WIDTH, self.engine.game.WINDOW_HEIGHT)
        
    def draw_2d_rays(self):
        """Draw rays from player position on the minimap"""
        glPushMatrix()
        
        # Get player data
        pos = self.engine.player.position
        angle = self.engine.player.player_angle
        
        # Flatten map grid to 1D list
        flat_map = [tile for row in self.engine.map.map_grid for tile in row]
        
        # Cast rays
        ray_data = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            flat_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )
        
        # Draw each ray
        glColor3f(1.0, 0.0, 0.0)  # Red color for rays
        glLineWidth(1)
        glBegin(GL_LINES)
        for ray in ray_data:
            glVertex2f(ray['start_x'], ray['start_y'])
            glVertex2f(ray['end_x'], ray['end_y'])
        glEnd()
        
        glPopMatrix()
    
    def draw_2d_player(self):
        glPushMatrix()

        # Get live references each frame
        pos = self.engine.player.position
        delta = self.engine.player.position_delta

        glColor3f(1.0, 1.0, 0.0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(pos.x, pos.y)
        glEnd()

        
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(pos.x, pos.y)
        glVertex2f(pos.x + delta.x * 50, pos.y + delta.y * 50)
        glEnd()

        glPopMatrix()

    