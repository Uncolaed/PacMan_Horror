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
        
        # Ray visualization settings
        self.show_rays = True
        self.ray_skip = 40  # Draw every Nth ray to avoid clutter

        # Pre-render map geometry
        self.minimap_display_list = None
        self._create_minimap_display_list()

    # ---------------------------------------------------------
    # BUILD STATIC MINIMAP TILE DISPLAY LIST
    # ---------------------------------------------------------
    def _create_minimap_display_list(self):
        map: Map = self.engine.map
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        # Minimaps are sized based on tile count, not pixels
        mini_size = min(W, H) * self.minimap_scale
        aspect_ratio = map.grid_x / map.grid_y

        mini_w = mini_size * aspect_ratio
        mini_h = mini_size

        # Tile sizes ON SCREEN (minimap pixels)
        tile_w = mini_w / map.grid_x
        tile_h = mini_h / map.grid_y

        mini_x = self.minimap_padding
        mini_y = self.minimap_padding

        # Create display list
        self.minimap_display_list = glGenLists(1)
        glNewList(self.minimap_display_list, GL_COMPILE)

        # Draw map tiles
        for y in range(map.grid_y):
            for x in range(map.grid_x):
                tile_val = map.map_grid[y][x]

                tile_x = mini_x + x * tile_w
                tile_y = mini_y + y * tile_h

                if tile_val == 0:
                    glColor3f(0.20, 0.20, 0.20)  # empty
                else:
                    glColor3f(0.85, 0.85, 0.85)  # wall

                # Tile fill
                glBegin(GL_QUADS)
                glVertex2f(tile_x, tile_y)
                glVertex2f(tile_x + tile_w, tile_y)
                glVertex2f(tile_x + tile_w, tile_y + tile_h)
                glVertex2f(tile_x, tile_y + tile_h)
                glEnd()

                # Tile border
                glColor3f(0.4, 0.4, 0.4)
                glBegin(GL_LINE_LOOP)
                glVertex2f(tile_x, tile_y)
                glVertex2f(tile_x + tile_w, tile_y)
                glVertex2f(tile_x + tile_w, tile_y + tile_h)
                glVertex2f(tile_x, tile_y + tile_h)
                glEnd()

        glEndList()

    # ---------------------------------------------------------
    # MAIN 2D DRAWING ENTRY POINT
    # ---------------------------------------------------------
    def draw2D(self):
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        # Switch to 2D
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, W, H, 0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Draw cached minimap
        glCallList(self.minimap_display_list)

        # Draw rays if enabled
        if self.show_rays:
            self._draw_rays()

        # Draw player on minimap (on top of rays)
        self._draw_player_on_minimap()

        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    # ---------------------------------------------------------
    # DRAW RAYS ON MINIMAP
    # ---------------------------------------------------------
    def _draw_rays(self):
        map = self.engine.map
        player = self.engine.player
        
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        mini_size = min(W, H) * self.minimap_scale
        aspect_ratio = map.grid_x / map.grid_y

        mini_w = mini_size * aspect_ratio
        mini_h = mini_size

        mini_x = self.minimap_padding
        mini_y = self.minimap_padding

        # Player position on minimap
        px = player.position.x
        py = player.position.y
        
        player_screen_x = mini_x + (px / map.grid_x) * mini_w
        player_screen_y = mini_y + (py / map.grid_y) * mini_h

        # Get raycaster to cast rays
        ray_count = 0
        
        # Enable line smoothing for better visuals
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        for ray_data in self.engine.raycaster.cast_rays():
            # Only draw every Nth ray to reduce clutter
            if ray_count % self.ray_skip != 0:
                ray_count += 1
                continue
            
            # Calculate hit point in world coordinates
            perpWallDist = ray_data['perpWallDist']
            rayDirX = ray_data['rayDirX']
            rayDirY = ray_data['rayDirY']
            
            # Hit point in world space
            hit_x = px + rayDirX * perpWallDist
            hit_y = py + rayDirY * perpWallDist
            
            # Convert to screen coordinates
            hit_screen_x = mini_x + (hit_x / map.grid_x) * mini_w
            hit_screen_y = mini_y + (hit_y / map.grid_y) * mini_h
            
            # Draw ray line with slight transparency
            glColor4f(1.0, 1.0, 0.0, 0.3)  # Yellow with alpha
            glBegin(GL_LINES)
            glVertex2f(player_screen_x, player_screen_y)
            glVertex2f(hit_screen_x, hit_screen_y)
            glEnd()
            
            # Draw hit point
            glColor4f(1.0, 0.0, 0.0, 0.6)  # Red with alpha
            glPointSize(3.0)
            glBegin(GL_POINTS)
            glVertex2f(hit_screen_x, hit_screen_y)
            glEnd()
            
            ray_count += 1
        
        glDisable(GL_LINE_SMOOTH)
        glDisable(GL_BLEND)

    # ---------------------------------------------------------
    # DRAW PLAYER MARKER (NOW USING TILE COORDINATES)
    # ---------------------------------------------------------
    def _draw_player_on_minimap(self):
        map = self.engine.map
        player = self.engine.player

        # Player tile coordinates
        px = player.position.x
        py = player.position.y
        dir = player.dir

        # Minimaps sized by tile count
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        mini_size = min(W, H) * self.minimap_scale
        aspect_ratio = map.grid_x / map.grid_y

        mini_w = mini_size * aspect_ratio
        mini_h = mini_size

        mini_x = self.minimap_padding
        mini_y = self.minimap_padding

        # Scale tile coords → screen minimap coords
        scaled_x = mini_x + (px / map.grid_x) * mini_w
        scaled_y = mini_y + (py / map.grid_y) * mini_h

        # Draw player dot
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(scaled_x, scaled_y)
        radius = 4
        for i in range(22):
            a = i / 20 * 2 * math.pi
            glVertex2f(scaled_x + radius * math.cos(a),
                       scaled_y + radius * math.sin(a))
        glEnd()

        # Direction indicator
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(scaled_x, scaled_y)
        glVertex2f(
            scaled_x + dir.x * 10,
            scaled_y + dir.y * 10
        )
        glEnd()