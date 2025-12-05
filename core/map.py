import os
import csv


class Map:
    def __init__(self, game, filename="level.csv"):
        self.game = game
        self.map_file_name = filename

        self.map_grid = []
        self.grid_x = 0
        self.grid_y = 0

        # Tile size is ONLY for rendering (not raycasting)
        self.grid_size = 64     

        # Spawn in TILE coordinates
        self.player_spawn = None

        self.load_world()

    # -------------------------------------------------------------
    # Load CSV map and extract tile grid + player spawn
    # -------------------------------------------------------------
    def load_world(self):
        path = os.path.join(self.game.dir, "maps", self.map_file_name)

        with open(path, "r") as file:
            reader = csv.reader(file, delimiter=",")
            self.map_grid = [list(row) for row in reader]

        # Convert tiles and extract 'P' spawn
        for y, row in enumerate(self.map_grid):
            for x, tile in enumerate(row):

                # Player start tile
                if tile == "P":
                    # Store spawn in TILE coordinates
                    self.player_spawn = (x + 0.5, y + 0.5)
                    self.map_grid[y][x] = 0  # Replace with empty

                else:
                    # Convert string to int
                    self.map_grid[y][x] = int(tile)

        # Map dimensions (in tiles)
        self.grid_y = len(self.map_grid)
        self.grid_x = len(self.map_grid[0]) if self.grid_y > 0 else 0

    # -------------------------------------------------------------
    # Optional helper: safe tile lookup
    # -------------------------------------------------------------
    def get_tile(self, x, y):
        """Return tile ID or treat out-of-bounds as wall."""
        if x < 0 or x >= self.grid_x:
            return 1  # boundary wall
        if y < 0 or y >= self.grid_y:
            return 1

        return self.map_grid[y][x]
