from gameplay.player import Player
from core.renderer_2d import Renderer2D
from core.renderer_3d import Renderer3D
from core.map import Map
from core.raycaster import RayCaster
from OpenGL.GL import *
from OpenGL.GLU import *
from textures.texture_manager import TextureManager,TextureID

class Engine:
    def __init__(self,game):
        self.game = game
        self.map = Map(self.game)
        self.player = Player(self)
        # self.texture_manager = TextureManager()
        # self.texture_manager.load_texture(TextureID.BRICK,self.game.dir+'/textures/brick.png')
        self.raycaster = RayCaster(self)
        self.renderer2D = Renderer2D(self)
        self.renderer3D = Renderer3D(self)
        
        
    def update(self):
        self.player.update()
        
    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.renderer3D.draw3D()
        self.renderer2D.draw2D()
        
    def handle_events(self):
        self.player.get_actions()
