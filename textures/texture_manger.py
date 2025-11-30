from enum import Enum, auto
from PIL import Image

class TextureID(Enum):
    BRICK = auto()
    STONE = auto()
    WOOD  = auto()
    DOOR  = auto()

class TextureManager:
    def __init__(self):
        # Stores textures like:
        # self.textures[TextureID.BRICK] = [[(r,g,b), ...], ...]
        self.textures = {}
        self.width = None
        self.height = None

    # Load and convert PNG to 2D RGB array
    def load_texture(self, tex_id: TextureID, filepath: str):
        img = Image.open(filepath).convert("RGB")
        w, h = img.size
        pixels = img.load()

        # Save texture size (first texture defines size)
        if self.width is None:
            self.width = w
            self.height = h
        else:
            if w != self.width or h != self.height:
                raise ValueError(f"TextureID {filepath} must be {self.width}x{self.height}")

        # Convert to Python list of lists
        data = [[pixels[x, y] for x in range(w)] for y in range(h)]
        self.textures[tex_id] = data

    # Returns raw texture array
    def get_texture(self, tex_id: TextureID):
        return self.textures[tex_id]

    # Sample texel at integer coordinate
    def get_pixel(self, tex_id: TextureID, x: int, y: int):
        # Clamp or wrap here if needed
        return self.textures[tex_id][y][x]
