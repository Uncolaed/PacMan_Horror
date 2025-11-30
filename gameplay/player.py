import pygame as pg
class Player:
    def __init__(self):
        self.position = pg.Vector2(200,200)
        self.position_delta = pg.Vector2()