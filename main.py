import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from math import sin, cos, pi, tan
import random,time,os

from core.engine import Engine
class Game:
    def __init__(self):
        pg.init()
        self.dir = os.path.dirname(os.path.abspath("main.py"))
        
        self.WINDOW_WIDTH = 1280
        self.WINDOW_HEIGHT = 720
        pg.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
        pg.display.set_caption("Raycasting Test")
        
        self.clock = pg.time.Clock()
        self.running = True
        self.engine = Engine(self)
        # init openGL context
        self.init_opengl()
        
    def init_opengl(self):
        glClearColor(0.3, 0.3, 0.3, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                # elif event.key == K_c:  # Toggle camera shake
                    # trigger_camera_shake()
                    
        # self.player.handle_events()
    def game_loop(self):
        self.handle_events()
        self.engine.display()
        pg.display.flip()
        self.clock.tick(60)
            
if __name__ == "__main__":
    game = Game()
    while game.running:
        game.game_loop()
    pg.quit()