from math import sin, cos, tan, pi, inf

class RayCaster:
    def __init__(self, engine):
        self.engine = engine
        self.game = engine.game

        self.fov = pi / 3          # 60° FOV
        self.num_rays = 240        # Number of rays
        self.delta_angle = self.fov / self.num_rays

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    @staticmethod
    def distance(ax, ay, bx, by):
        dx = bx - ax
        dy = by - ay
        return (dx * dx + dy * dy) ** 0.5

    def tile_at(self, game_map, mx, my, size_x, size_y):
        if mx < 0 or mx >= size_x or my < 0 or my >= size_y:
            return None
        return game_map[my * size_x + mx]

    # ------------------------------------------------------------
    # Unified grid traversal for horizontal or vertical intersection
    # ------------------------------------------------------------

    def trace_intersection(
        self,
        px, py,
        ray_angle,
        game_map, size_x, size_y, tile,
        vertical=False
    ):
        """
        Generic grid stepping used for both horizontal & vertical checks.
        vertical = True → stepping on vertical grid lines
        vertical = False → stepping on horizontal grid lines
        """

        sin_a = sin(ray_angle)
        cos_a = cos(ray_angle)
        tan_a = sin_a / cos_a if cos_a != 0 else None

        # -------------------------------
        # INITIAL INTERSECTION AND STEPS
        # -------------------------------
        if vertical:
            # Ray facing right?
            right = (ray_angle < pi / 2) or (ray_angle > 3 * pi / 2)

            # first vertical gridline
            x_inter = (int(px / tile) + (1 if right else 0)) * tile
            if not right:
                x_inter -= 0  # keep same (int * tile) already correct

            if tan_a is None:
                return None, None, inf

            y_inter = py + (x_inter - px) * tan_a

            x_step = tile if right else -tile
            y_step = x_step * tan_a

        else:
            # Ray facing down?
            down = (0 < ray_angle < pi)

            # first horizontal gridline
            y_inter = (int(py / tile) + (1 if down else 0)) * tile
            if not down:
                y_inter -= 0

            if tan_a == 0 or tan_a is None:
                return None, None, inf

            x_inter = px + (y_inter - py) / tan_a

            y_step = tile if down else -tile
            x_step = y_step / tan_a

        # --------------------------------------
        # Correct stepping orientation signs
        # --------------------------------------
        # vertical walls need to detect vertical orientation of ray
        if vertical:
            # If ray is facing up but y_step is positive, flip, etc.
            if (sin_a < 0 and y_step > 0) or (sin_a > 0 and y_step < 0):
                y_step = -y_step
        else:
            # horizontal walls need proper x_step sign
            if (cos_a < 0 and x_step > 0) or (cos_a > 0 and x_step < 0):
                x_step = -x_step

        # ----------------------------------------------------
        # GRID TRAVERSAL
        # ----------------------------------------------------
        x, y = x_inter, y_inter

        while True:
            # Which tile to check?
            tile_x = int(x / tile)
            tile_y = int(y / tile)

            # Offsets for touching boundary
            if vertical:
                if cos_a < 0:
                    tile_x -= 1
            else:
                if sin_a < 0:
                    tile_y -= 1

            # Out of bounds?
            tile_val = self.tile_at(game_map, tile_x, tile_y, size_x, size_y)
            if tile_val is None:
                return None, None, inf

            # Wall hit?
            if tile_val == 1:
                dist = self.distance(px, py, x, y)
                return x, y, dist

            # Step further along gridline
            x += x_step
            y += y_step

    # ------------------------------------------------------------
    # Ray casting core
    # ------------------------------------------------------------

    def cast_rays(self, px, py, pa, game_map, size_x, size_y, tile):
        rays = []
        ray_angle = pa - self.fov / 2

        for _ in range(self.num_rays):
            ray_angle %= (2 * pi)

            # horizontal intersection
            hx, hy, hd = self.trace_intersection(
                px, py, ray_angle,
                game_map, size_x, size_y, tile,
                vertical=False
            )

            # vertical intersection
            vx, vy, vd = self.trace_intersection(
                px, py, ray_angle,
                game_map, size_x, size_y, tile,
                vertical=True
            )

            # which one is closer?
            if hd < vd:
                end_x, end_y = hx, hy
                dist = hd
                side = 1  # horizontal hit
            else:
                end_x, end_y = vx, vy
                dist = vd
                side = 0  # vertical hit

            # fisheye correction
            perp_dist = dist * cos(ray_angle - pa)

            # texture offset
            if side == 0:  # vertical wall
                wall_x = (end_y / tile) % 1.0
            else:          # horizontal wall
                wall_x = (end_x / tile) % 1.0

            rays.append({
                "start_x": px,
                "start_y": py,
                "end_x": end_x,
                "end_y": end_y,
                "distance": perp_dist,
                "side": side,
                "wall_x": wall_x,
                "angle": ray_angle
            })

            ray_angle += self.delta_angle

        return rays

    # ------------------------------------------------------------
    # 3D projection data
    # ------------------------------------------------------------

    def get_3d_view_data(
        self,
        px, py, pa,
        game_map, size_x, size_y,
        tile, window_height
    ):
        wall_slices = []
        ray_angle = pa - self.fov / 2

        for _ in range(self.num_rays):
            ray_angle %= (2 * pi)

            # horizontal
            hx, hy, hd = self.trace_intersection(
                px, py, ray_angle, game_map, size_x, size_y, tile, vertical=False
            )
            # vertical
            vx, vy, vd = self.trace_intersection(
                px, py, ray_angle, game_map, size_x, size_y, tile, vertical=True
            )

            if hd < vd:
                end_x, end_y, dist, side = hx, hy, hd, 1
            else:
                end_x, end_y, dist, side = vx, vy, vd, 0

            perp_dist = dist * cos(ray_angle - pa)
            line_height = int(window_height / perp_dist) if perp_dist > 0 else window_height

            draw_start = max((window_height // 2) - (line_height // 2), 0)
            draw_end = min((window_height // 2) + (line_height // 2), window_height - 1)

            wall_x = (end_y / tile) % 1.0 if side == 0 else (end_x / tile) % 1.0

            wall_slices.append({
                "draw_start": draw_start,
                "draw_end": draw_end,
                "side": side,
                "distance": perp_dist,
                "wall_x": wall_x,
                "line_height": line_height
            })

            ray_angle += self.delta_angle

        return wall_slices
