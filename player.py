import pygame, math

from OpenGL.GL import *
from OpenGL.GLU import *
from textures.texture_manger import TextureID,TextureManager

class Player():
    def __init__(self, game):
        self.game = game
        self.position = pygame.Vector2(300,300)
        self.rect = pygame.Rect(300,300,8,8)
        self.speed = 150
        self.player_angle = 1
        self.position_delta = pygame.Vector2(math.cos(self.player_angle) * 5,math.sin(self.player_angle)*5)
        self.ONE_DEGREE = .0174533
        self.final_distance = 1
        self.mouse_sensitivity = 0.01
        
        self.texture_manager:TextureManager = self.game.texture_manager
        
        # Store hit information for texturing
        self.hit_vertical = False
        self.hit_x = 0
        self.hit_y = 0

    def update(self):
        if self.game.actions["mouse_x"] != 0:
            dx = self.game.actions["mouse_x"]
            self.player_angle += dx * self.mouse_sensitivity * (60 * self.game.dt)

            if self.player_angle > 2 * math.pi: 
                self.player_angle -= 2 * math.pi
            if self.player_angle < 0: 
                self.player_angle += 2 * math.pi

            self.rotate_player()
            self.game.actions["mouse_x"] = 0

        if self.game.actions["up"]: self.move_player(1)
        if self.game.actions["down"]: self.move_player(-1)
        if self.game.actions["left"]: self.strafe_player(-1)
        if self.game.actions["right"]: self.strafe_player(1)

    def is_colliding(self, x, y):
        rel_x = int(x) >> 6
        rel_y = int(y) >> 6
        return self.game.map.map_grid[rel_y][rel_x]

    def rotate_player(self):
        self.position_delta.x = math.cos(self.player_angle) * 5 
        self.position_delta.y = math.sin(self.player_angle) * 5 

    def move_player(self, direction):
        newx = self.position.x + self.position_delta.x * self.game.dt * direction * 10
        newy = self.position.y + self.position_delta.y * self.game.dt * direction * 10
        if not self.is_colliding(newx,newy):
            self.position.x = newx
            self.position.y = newy

    def strafe_player(self, direction):
        strafe_angle = self.player_angle + math.pi / 2
        strafe_x = math.cos(strafe_angle) * 5
        strafe_y = math.sin(strafe_angle) * 5
        
        newx = self.position.x + strafe_x * self.game.dt * direction * 10
        newy = self.position.y + strafe_y * self.game.dt * direction * 10
        
        if not self.is_colliding(newx, newy):
            self.position.x = newx
            self.position.y = newy

    def draw(self):
        int_x, int_y = int(self.position.x), int(self.position.y)
        glColor3f(1,1,0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2i(int_x, int_y)
        glEnd()

        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2i(int_x, int_y)
        glVertex2i(int_x + int(self.position_delta.x) * 5, int_y + int(self.position_delta.y) * 5)
        glEnd()

    def drawRays(self):
        int_x, int_y = int(self.position.x), int(self.position.y)
        self.ray_angle = self.radian_bound(self.player_angle - 15 * self.ONE_DEGREE)
        
        # Cache texture dimensions and pre-calculate constants
        tex_width = self.texture_manager.width or 32
        tex_height = self.texture_manager.height or 32
        grid_to_tex = tex_width / 64.0
        
        # Pre-calculate distance shade factor
        shade_factor = 1.0 / 600.0
        
        # Adjust angle increment for 120 rays (60 degree FOV / 120 rays = 0.5 degrees per ray)
        angle_increment = 0.3 * self.ONE_DEGREE
        
        for i in range(0, 240):
            # Draw 2D rays
            self.Check_Horizontal_Lines()
            self.Check_Vertical_Lines()
            
            # Determine which ray is shorter
            if self.Vdist < self.Hdist:
                ray_x, ray_y = self.vray_x, self.vray_y
                self.final_distance = self.Vdist
                hit_vertical = True
                glColor3f(.9,.9,.9)
            else:
                ray_x, ray_y = self.hray_x, self.hray_y
                self.final_distance = self.Hdist
                hit_vertical = False
                glColor3f(1,1,1)
            
            # Draw 2D ray
            glLineWidth(1) 
            glBegin(GL_LINES)
            glVertex2i(int_x, int_y)
            glVertex2i(int(ray_x), int(ray_y))
            glEnd()
            
            # Fix fish eye effect
            self.final_distance *= math.cos(self.player_angle - self.ray_angle)

            line_height = min((self.game.map.grid_size * self.game.DISPLAY3D_W) / self.final_distance, self.game.DISPLAY3D_W)
            int_line_height = int(line_height)
            offset3d = int(self.game.DISPLAY3D_H - line_height * 0.5)
            
            # Calculate texture X coordinate once (adjusted for 32x32 textures)
            tx = int(((int(ray_y if hit_vertical else ray_x) % 64) / 64.0 * tex_width))
            
            # Pre-calculate shading and texture column
            shade = max(0, 0.5 - self.final_distance * shade_factor)
            texture_id = TextureID.BRICK
            texture_column = self.texture_manager.get_texture(texture_id)
            
            # Pre-calculate y-to-texture mapping factor
            y_to_tex = tex_height / line_height
            
            # Batch render with GL_POINTS - start once
            glPointSize(4)  # Reduced point size for 120 rays
            glBegin(GL_POINTS)
            
            x_pos = i * 4 + 530  # Reduced spacing for 120 rays (4 pixels instead of 8)
            
            # Draw textured wall slice
            for y in range(int_line_height):
                ty = min(int(y * y_to_tex), tex_height - 1)
                
                try:
                    r, g, b = texture_column[ty][tx]
                    
                    # Apply shading with bit shifting for faster int multiplication
                    r = int(r * shade)
                    g = int(g * shade)
                    b = int(b * shade)
                    
                    glColor3ub(r, g, b)
                    glVertex2i(x_pos, y + offset3d)
                except (KeyError, IndexError):
                    glColor3f(1, 1, 1)
                    glVertex2i(x_pos, y + offset3d)
            
            glEnd()  # End GL_POINTS batch
            
            # Increment angle by 0.5 degrees for 120 rays
            self.ray_angle = self.radian_bound(self.ray_angle + angle_increment)

    def Check_Horizontal_Lines(self):
        self.Hdist, self.hray_x, self.hray_y = 10000,0,0
        int_x, int_y = int(self.position.x), int(self.position.y)
        ray_x,ray_y,dof,y_off,x_off = 0,0,0,0,0
        aTan = -1 / math.tan(self.ray_angle)

        if self.ray_angle > math.pi:
            ray_y = ((int_y >>6)<<6) - .0001
            ray_x = (self.position.y - ray_y) * aTan + self.position.x
            y_off = -64
            x_off = -y_off * aTan

        elif self.ray_angle < math.pi:
            ray_y = ((int_y >>6)<<6) + 64
            ray_x = (self.position.y - ray_y) * aTan + self.position.x
            y_off = 64
            x_off = -y_off * aTan

        else:
            ray_x, ray_y = self.position.x, self.position.y
            dof = 8
        
        while dof < 8:
            map_x = int(ray_x) >> 6
            map_y = int(ray_y) >> 6
            map_x = max(min(map_x,self.game.map.grid_x - 1),0)
            map_y = max(min(map_y,self.game.map.grid_y - 1),0)
            if self.game.map.map_grid[map_y][map_x] == 1:
                self.hray_x, self.hray_y = ray_x, ray_y
                self.Hdist = math.hypot(self.position.x - self.hray_x, self.position.y - self.hray_y)
                dof = 8
            else:
                ray_x += x_off
                ray_y += y_off
                dof += 1

    def Check_Vertical_Lines(self):
        self.Vdist, self.vray_x, self.vray_y = 10000,0,0
        HALF_PI = math.pi/2
        THREE_PI_DIV2 = 3*math.pi/2
        int_x, int_y = int(self.position.x), int(self.position.y)
        ray_x,ray_y,dof,y_off,x_off = 0,0,0,0,0
        nTan = -1*math.tan(self.ray_angle)

        if self.ray_angle > HALF_PI and self.ray_angle < THREE_PI_DIV2:
            ray_x = ((int_x >>6)<<6) - .0001
            ray_y = (self.position.x - ray_x) * nTan + self.position.y
            x_off = -64
            y_off = -x_off * nTan

        elif self.ray_angle < HALF_PI or self.ray_angle > THREE_PI_DIV2:
            ray_x = ((int_x >>6)<<6) + 64
            ray_y = (self.position.x - ray_x) * nTan + self.position.y
            x_off = 64
            y_off = -x_off * nTan

        else:
            ray_x, ray_y = self.position.x, self.position.y
            dof = 8
        
        while dof < 8:
            map_x = int(ray_x) >> 6
            map_y = int(ray_y) >> 6
            map_x = max(min(map_x,self.game.map.grid_x - 1),0)
            map_y = max(min(map_y,self.game.map.grid_y - 1),0)

            if self.game.map.map_grid[map_y][map_x] == 1: 
                self.vray_x, self.vray_y = ray_x, ray_y
                self.Vdist = math.hypot(self.position.x - self.vray_x, self.position.y - self.vray_y)
                dof = 8
            else:
                ray_x += x_off
                ray_y += y_off
                dof += 1

    def radian_bound(self, value):
        if value > 2 * math.pi: value -= 2 * math.pi
        if value < 0: value += 2 * math.pi
        return value