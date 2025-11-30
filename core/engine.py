from gameplay.player import Player
from core.renderer import Renderer
from core.map import Map
from OpenGL.GL import *
from OpenGL.GLU import *

class Engine:
    def __init__(self,game):
        self.game = game
        self.player = Player()
        self.renderer = Renderer(self)
        self.map = Map(self.game)
        
    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.renderer.draw2D()
        