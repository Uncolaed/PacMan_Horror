from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.engine import Engine
    from main import Game

import math
from math import sin, cos, pi, tan

class RayCaster:
    def __init__(self, engine):
        self.engine: Engine = engine
        self.game: Game = engine.game
        
        # Raycasting configuration
        self.fov = pi / 3  # 60 degrees field of view
        self.num_rays = 240 # Number of rays to cast
    
    def check_horizontal_intersection(self, player_pos_x, player_pos_y, ray_angle, game_map, map_size_x, map_size_y, tile_size):
        """
        Check for horizontal grid line intersections.
        
        Returns:
            tuple: (hit_x, hit_y, distance) or (None, None, float('inf')) if no hit
        """
        # Determine if ray is facing up or down
        ray_facing_down = ray_angle > 0 and ray_angle < pi
        
        # Find first horizontal grid intersection
        if ray_facing_down:
            y_intersect = (int(player_pos_y / tile_size) + 1) * tile_size
        else:
            y_intersect = int(player_pos_y / tile_size) * tile_size
        
        # Calculate x coordinate of first intersection
        if tan(ray_angle) != 0:
            x_intersect = player_pos_x + (y_intersect - player_pos_y) / tan(ray_angle)
        else:
            return None, None, float('inf')
        
        # Calculate step sizes
        y_step = tile_size if ray_facing_down else -tile_size
        if tan(ray_angle) != 0:
            x_step = tile_size / tan(ray_angle)
        else:
            x_step = 0
        
        # Make sure x_step has the correct sign
        if (ray_angle > pi / 2 and ray_angle < 3 * pi / 2 and x_step > 0) or \
           (ray_angle < pi / 2 or ray_angle > 3 * pi / 2) and x_step < 0:
            x_step = -x_step
        
        # Check intersections along the ray
        while True:
            # Check which grid cell to test
            check_y = int(y_intersect / tile_size)
            if not ray_facing_down:
                check_y -= 1
            check_x = int(x_intersect / tile_size)
            
            # Check bounds
            if check_x < 0 or check_x >= map_size_x or check_y < 0 or check_y >= map_size_y:
                return None, None, float('inf')
            
            # Check if there's a wall
            if game_map[check_y * map_size_x + check_x] == 1:
                # Calculate distance
                dx = x_intersect - player_pos_x
                dy = y_intersect - player_pos_y
                distance = (dx * dx + dy * dy) ** 0.5
                return x_intersect, y_intersect, distance
            
            # Move to next intersection
            x_intersect += x_step
            y_intersect += y_step
    
    def check_vertical_intersection(self, player_pos_x, player_pos_y, ray_angle, game_map, map_size_x, map_size_y, tile_size):
        """
        Check for vertical grid line intersections.
        
        Returns:
            tuple: (hit_x, hit_y, distance) or (None, None, float('inf')) if no hit
        """
        # Determine if ray is facing right or left
        ray_facing_right = ray_angle < pi / 2 or ray_angle > 3 * pi / 2
        
        # Find first vertical grid intersection
        if ray_facing_right:
            x_intersect = (int(player_pos_x / tile_size) + 1) * tile_size
        else:
            x_intersect = int(player_pos_x / tile_size) * tile_size
        
        # Calculate y coordinate of first intersection
        y_intersect = player_pos_y + (x_intersect - player_pos_x) * tan(ray_angle)
        
        # Calculate step sizes
        x_step = tile_size if ray_facing_right else -tile_size
        y_step = tile_size * tan(ray_angle)
        
        # Make sure y_step has the correct sign
        if (ray_angle > pi and y_step > 0) or (ray_angle < pi and y_step < 0):
            y_step = -y_step
        
        # Check intersections along the ray
        while True:
            # Check which grid cell to test
            check_x = int(x_intersect / tile_size)
            if not ray_facing_right:
                check_x -= 1
            check_y = int(y_intersect / tile_size)
            
            # Check bounds
            if check_x < 0 or check_x >= map_size_x or check_y < 0 or check_y >= map_size_y:
                return None, None, float('inf')
            
            # Check if there's a wall
            if game_map[check_y * map_size_x + check_x] == 1:
                # Calculate distance
                dx = x_intersect - player_pos_x
                dy = y_intersect - player_pos_y
                distance = (dx * dx + dy * dy) ** 0.5
                return x_intersect, y_intersect, distance
            
            # Move to next intersection
            x_intersect += x_step
            y_intersect += y_step
        
    def cast_rays(self, player_pos_x, player_pos_y, player_angle, game_map, map_size_x, map_size_y, tile_size):
        """
        Cast rays from player position and return ray data.
        Uses separate horizontal and vertical intersection checks.
        
        Args:
            player_pos_x: Player's X position
            player_pos_y: Player's Y position
            player_angle: Player's viewing angle
            game_map: List representing the map (1 = wall, 0 = empty)
            map_size_x: Map width in tiles
            map_size_y: Map height in tiles
            tile_size: Size of each tile
            
        Returns:
            List of dicts with ray data
        """
        ray_data = []
        ray_angle = player_angle - self.fov / 2

        for ray in range(self.num_rays):
            # Normalize ray angle
            ray_angle = ray_angle % (2 * pi)

            # Check horizontal intersections
            h_x, h_y, h_dist = self.check_horizontal_intersection(
                player_pos_x, player_pos_y, ray_angle, game_map, map_size_x, map_size_y, tile_size
            )
            
            # Check vertical intersections
            v_x, v_y, v_dist = self.check_vertical_intersection(
                player_pos_x, player_pos_y, ray_angle, game_map, map_size_x, map_size_y, tile_size
            )
            
            # Choose the closer intersection
            if h_dist < v_dist:
                ray_end_x, ray_end_y = h_x, h_y
                distance = h_dist
                side = 1  # Horizontal wall hit
            else:
                ray_end_x, ray_end_y = v_x, v_y
                distance = v_dist
                side = 0  # Vertical wall hit
            
            # Calculate perpendicular distance (fixes fisheye effect)
            perp_wall_dist = distance * cos(ray_angle - player_angle)
            
            # Calculate wall_x (texture coordinate)
            if side == 0:  # Vertical wall
                wall_x = (ray_end_y / tile_size) % 1.0
            else:  # Horizontal wall
                wall_x = (ray_end_x / tile_size) % 1.0

            # Store ray data
            ray_data.append({
                'start_x': player_pos_x,
                'start_y': player_pos_y,
                'end_x': ray_end_x,
                'end_y': ray_end_y,
                'distance': perp_wall_dist,
                'side': side,
                'wall_x': wall_x,
                'angle': ray_angle
            })

            # Move to next ray
            ray_angle += self.fov / self.num_rays
            
        return ray_data

    def get_3d_view_data(self, player_pos_x, player_pos_y, player_angle, game_map, map_size_x, map_size_y, 
                         tile_size, window_height):
        """
        Calculate 3D view data based on raycasting without drawing.
        Uses separate horizontal and vertical intersection checks.
        
        Args:
            player_pos_x: Player's X position
            player_pos_y: Player's Y position
            player_angle: Player's viewing angle
            game_map: List representing the map (1 = wall, 0 = empty)
            map_size_x: Map width in tiles
            map_size_y: Map height in tiles
            tile_size: Size of each tile
            window_height: Height of the window
            
        Returns:
            List of dicts with wall slice data
        """
        wall_data = []
        ray_angle = player_angle - self.fov / 2

        for ray in range(self.num_rays):
            # Normalize ray angle
            ray_angle = ray_angle % (2 * pi)

            # Check horizontal intersections
            h_x, h_y, h_dist = self.check_horizontal_intersection(
                player_pos_x, player_pos_y, ray_angle, game_map, map_size_x, map_size_y, tile_size
            )
            
            # Check vertical intersections
            v_x, v_y, v_dist = self.check_vertical_intersection(
                player_pos_x, player_pos_y, ray_angle, game_map, map_size_x, map_size_y, tile_size
            )
            
            # Choose the closer intersection
            if h_dist < v_dist:
                ray_end_x, ray_end_y = h_x, h_y
                distance = h_dist
                side = 1  # Horizontal wall hit
            else:
                ray_end_x, ray_end_y = v_x, v_y
                distance = v_dist
                side = 0  # Vertical wall hit
            
            # Calculate perpendicular distance (fixes fisheye effect)
            perp_wall_dist = distance * cos(ray_angle - player_angle)
            
            # Calculate height of line to draw on screen
            line_height = int(window_height / perp_wall_dist) if perp_wall_dist > 0 else window_height

            # Calculate lowest and highest pixel to fill in current stripe
            draw_start = max(-line_height // 2 + window_height // 2, 0)
            draw_end = min(line_height // 2 + window_height // 2, window_height - 1)

            # Calculate wall_x (texture coordinate)
            if side == 0:  # Vertical wall
                wall_x = (ray_end_y / tile_size) % 1.0
            else:  # Horizontal wall
                wall_x = (ray_end_x / tile_size) % 1.0

            # Store wall slice data
            wall_data.append({
                'draw_start': draw_start,
                'draw_end': draw_end,
                'side': side,
                'distance': perp_wall_dist,
                'wall_x': wall_x,
                'line_height': line_height
            })
            

            # Move to next ray
            ray_angle += self.fov / self.num_rays
            
        return wall_data
    