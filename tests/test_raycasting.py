from OpenGL.GLUT import *
from OpenGL.GL import *
from OpenGL.GLU import *
from math import sin, cos, pi, tan
import random
import time

# ------------- Constants -------------

# Window dimensions
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 512

# Map dimensions
MAP_SIZE_X = 8
MAP_SIZE_Y = 8
TILE_SIZE = 64

# Player variables
PLAYER_POS_X = 300.0
PLAYER_POS_Y = 300.0
PLAYER_ANGLE = 0.0
PLAYER_DELTA_X = cos(PLAYER_ANGLE) * 5
PLAYER_DELTA_Y = sin(PLAYER_ANGLE) * 5

# Camera shake variables
CAMERA_SHAKE = False
SHAKE_INTENSITY = 5.0  # Maximum pixels of shake
SHAKE_DURATION = 0.5  # Duration of shake in seconds
shake_timer = 10.0
last_time = time.time()

# Raycasting variables
FOV = pi / 3  # 60 degrees field of view
NUM_RAYS = 240  # Number of rays to cast

# Define a simple map (1 = wall, 0 = empty space)
my_map = [
    1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 0, 0, 0, 1,
    1, 0, 1, 0, 0, 1, 0, 1,
    1, 0, 1, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1,
]


# ------------- Functions -------------
def get_camera_offset():
    """Calculate camera shake offset based on time"""
    global CAMERA_SHAKE, shake_timer, last_time

    if not CAMERA_SHAKE:
        return 0, 0

    # Calculate delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    # Update shake timer
    shake_timer -= delta_time
    if shake_timer <= 0:
        CAMERA_SHAKE = False
        return 0, 0

    # Calculate shake progress (0 to 1)
    progress = shake_timer / SHAKE_DURATION

    # Apply easing function to make shake feel more natural
    intensity = SHAKE_INTENSITY * progress * progress

    # Generate random offset with Perlin-like smooth randomness
    offset_x = (random.random() * 2 - 1) * intensity
    offset_y = (random.random() * 2 - 1) * intensity

    return offset_x, offset_y


def trigger_camera_shake():
    """Start camera shake effect"""
    global CAMERA_SHAKE, shake_timer, last_time
    CAMERA_SHAKE = True
    shake_timer = SHAKE_DURATION
    last_time = time.time()


# draw the map as a grid
def draw_map():
    offset_x, offset_y = get_camera_offset()

    glPushMatrix()
    glTranslatef(offset_x, offset_y, 0)

    for y in range(MAP_SIZE_Y):
        for x in range(MAP_SIZE_X):
            # declare the tile variable
            tile = my_map[y * MAP_SIZE_X + x]
            # set color based on tile type
            if tile == 1:
                glColor3f(1.0, 1.0, 1.0)  # White for walls
            else:
                glColor3f(0.0, 0.0, 0.0)  # Black for empty space
            # set the position and draw the tile
            x_box = x * TILE_SIZE
            y_box = y * TILE_SIZE
            # begin drawing the quad
            glBegin(GL_QUADS)
            # define the four corners of the tile
            glVertex2i(x_box + 1, y_box + 1)
            glVertex2i(x_box + 1, y_box + TILE_SIZE - 1)
            glVertex2i(x_box + TILE_SIZE - 1, y_box + TILE_SIZE - 1)
            glVertex2i(x_box + TILE_SIZE - 1, y_box + 1)
            glEnd()

    glPopMatrix()


# Draw the player as a yellow point
def draw_player():
    offset_x, offset_y = get_camera_offset()

    glPushMatrix()
    glTranslatef(offset_x, offset_y, 0)

    glColor3f(1.0, 1.0, 0.0)
    glPointSize(8)
    glBegin(GL_POINTS)
    glVertex2f(PLAYER_POS_X, PLAYER_POS_Y)
    glEnd()

    glLineWidth(3)
    glBegin(GL_LINES)
    glVertex2f(PLAYER_POS_X, PLAYER_POS_Y)
    glVertex2f(PLAYER_POS_X + PLAYER_DELTA_X * 5, PLAYER_POS_Y + PLAYER_DELTA_Y * 5)
    glEnd()

    glPopMatrix()


