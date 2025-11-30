from OpenGL.GL import *
from OpenGL.GLU import *

class Renderer:
    def __init__(self, engine):
        self.engine = engine
        self.raycaster = engine.raycaster

        # minimap settings
        self.minimap_scale = 0.15
        self.minimap_padding = 10

    # ------------------------------------------------------------
    # Projection helpers
    # ------------------------------------------------------------

    def push_ortho(self, left, right, bottom, top):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(left, right, bottom, top)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def pop_ortho(self):
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # ------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------

    def draw_background(self, width, height):
        mid = height // 2

        # ceiling
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex2i(0, 0)
        glVertex2i(width, 0)
        glVertex2i(width, mid)
        glVertex2i(0, mid)
        glEnd()

        # floor
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex2i(0, mid)
        glVertex2i(width, mid)
        glVertex2i(width, height)
        glVertex2i(0, height)
        glEnd()

    def get_flat_map(self):
        # flatten 2D list into 1D
        return [t for row in self.engine.map.map_grid for t in row]

    # ------------------------------------------------------------
    # 3D View
    # ------------------------------------------------------------

    def draw_wall_slice(self, x, width, start, end, side):
        # color based on vertical/horizontal collision
        if side == 1:
            glColor3f(0.7, 0.7, 0.7)
        else:
            glColor3f(0.9, 0.9, 0.9)

        glBegin(GL_QUADS)
        glVertex2f(x, start)
        glVertex2f(x + width, start)
        glVertex2f(x + width, end)
        glVertex2f(x, end)
        glEnd()

    def draw3D(self):
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        self.push_ortho(0, W, H, 0)
        self.draw_background(W, H)

        # player info
        pos = self.engine.player.position
        angle = self.engine.player.player_angle

        # ray data
        game_map = self.get_flat_map()
        rays = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            game_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )

        ray_w = W / self.raycaster.num_rays
        mid_y = H // 2
        tile = self.engine.map.grid_size

        for i, r in enumerate(rays):
            dist = r["distance"] if r["distance"] > 0 else 0.001
            line_h = int(min((tile * W) / dist, W))

            start = max(mid_y - line_h // 2, 0)
            end = min(mid_y + line_h // 2, H - 1)

            self.draw_wall_slice(i * ray_w, ray_w, start, end, r["side"])

        self.pop_ortho()

    # ------------------------------------------------------------
    # 2D Minimap
    # ------------------------------------------------------------

    def setup_minimap_view(self):
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        map_w = self.engine.map.grid_x * self.engine.map.grid_size
        map_h = self.engine.map.grid_y * self.engine.map.grid_size
        aspect = map_w / map_h

        mini_size = min(W, H) * self.minimap_scale
        mini_w = mini_size * aspect
        mini_h = mini_size

        # viewport in top-left
        glViewport(
            self.minimap_padding,
            H - int(mini_h) - self.minimap_padding,
            int(mini_w),
            int(mini_h)
        )

        self.push_ortho(0, map_w, map_h, 0)

    def restore_full_viewport(self):
        glViewport(
            0,
            0,
            self.engine.game.WINDOW_WIDTH,
            self.engine.game.WINDOW_HEIGHT
        )
        self.pop_ortho()

    def draw_2d_rays(self):
        pos = self.engine.player.position
        angle = self.engine.player.player_angle

        game_map = self.get_flat_map()
        rays = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            game_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )

        glColor3f(1.0, 0.0, 0.0)
        glLineWidth(1)
        glBegin(GL_LINES)
        for r in rays:
            glVertex2f(r["start_x"], r["start_y"])
            glVertex2f(r["end_x"], r["end_y"])
        glEnd()

    def draw_2d_player(self):
        pos = self.engine.player.position
        delta = self.engine.player.position_delta

        glColor3f(1.0, 1.0, 0.0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(pos.x, pos.y)
        glEnd()

        # direction line
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(pos.x, pos.y)
        glVertex2f(pos.x + delta.x * 50, pos.y + delta.y * 50)
        glEnd()

    def draw2D(self):
        self.setup_minimap_view()

        self.engine.map.draw()
        self.draw_2d_rays()
        self.draw_2d_player()

        self.restore_full_viewport()
