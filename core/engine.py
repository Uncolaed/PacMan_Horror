from gameplay.player import Player
from core.renderer import Renderer
from core.map import Map
from core.raycaster import RayCaster
from OpenGL.GL import *
from OpenGL.GLU import *

class Engine:
    def __init__(self,game):
        self.game = game
        self.map = Map(self.game)
        self.player = Player(self)
        self.raycaster = RayCaster(self)
        self.renderer = Renderer(self)
        
    def update(self):
        self.player.update()
        
    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.renderer.draw3D()
        self.renderer.draw2D()
        
    def handle_events(self):
        self.player.get_actions()