def cast_rays():
    """Cast rays and draw them on the minimap"""
    global PLAYER_POS_X, PLAYER_POS_Y, PLAYER_ANGLE

    offset_x, offset_y = get_camera_offset()

    glPushMatrix()
    glTranslatef(offset_x, offset_y, 0)

    ray_angle = PLAYER_ANGLE - FOV / 2

    for ray in range(NUM_RAYS):
        # Normalize ray angle
        ray_angle = ray_angle % (2 * pi)

        # Ray direction vector
        ray_dir_x = cos(ray_angle)
        ray_dir_y = sin(ray_angle)

        # Player's position in map coordinates
        map_x = int(PLAYER_POS_X / TILE_SIZE)
        map_y = int(PLAYER_POS_Y / TILE_SIZE)

        # Length of ray from current position to next x or y-side
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

        # Direction to step in x or y direction (either +1 or -1)
        step_x = 1 if ray_dir_x >= 0 else -1
        step_y = 1 if ray_dir_y >= 0 else -1

        # Length of ray from one x or y-side to next x or y-side
        if ray_dir_x < 0:
            side_dist_x = (PLAYER_POS_X / TILE_SIZE - map_x) * delta_dist_x
        else:
            side_dist_x = (map_x + 1.0 - PLAYER_POS_X / TILE_SIZE) * delta_dist_x

        if ray_dir_y < 0:
            side_dist_y = (PLAYER_POS_Y / TILE_SIZE - map_y) * delta_dist_y
        else:
            side_dist_y = (map_y + 1.0 - PLAYER_POS_Y / TILE_SIZE) * delta_dist_y

        # Perform DDA (Digital Differential Analysis)
        hit = 0  # Was a wall hit?
        side = 0  # Was a NS or EW wall hit?

        while hit == 0:
            # Jump to next map square, either in x-direction, or in y-direction
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            # Check if ray has hit a wall
            if map_x < 0 or map_x >= MAP_SIZE_X or map_y < 0 or map_y >= MAP_SIZE_Y:
                hit = 1  # Ray went out of bounds
            elif my_map[map_y * MAP_SIZE_X + map_x] == 1:
                hit = 1  # Ray hit a wall

        # Calculate distance projected on camera direction
        if side == 0:
            perp_wall_dist = (map_x - PLAYER_POS_X / TILE_SIZE + (1 - step_x) / 2) / ray_dir_x
        else:
            perp_wall_dist = (map_y - PLAYER_POS_Y / TILE_SIZE + (1 - step_y) / 2) / ray_dir_y

        # Calculate where the ray hit the wall
        if side == 0:
            wall_x = PLAYER_POS_Y / TILE_SIZE + perp_wall_dist * ray_dir_y
        else:
            wall_x = PLAYER_POS_X / TILE_SIZE + perp_wall_dist * ray_dir_x
        wall_x -= int(wall_x)

        # Calculate height of line to draw on screen
        line_height = int(WINDOW_HEIGHT / perp_wall_dist) if perp_wall_dist > 0 else WINDOW_HEIGHT

        # Draw the ray on the minimap
        ray_end_x = PLAYER_POS_X + cos(ray_angle) * perp_wall_dist * TILE_SIZE
        ray_end_y = PLAYER_POS_Y + sin(ray_angle) * perp_wall_dist * TILE_SIZE

        glColor3f(1.0, 0.0, 0.0)  # Red color for rays
        glLineWidth(1)
        glBegin(GL_LINES)
        glVertex2f(PLAYER_POS_X, PLAYER_POS_Y)
        glVertex2f(ray_end_x, ray_end_y)
        glEnd()

        # Move to next ray
        ray_angle += FOV / NUM_RAYS

    glPopMatrix()


