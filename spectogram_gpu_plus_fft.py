import numpy as np
import sounddevice as sd
from vispy import app, gloo
import matplotlib.cm as cm
import matplotlib

# Enable DPI awareness for high-resolution displays
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    print(f"Failed to set DPI awareness: {e}")

# OpenGL texture parameters
from vispy.gloo import gl
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)

# Vertex shader
vertex_shader = """
attribute vec2 a_position;
attribute vec2 a_texcoord;
varying vec2 v_texcoord;
void main() {
    v_texcoord = a_texcoord;
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

# Fragment shader
fragment_shader = """
uniform sampler2D u_texture;
uniform sampler2D u_colormap;
varying vec2 v_texcoord;
void main() {
    float intensity = texture2D(u_texture, v_texcoord).r; // Intensity from data
    vec4 color = texture2D(u_colormap, vec2(intensity, 0.0)); // Map to colormap
    gl_FragColor = color;
}
"""

class TimeFFTCanvas(app.Canvas):
    def __init__(self, sample_rate, block_size):
        super().__init__(keys='interactive', size=(1280, 720))
        self.sample_rate = sample_rate
        self.block_size = block_size

        # Audio buffer
        self.audio_buffer = np.zeros(block_size, dtype=np.float32)

        # Initialize sounddevice input stream
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            callback=self.audio_callback,
            dtype='float32'
        )
        self.stream.start()

        # Time-Series Data Texture
        self.time_data = np.zeros((1, self.block_size), dtype=np.float32)
        self.time_texture = gloo.Texture2D(self.time_data, interpolation='linear')

        # FFT Data Texture
        self.fft_data = np.zeros((1, self.block_size // 2), dtype=np.float32)
        self.fft_texture = gloo.Texture2D(self.fft_data, interpolation='linear')

        # Colormap
        self.colormap_texture = self.create_colormap_texture()

        # Create shader program
        self.program = gloo.Program(vertex_shader, fragment_shader)
        self.program['u_colormap'] = self.colormap_texture
        self.program['a_position'] = gloo.VertexBuffer(np.array([[-1, -1], [1, -1], [-1, 1], [1, 1]], dtype=np.float32))
        self.program['a_texcoord'] = gloo.VertexBuffer(np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float32))

        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.timer = app.Timer('auto', connect=self.update_visualization, start=True)

        # Box Program
        # self.box_program = gloo.Program(
        #     """
        #     attribute vec2 a_position;
        #     void main() {
        #         gl_Position = vec4(a_position, 0.0, 1.0);
        #     }
        #     """,
        #     """
        #     uniform vec4 u_color;
        #     void main() {
        #         gl_FragColor = u_color;
        #     }
        #     """
        # )
        # self.box_vertices = gloo.VertexBuffer(np.array([
        #     [-0.5, -0.5],  # Bottom-left
        #     [0.5, -0.5],   # Bottom-right
        #     [0.5, 0.5],    # Top-right
        #     [-0.5, 0.5],   # Top-left
        #     [-0.5, -0.5],  # Close the loop
        # ], dtype=np.float32))
        # self.box_program['a_position'] = self.box_vertices
        # self.box_program['u_color'] = (1.0, 0.0, 0.0, 1.0)  # Red box

        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.timer = app.Timer('auto', connect=self.update_visualization, start=True)
        self.show()

    def create_colormap_texture(self):
        """Generate a texture from a colormap."""
        colormap = matplotlib.colormaps.get_cmap('viridis')
        colormap_data = (colormap(np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)
        colormap_texture = gloo.Texture2D(colormap_data[np.newaxis, :, :], interpolation='linear')
        return colormap_texture

    def audio_callback(self, indata, frames, time, status):
        """Callback to process audio data."""
        if status:
            print(f"Audio stream status: {status}")
        self.audio_buffer = np.copy(indata[:, 0])  # Copy audio data

    def update_visualization(self, event):
        """Update both time-series and FFT visualizations."""
        # Update Time-Series Data
        time_series = self.audio_buffer
        time_series_normalized = (time_series - np.min(time_series)) / (np.max(time_series) - np.min(time_series))
        self.time_data = time_series_normalized[np.newaxis, :]
        self.time_texture.set_data(self.time_data)

        # Compute FFT
        fft_result = np.abs(np.fft.rfft(self.audio_buffer))  # Compute magnitude
        fft_result = 10 * np.log10(fft_result + 1e-10)  # Convert to dB scale
        fft_result_normalized = (fft_result - np.min(fft_result)) / (np.max(fft_result) - np.min(fft_result))
        self.fft_data = fft_result_normalized[np.newaxis, :]
        self.fft_texture.set_data(self.fft_data)

        self.update()

    def on_draw(self, event):
        gloo.clear()

        # Draw Time-Series in top half
        gloo.set_viewport(0, self.size[1] // 2, self.size[0], self.size[1] // 2)
        self.program['u_texture'] = self.time_texture
        self.program.draw('triangle_strip')

        # Draw FFT in bottom half
        gloo.set_viewport(0, 0, self.size[0], self.size[1] // 2)
        self.program['u_texture'] = self.fft_texture
        self.program.draw('triangle_strip')

        # Draw Box
        gloo.set_viewport(0, 0, *self.size)  # Full canvas for the box
        self.box_program.draw('line_strip')

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.size)


# Parameters
sample_rate = 44100  # Sampling rate in Hz
block_size = 2048  # Number of samples per block

# Start the visualization
canvas = TimeFFTCanvas(sample_rate, block_size)
app.run()
