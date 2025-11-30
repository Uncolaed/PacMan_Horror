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
        self.init_opengl()
        self.prev_time = time.time()
        self.fps_list = []
        
        # Better approach: Set relative mouse mode
        pg.event.set_grab(True)      
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        try:
            pg.mouse.set_relative_mouse_mode(True)  # This auto-centers
        except:
            pg.mouse.get_rel()  # Fallback: flush initial movement
            
    def init_opengl(self):
        glClearColor(0.3, 0.3, 0.3, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def get_dt(self):
        now = time.time()
        self.dt = now - self.prev_time
        self.prev_time = now
        self.get_fps()
    def get_fps(self):
        fps = 1 / self.dt if self.dt else 0
        if len(self.fps_list) == 50:
            self.fps_list.pop(0)
        self.fps_list.append(fps)
        avg_fps = sum(self.fps_list) / len(self.fps_list)
        pg.display.set_caption("Raycaster - FPS: " + str(round(avg_fps, 2)))
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    
        self.engine.handle_events()
    def game_loop(self):
        self.clock.tick()  # Updates clock without capping FPS
        self.get_dt()
        self.handle_events()
        self.engine.update()
        self.engine.display()
        pg.display.flip()
            
if __name__ == "__main__":
    game = Game()
    while game.running:
        game.game_loop()
    pg.quit()