def draw_3d_view():
    """Draw a simple 3D representation based on raycasting"""
    offset_x, offset_y = get_camera_offset()

    # Apply shake to 3D view as well
    glPushMatrix()
    glTranslatef(offset_x, offset_y, 0)

    # Draw 3D view background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2i(WINDOW_WIDTH // 2, 0)
    glVertex2i(WINDOW_WIDTH, 0)
    glVertex2i(WINDOW_WIDTH, WINDOW_HEIGHT)
    glVertex2i(WINDOW_WIDTH // 2, WINDOW_HEIGHT)
    glEnd()

    ray_angle = PLAYER_ANGLE - FOV / 2
    ray_width = (WINDOW_WIDTH // 2) / NUM_RAYS

    for ray in range(NUM_RAYS):
        # Normalize ray angle
        ray_angle = ray_angle % (2 * pi)

        # Ray direction vector
        ray_dir_x = cos(ray_angle)
        ray_dir_y = sin(ray_angle)

        # Player's position in map coordinates
        map_x = int(PLAYER_POS_X / TILE_SIZE)
        map_y = int(PLAYER_POS_Y / TILE_SIZE)

        # Length of ray from current position to next x or y-side
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

        # Direction to step in x or y direction (either +1 or -1)
        step_x = 1 if ray_dir_x >= 0 else -1
        step_y = 1 if ray_dir_y >= 0 else -1

        # Length of ray from one x or y-side to next x or y-side
        if ray_dir_x < 0:
            side_dist_x = (PLAYER_POS_X / TILE_SIZE - map_x) * delta_dist_x
        else:
            side_dist_x = (map_x + 1.0 - PLAYER_POS_X / TILE_SIZE) * delta_dist_x

        if ray_dir_y < 0:
            side_dist_y = (PLAYER_POS_Y / TILE_SIZE - map_y) * delta_dist_y
        else:
            side_dist_y = (map_y + 1.0 - PLAYER_POS_Y / TILE_SIZE) * delta_dist_y

        # Perform DDA (Digital Differential Analysis)
        hit = 0
        side = 0

        while hit == 0:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= MAP_SIZE_X or map_y < 0 or map_y >= MAP_SIZE_Y:
                hit = 1
            elif my_map[map_y * MAP_SIZE_X + map_x] == 1:
                hit = 1

        # Calculate distance projected on camera direction
        if side == 0:
            perp_wall_dist = (map_x - PLAYER_POS_X / TILE_SIZE + (1 - step_x) / 2) / ray_dir_x
        else:
            perp_wall_dist = (map_y - PLAYER_POS_Y / TILE_SIZE + (1 - step_y) / 2) / ray_dir_y

        # Calculate height of line to draw on screen
        line_height = int(WINDOW_HEIGHT / perp_wall_dist) if perp_wall_dist > 0 else WINDOW_HEIGHT

        # Calculate lowest and highest pixel to fill in current stripe
        draw_start = max(-line_height // 2 + WINDOW_HEIGHT // 2, 0)
        draw_end = min(line_height // 2 + WINDOW_HEIGHT // 2, WINDOW_HEIGHT - 1)

        # Choose wall color based on side hit
        if side == 1:
            glColor3f(0.7, 0.7, 0.7)  # Darker color for y-side walls
        else:
            glColor3f(0.9, 0.9, 0.9)  # Lighter color for x-side walls

        # Draw the wall slice
        x_pos = WINDOW_WIDTH // 2 + ray * ray_width
        glBegin(GL_QUADS)
        glVertex2f(x_pos, draw_start)
        glVertex2f(x_pos + ray_width, draw_start)
        glVertex2f(x_pos + ray_width, draw_end)
        glVertex2f(x_pos, draw_end)
        glEnd()

        # Move to next ray
        ray_angle += FOV / NUM_RAYS

    glPopMatrix()


# Display function
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_map()
    cast_rays()
    draw_player()
    draw_3d_view()
    glutSwapBuffers()


def update_player_direction():
    """Update delta vectors based on current angle"""
    global PLAYER_DELTA_X, PLAYER_DELTA_Y
    PLAYER_DELTA_X = cos(PLAYER_ANGLE) * 5
    PLAYER_DELTA_Y = sin(PLAYER_ANGLE) * 5


# check for key presses
def check_keys(key, x, y):
    global PLAYER_POS_X, PLAYER_POS_Y, PLAYER_DELTA_X, PLAYER_DELTA_Y, PLAYER_ANGLE

    key = key.decode("utf-8")
    PLAYER_ANGLE = PLAYER_ANGLE % (2 * pi)

    if key == 'a':
        PLAYER_ANGLE -= 0.1
        update_player_direction()
    if key == 'd':
        PLAYER_ANGLE += 0.1
        update_player_direction()
    if key == 'w':
        PLAYER_POS_X += PLAYER_DELTA_X
        PLAYER_POS_Y += PLAYER_DELTA_Y
    if key == 's':
        PLAYER_POS_X -= PLAYER_DELTA_X
        PLAYER_POS_Y -= PLAYER_DELTA_Y
    if key == 'c':  # Toggle camera shake
        trigger_camera_shake()

    # Keep angle within 0-2π range
    PLAYER_ANGLE = PLAYER_ANGLE % (2 * pi)

    # Request redisplay
    glutPostRedisplay()


# Initialize OpenGL settings
def init():
    # background color dark gray
    glClearColor(0.3, 0.3, 0.3, 0)
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    # initial player position
    global PLAYER_POS_X, PLAYER_POS_Y
    PLAYER_POS_X = 300
    PLAYER_POS_Y = 300


def main():
    # Initialize GLUT
    glutInit()
    # Create the window
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Raycasting Test")
    # Initialize my OpenGL settings
    init()
    # Register the display function
    glutDisplayFunc(display)
    # Register the idle function to continuously check for key presses
    glutKeyboardFunc(check_keys)
    # Run the main loop
    glutMainLoop()


if __name__ == "__main__":
    main()