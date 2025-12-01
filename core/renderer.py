from OpenGL.GL import *
from OpenGL.GLU import *
from textures.texture_manager import TextureID

import numpy as np
import ctypes

# Vertex shader for textured walls
VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texCoord;
layout(location = 2) in float shade;
layout(location = 3) in float texIndex;

out vec2 fragTexCoord;
out float fragShade;
flat out int fragTexIndex;

uniform mat4 projection;

void main() {
    gl_Position = projection * vec4(position, 0.0, 1.0);
    fragTexCoord = texCoord;
    fragShade = shade;
    fragTexIndex = int(texIndex);
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 fragTexCoord;
in float fragShade;
flat in int fragTexIndex;

out vec4 outColor;

uniform sampler2D textures[4];

void main() {
    vec4 texColor;
    if (fragTexIndex == 0) {
        texColor = texture(textures[0], fragTexCoord);
    } else if (fragTexIndex == 1) {
        texColor = texture(textures[1], fragTexCoord);
    } else if (fragTexIndex == 2) {
        texColor = texture(textures[2], fragTexCoord);
    } else {
        texColor = texture(textures[3], fragTexCoord);
    }
    outColor = vec4(texColor.rgb * fragShade, texColor.a);
}
"""

# Simple color shader for background
COLOR_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec3 color;

out vec3 fragColor;

uniform mat4 projection;

void main() {
    gl_Position = projection * vec4(position, 0.0, 1.0);
    fragColor = color;
}
"""

COLOR_FRAGMENT_SHADER = """
#version 330 core
in vec3 fragColor;
out vec4 outColor;

void main() {
    outColor = vec4(fragColor, 1.0);
}
"""

class Renderer:
    def __init__(self, engine):
        self.engine = engine
        self.raycaster = engine.raycaster
        self.texture_manager = engine.texture_manager

        # minimap settings
        self.minimap_scale = 0.15
        self.minimap_padding = 10
        
        # Shading settings (distance-based fog effect)
        self.shade_factor = 1.0 / 600.0  # How quickly walls darken with distance
        self.min_shade = 0  # Minimum brightness (prevents pure black)
        self.max_shade = 0.5  # Maximum brightness (close walls)
        self.side_shade_multiplier = 0.4  # Darken N/S walls for depth perception
        
        # GPU resources (initialized later)
        self.textured_shader = None
        self.color_shader = None
        self.wall_vao = None
        self.wall_vbo = None
        self.bg_vao = None
        self.bg_vbo = None
        self.gpu_textures = {}  # TextureID -> OpenGL texture ID
        self.initialized = False
        
        # Pre-allocated buffers for textured wall rendering
        # Each vertex: position(2) + texCoord(2) + shade(1) + texIndex(1) = 6 floats
        self.max_wall_quads = 1000
        self.wall_buffer = np.zeros((self.max_wall_quads * 6, 6), dtype=np.float32)
        self.wall_quad_count = 0
        
        # Background buffer: position(2) + color(3) = 5 floats
        # Increased size to accommodate shaded floor/ceiling strips
        self.floor_ceiling_strips = 32  # Number of strips for gradient effect
        self.bg_buffer = np.zeros((self.floor_ceiling_strips * 2 * 6, 5), dtype=np.float32)
        
        # Floor and ceiling base colors
        self.ceiling_color = (0.3, 0.3, 0.35)  # Slightly blue-ish gray
        self.floor_color = (0.25, 0.2, 0.15)   # Brownish gray

    def compile_shader(self, source, shader_type):
        """Compile a shader from source."""
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"Shader compilation failed: {error}")
        return shader

    def link_program(self, vertex_shader, fragment_shader):
        """Link vertex and fragment shaders into a program."""
        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)
        
        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program).decode()
            raise RuntimeError(f"Program linking failed: {error}")
        
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        return program

    def upload_texture_to_gpu(self, tex_id):
        """Upload a texture from texture_manager to GPU memory."""
        if tex_id in self.gpu_textures:
            return self.gpu_textures[tex_id]
        
        texture_data = self.texture_manager.get_texture(tex_id)
        width = self.texture_manager.width
        height = self.texture_manager.height
        
        # Convert to numpy array (RGB format)
        pixels = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                pixels[y, x] = texture_data[y][x]
        
        # Create OpenGL texture
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        
        self.gpu_textures[tex_id] = tex
        return tex

    def init_gl_resources(self):
        """Initialize OpenGL shaders and buffers. Call after OpenGL context is created."""
        if self.initialized:
            return
            
        try:
            # Compile textured shader
            vert = self.compile_shader(VERTEX_SHADER, GL_VERTEX_SHADER)
            frag = self.compile_shader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
            self.textured_shader = self.link_program(vert, frag)
            
            # Compile color shader for background
            vert2 = self.compile_shader(COLOR_VERTEX_SHADER, GL_VERTEX_SHADER)
            frag2 = self.compile_shader(COLOR_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
            self.color_shader = self.link_program(vert2, frag2)
            
            # Create wall VAO/VBO (textured quads)
            self.wall_vao = glGenVertexArrays(1)
            glBindVertexArray(self.wall_vao)
            
            self.wall_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.wall_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.wall_buffer.nbytes, None, GL_DYNAMIC_DRAW)
            
            stride = 6 * 4  # 6 floats * 4 bytes
            # position (location 0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # texCoord (location 1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
            glEnableVertexAttribArray(1)
            # shade (location 2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(16))
            glEnableVertexAttribArray(2)
            # texIndex (location 3)
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(20))
            glEnableVertexAttribArray(3)
            
            # Create background VAO/VBO
            self.bg_vao = glGenVertexArrays(1)
            glBindVertexArray(self.bg_vao)
            
            self.bg_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.bg_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.bg_buffer.nbytes, None, GL_DYNAMIC_DRAW)
            
            bg_stride = 5 * 4  # 5 floats * 4 bytes
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, bg_stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, bg_stride, ctypes.c_void_p(8))
            glEnableVertexAttribArray(1)
            
            glBindVertexArray(0)
            
            # Upload textures to GPU
            if self.texture_manager:
                for tex_id in TextureID:
                    if tex_id in self.texture_manager.textures:
                        self.upload_texture_to_gpu(tex_id)
            
            self.initialized = True
            
        except Exception as e:
            print(f"Failed to initialize GPU renderer: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to immediate mode")
            self.initialized = False

    def create_ortho_matrix(self, left, right, bottom, top):
        """Create orthographic projection matrix."""
        matrix = np.zeros((4, 4), dtype=np.float32)
        matrix[0, 0] = 2.0 / (right - left)
        matrix[1, 1] = 2.0 / (top - bottom)
        matrix[2, 2] = -1.0
        matrix[3, 0] = -(right + left) / (right - left)
        matrix[3, 1] = -(top + bottom) / (top - bottom)
        matrix[3, 3] = 1.0
        return matrix

    def begin_wall_batch(self):
        """Start a new batch of textured wall quads."""
        self.wall_quad_count = 0

    def add_textured_wall_slice(self, x, width, start, end, tex_u, tex_v_start, tex_v_end, shade, tex_index):
        """Add a textured wall slice to the batch."""
        if self.wall_quad_count >= self.max_wall_quads:
            self.flush_wall_batch()
        
        idx = self.wall_quad_count * 6
        
        # Two triangles per quad (6 vertices)
        # Each vertex: [x, y, u, v, shade, texIndex]
        # Triangle 1: top-left, top-right, bottom-right
        self.wall_buffer[idx] = [x, start, tex_u, tex_v_start, shade, tex_index]
        self.wall_buffer[idx + 1] = [x + width, start, tex_u, tex_v_start, shade, tex_index]
        self.wall_buffer[idx + 2] = [x + width, end, tex_u, tex_v_end, shade, tex_index]
        # Triangle 2: top-left, bottom-right, bottom-left
        self.wall_buffer[idx + 3] = [x, start, tex_u, tex_v_start, shade, tex_index]
        self.wall_buffer[idx + 4] = [x + width, end, tex_u, tex_v_end, shade, tex_index]
        self.wall_buffer[idx + 5] = [x, end, tex_u, tex_v_end, shade, tex_index]
        
        self.wall_quad_count += 1

    def flush_wall_batch(self):
        """Render all batched textured wall quads."""
        if self.wall_quad_count == 0:
            return
        
        vertex_count = self.wall_quad_count * 6
        
        glBindVertexArray(self.wall_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.wall_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.wall_buffer[:vertex_count].nbytes, 
                        self.wall_buffer[:vertex_count])
        
        glDrawArrays(GL_TRIANGLES, 0, vertex_count)
        glBindVertexArray(0)
        self.wall_quad_count = 0

    def draw_background_gpu(self, W, H):
        """Draw background (ceiling and floor) with distance-based shading."""
        mid = H // 2
        num_strips = self.floor_ceiling_strips
        strip_height = mid / num_strips
        
        vertex_idx = 0
        
        # Draw ceiling strips (from horizon up to top)
        # Strips near horizon are darker (simulating distance)
        for i in range(num_strips):
            # y position: strip 0 is at horizon, strip (num_strips-1) is at top
            y_bottom = mid - (i * strip_height)
            y_top = mid - ((i + 1) * strip_height)
            
            # Calculate shade: near horizon (i=0) is dark, near top (i=num_strips) is bright
            # This simulates looking at distant ceiling near horizon vs close ceiling above
            shade = self.min_shade + (self.max_shade - self.min_shade) * (i / num_strips)
            
            r = self.ceiling_color[0] * shade
            g = self.ceiling_color[1] * shade
            b = self.ceiling_color[2] * shade
            
            # Two triangles per strip
            self.bg_buffer[vertex_idx] = [0, y_top, r, g, b]
            self.bg_buffer[vertex_idx + 1] = [W, y_top, r, g, b]
            self.bg_buffer[vertex_idx + 2] = [W, y_bottom, r, g, b]
            self.bg_buffer[vertex_idx + 3] = [0, y_top, r, g, b]
            self.bg_buffer[vertex_idx + 4] = [W, y_bottom, r, g, b]
            self.bg_buffer[vertex_idx + 5] = [0, y_bottom, r, g, b]
            vertex_idx += 6
        
        # Draw floor strips (from horizon down to bottom)
        # Strips near horizon are darker (simulating distance)
        for i in range(num_strips):
            # y position: strip 0 is at horizon, strip (num_strips-1) is at bottom
            y_top = mid + (i * strip_height)
            y_bottom = mid + ((i + 1) * strip_height)
            
            # Calculate shade: near horizon (i=0) is dark, near bottom (i=num_strips) is bright
            shade = self.min_shade + (self.max_shade - self.min_shade) * (i / num_strips)
            
            r = self.floor_color[0] * shade
            g = self.floor_color[1] * shade
            b = self.floor_color[2] * shade
            
            # Two triangles per strip
            self.bg_buffer[vertex_idx] = [0, y_top, r, g, b]
            self.bg_buffer[vertex_idx + 1] = [W, y_top, r, g, b]
            self.bg_buffer[vertex_idx + 2] = [W, y_bottom, r, g, b]
            self.bg_buffer[vertex_idx + 3] = [0, y_top, r, g, b]
            self.bg_buffer[vertex_idx + 4] = [W, y_bottom, r, g, b]
            self.bg_buffer[vertex_idx + 5] = [0, y_bottom, r, g, b]
            vertex_idx += 6
        
        glUseProgram(self.color_shader)
        proj_loc = glGetUniformLocation(self.color_shader, "projection")
        proj_matrix = self.create_ortho_matrix(0, W, H, 0)
        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, proj_matrix)
        
        glBindVertexArray(self.bg_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.bg_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.bg_buffer[:vertex_idx].nbytes, self.bg_buffer[:vertex_idx])
        glDrawArrays(GL_TRIANGLES, 0, vertex_idx)
        glBindVertexArray(0)

    # ------------------------------------------------------------
    # Projection helpers (keep for compatibility)
    # ------------------------------------------------------------

    def push_ortho(self, left, right, bottom, top):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(left, right, bottom, top)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def pop_ortho(self):
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # ------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------

    def draw_background(self, width, height):
        """Draw background with distance-based shading (fallback/immediate mode)."""
        mid = height // 2
        num_strips = self.floor_ceiling_strips
        strip_height = mid / num_strips
        
        # Draw ceiling strips (from horizon up to top)
        for i in range(num_strips):
            y_bottom = mid - (i * strip_height)
            y_top = mid - ((i + 1) * strip_height)
            
            shade = self.min_shade + (self.max_shade - self.min_shade) * (i / num_strips)
            
            r = self.ceiling_color[0] * shade
            g = self.ceiling_color[1] * shade
            b = self.ceiling_color[2] * shade
            
            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            glVertex2f(0, y_top)
            glVertex2f(width, y_top)
            glVertex2f(width, y_bottom)
            glVertex2f(0, y_bottom)
            glEnd()
        
        # Draw floor strips (from horizon down to bottom)
        for i in range(num_strips):
            y_top = mid + (i * strip_height)
            y_bottom = mid + ((i + 1) * strip_height)
            
            shade = self.min_shade + (self.max_shade - self.min_shade) * (i / num_strips)
            
            r = self.floor_color[0] * shade
            g = self.floor_color[1] * shade
            b = self.floor_color[2] * shade
            
            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            glVertex2f(0, y_top)
            glVertex2f(width, y_top)
            glVertex2f(width, y_bottom)
            glVertex2f(0, y_bottom)
            glEnd()

    def get_flat_map(self):
        return [t for row in self.engine.map.map_grid for t in row]

    # ------------------------------------------------------------
    # Texture Mapping Logic
    # ------------------------------------------------------------

    def get_texture_for_wall(self, tile_value):
        if tile_value == 1:
            return TextureID.BRICK
        elif tile_value == 2:
            return TextureID.STONE
        elif tile_value == 3:
            return TextureID.WOOD
        else:
            return TextureID.BRICK

    def get_texture_index(self, tex_id):
        """Get texture array index for shader."""
        mapping = {
            TextureID.BRICK: 0,
            TextureID.STONE: 1,
            TextureID.WOOD: 2,
            TextureID.DOOR: 3,
        }
        return mapping.get(tex_id, 0)

    def calculate_shade(self, distance, side):
        """
        Calculate shade value based on distance and wall side.
        Uses a fog-like effect where walls get darker with distance.
        
        Args:
            distance: Distance to the wall
            side: 0 for E/W walls, 1 for N/S walls
            
        Returns:
            Shade value between min_shade and max_shade
        """
        # Distance-based shading (fog effect)
        # shade decreases as distance increases
        distance_shade = max(self.min_shade, self.max_shade - distance * self.shade_factor)
        
        # Apply side-based shading (N/S walls are darker for depth perception)
        if side == 1:
            distance_shade *= self.side_shade_multiplier
        
        return distance_shade

    def draw_wall_slice(self, x, width, start, end, side, shade=1.0):
        # Apply the shade value to the base color
        if side == 1:
            base = 0.7
        else:
            base = 0.9
        
        color = base * shade
        glColor3f(color, color, color)

        glBegin(GL_QUADS)
        glVertex2f(x, start)
        glVertex2f(x + width, start)
        glVertex2f(x + width, end)
        glVertex2f(x, end)
        glEnd()

    # ------------------------------------------------------------
    # 3D View - GPU Accelerated
    # ------------------------------------------------------------

    def draw3D(self):
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        # Initialize GPU resources if not done
        self.init_gl_resources()

        if self.initialized:
            self.draw3D_gpu(W, H)
        else:
            self.draw3D_fallback(W, H)

    def draw3D_gpu(self, W, H):
        """GPU-accelerated 3D rendering with proper texture mapping."""
        # Draw background first
        self.draw_background_gpu(W, H)
        
        # Now draw textured walls
        glUseProgram(self.textured_shader)
        
        # Set projection matrix
        proj_loc = glGetUniformLocation(self.textured_shader, "projection")
        proj_matrix = self.create_ortho_matrix(0, W, H, 0)
        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, proj_matrix)
        
        # Bind textures to texture units
        for tex_id, gl_tex in self.gpu_textures.items():
            tex_index = self.get_texture_index(tex_id)
            glActiveTexture(GL_TEXTURE0 + tex_index)
            glBindTexture(GL_TEXTURE_2D, gl_tex)
            loc = glGetUniformLocation(self.textured_shader, f"textures[{tex_index}]")
            glUniform1i(loc, tex_index)
        
        # Start batching walls
        self.begin_wall_batch()
        
        # Player info
        pos = self.engine.player.position
        angle = self.engine.player.player_angle

        # Cast rays
        game_map = self.get_flat_map()
        rays = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            game_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )

        ray_w = W / self.raycaster.num_rays
        mid_y = H // 2
        tile = self.engine.map.grid_size

        # Batch all wall slices with proper texture coordinates
        for i, r in enumerate(rays):
            dist = r["distance"] if r["distance"] > 0 else 0.001
            line_h = int(min((tile * W) / dist, W))

            start = max(mid_y - line_h // 2, 0)
            end = min(mid_y + line_h // 2, H - 1)
            
            # Calculate texture coordinates
            wall_x = r["wall_x"]  # 0.0 to 1.0 across the wall
            tex_u = wall_x  # U coordinate (horizontal)
            
            # V coordinates depend on where the wall slice starts/ends
            # If wall is clipped, adjust V coordinates accordingly
            full_start = mid_y - line_h // 2
            full_end = mid_y + line_h // 2
            
            if line_h > 0:
                tex_v_start = (start - full_start) / line_h
                tex_v_end = (end - full_start) / line_h
            else:
                tex_v_start = 0.0
                tex_v_end = 1.0
            
            # Calculate distance-based shade with side shading
            shade = self.calculate_shade(dist, r["side"])
            
            # Get texture index
            tex_id = self.get_texture_for_wall(1)  # TODO: use actual tile value
            tex_index = float(self.get_texture_index(tex_id))
            
            self.add_textured_wall_slice(
                i * ray_w, ray_w, start, end,
                tex_u, tex_v_start, tex_v_end,
                shade, tex_index
            )

        # Flush all batched wall quads
        self.flush_wall_batch()
        
        glUseProgram(0)

    def draw3D_fallback(self, W, H):
        """Fallback to immediate mode if GPU init fails."""
        self.push_ortho(0, W, H, 0)
        self.draw_background(W, H)

        pos = self.engine.player.position
        angle = self.engine.player.player_angle

        game_map = self.get_flat_map()
        rays = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            game_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )

        ray_w = W / self.raycaster.num_rays
        mid_y = H // 2
        tile = self.engine.map.grid_size

        for i, r in enumerate(rays):
            dist = r["distance"] if r["distance"] > 0 else 0.001
            line_h = int(min((tile * W) / dist, W))
            start = max(mid_y - line_h // 2, 0)
            end = min(mid_y + line_h // 2, H - 1)
            
            # Calculate distance-based shade
            shade = self.calculate_shade(dist, r["side"])
            self.draw_wall_slice(i * ray_w, ray_w, start, end, r["side"], shade)

        self.pop_ortho()

    # ------------------------------------------------------------
    # 2D Minimap
    # ------------------------------------------------------------

    def setup_minimap_view(self):
        W = self.engine.game.WINDOW_WIDTH
        H = self.engine.game.WINDOW_HEIGHT

        map_w = self.engine.map.grid_x * self.engine.map.grid_size
        map_h = self.engine.map.grid_y * self.engine.map.grid_size
        aspect = map_w / map_h

        mini_size = min(W, H) * self.minimap_scale
        mini_w = mini_size * aspect
        mini_h = mini_size

        glViewport(
            self.minimap_padding,
            H - int(mini_h) - self.minimap_padding,
            int(mini_w),
            int(mini_h)
        )

        self.push_ortho(0, map_w, map_h, 0)

    def restore_full_viewport(self):
        glViewport(
            0,
            0,
            self.engine.game.WINDOW_WIDTH,
            self.engine.game.WINDOW_HEIGHT
        )
        self.pop_ortho()

    def draw_2d_rays(self):
        pos = self.engine.player.position
        angle = self.engine.player.player_angle

        game_map = self.get_flat_map()
        rays = self.raycaster.cast_rays(
            pos.x, pos.y, angle,
            game_map,
            self.engine.map.grid_x,
            self.engine.map.grid_y,
            self.engine.map.grid_size
        )

        glColor3f(1.0, 0.0, 0.0)
        glLineWidth(1)
        glBegin(GL_LINES)
        for r in rays:
            glVertex2f(r["start_x"], r["start_y"])
            glVertex2f(r["end_x"], r["end_y"])
        glEnd()

    def draw_2d_player(self):
        pos = self.engine.player.position
        delta = self.engine.player.position_delta

        glColor3f(1.0, 1.0, 0.0)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(pos.x, pos.y)
        glEnd()

        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(pos.x, pos.y)
        glVertex2f(pos.x + delta.x * 50, pos.y + delta.y * 50)
        glEnd()

    def draw2D(self):
        self.setup_minimap_view()

        self.engine.map.draw()
        self.draw_2d_rays()
        self.draw_2d_player()

        self.restore_full_viewport()