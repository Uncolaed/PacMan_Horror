from enum import Enum, auto
from PIL import Image
import numpy as np

class TextureID(Enum):
    BRICK = auto()
    STONE = auto()
    WOOD  = auto()
    DOOR  = auto()

class TextureManager:
    def __init__(self):
        # Store textures as numpy arrays for speed
        self.textures = {}
        self.width = None
        self.height = None
    
    def load_texture(self, tex_id: TextureID, filepath: str):
        """Load texture and convert to numpy array immediately"""
        img = Image.open(filepath).convert("RGB")
        w, h = img.size
        
        # Save texture size (first texture defines size)
        if self.width is None:
            self.width = w
            self.height = h
        else:
            if w != self.width or h != self.height:
                raise ValueError(f"Texture {filepath} must be {self.width}x{self.height}")
        
        # Convert directly to numpy array - MUCH faster than nested lists
        # PIL images can be converted to numpy with np.array()
        data = np.array(img, dtype=np.uint8)
        self.textures[tex_id] = data
    
    def get_texture(self, tex_id: TextureID):
        """Returns numpy array of texture"""
        return self.textures[tex_id]
    
    def get_pixel(self, tex_id: TextureID, x: int, y: int):
        """Sample texel at integer coordinate (for compatibility)"""
        return tuple(self.textures[tex_id][y, x])