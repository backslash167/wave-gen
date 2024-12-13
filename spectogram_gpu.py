import matplotlib
import numpy as np
from vispy import app, gloo
from scipy.signal import spectrogram
import matplotlib.cm as cm
import sounddevice as sd
import time

print(sd.query_devices())
print(sd.default.device)

import numpy.fft as fft




from vispy.gloo import gl
import ctypes

# Enable system DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    print(f"Failed to set DPI awareness: {e}")

def get_dpi_scaling():
    hdc = ctypes.windll.user32.GetDC(0)  # Get device context for the screen
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 = LOGPIXELSX
    ctypes.windll.user32.ReleaseDC(0, hdc)
    return dpi / 96.0  # Normalize against standard DPI (96 DPI)

# OpenGL texture parameters
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

# Fragment shader with GPU-based colormap
fragment_shader = """
uniform sampler2D u_texture;
uniform sampler2D u_colormap;
varying vec2 v_texcoord;
void main() {
    float intensity = texture2D(u_texture, v_texcoord).r; // Get normalized intensity
    vec4 color = texture2D(u_colormap, vec2(intensity, 0.0)); // Map intensity to colormap
    gl_FragColor = color;
}
"""

class SpectrogramCanvas(app.Canvas):
    def __init__(self, sample_rate, block_size, freq_min, freq_max, time_window):
        super().__init__(keys="interactive", size=(2560, 1440))
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.freq_min = freq_min
        self.freq_max = freq_max
        self.time_window = time_window

        # Initialize sounddevice input stream
        self.audio_buffer = np.zeros(block_size, dtype=np.float32)  # Placeholder buffer
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.audio_callback,
            blocksize=self.block_size,
            dtype='float32'
        )
        self.stream.start()

        # Compute initial spectrogram
        _, _, initial_Sxx = spectrogram(np.zeros(block_size), fs=sample_rate, nperseg=256, noverlap=128)
        self.data = np.zeros((initial_Sxx.shape[0], 1024), dtype=np.float32)  # Match spectrogram frequency bins

        # Prepare texture for data
        self.texture = gloo.Texture2D(self.data, interpolation="linear")

        # Prepare colormap texture
        self.colormap_texture = self.create_colormap_texture()

        # Create shader program
        self.program = gloo.Program(vertex_shader, fragment_shader)
        self.program["u_texture"] = self.texture
        self.program["u_colormap"] = self.colormap_texture
        self.program["a_position"] = gloo.VertexBuffer(
            np.array([[-1, -1], [+1, -1], [-1, +1], [+1, +1]], dtype=np.float32)
        )
        self.program["a_texcoord"] = gloo.VertexBuffer(
            np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float32)
        )

        gloo.set_state(clear_color="black", blend=True, blend_func=("src_alpha", "one_minus_src_alpha"))

        self.timer = app.Timer(0.001, connect=self.update_spectrogram, start=True)
        self.show()

    def create_colormap_texture(self):
        """Generate a texture from a colormap."""
        colormap = matplotlib.colormaps.get_cmap("viridis")
        colormap_data = (colormap(np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)
        colormap_texture = gloo.Texture2D(colormap_data[np.newaxis, :, :], interpolation="linear")
        return colormap_texture

    def audio_callback(self, indata, frames, time, status):
        """Audio callback function to capture real-time audio data."""
        if status:
            print(f"Audio stream status: {status}")
        self.audio_buffer = np.copy(indata[:, 0])  # Copy the audio data to the buffer

    def update_spectrogram(self, event):
        # start_time = time.perf_counter()  # Start timing

        # Use real-time audio data
        # audio_data = np.sin(2 * np.pi * 6000 * np.arange(block_size) / sample_rate)
        audio_data = self.audio_buffer
        # print(f"Sampling rate: {self.stream.samplerate}")
        # fft_data = fft.rfft(audio_data)
        # freqs = fft.rfftfreq(len(audio_data), 1 / sample_rate)
        # max_freq = freqs[np.argmax(np.abs(fft_data))]
        # print(f"Maximum frequency in audio input: {max_freq} Hz")

        # Compute spectrogram
        f, t, Sxx = spectrogram(audio_data, fs=self.sample_rate, nperseg=1024, noverlap=512)

        # Downsample spectrogram data for visualization
        Sxx = Sxx[:min(self.data.shape[0], Sxx.shape[0]), :]  # Match number of rows

        # Convert to dB and normalize
        Sxx = 10 * np.log10(Sxx + 1e-10)
        Sxx = np.clip((Sxx - np.min(Sxx)) / (np.max(Sxx) - np.min(Sxx)), 0, 1)

        # Shift spectrogram data
        self.data[:, :-1] = self.data[:, 1:]  # Shift left
        self.data[:Sxx.shape[0], -1] = Sxx.mean(axis=1)  # Add new column
        if Sxx.shape[0] < self.data.shape[0]:  # Zero remaining rows if Sxx has fewer rows
            self.data[Sxx.shape[0]:, -1] = 0

        # Update texture with new data
        self.texture.set_data(self.data)
        self.update()

        # Print frame processing time
        # frame_time = time.perf_counter() - start_time  # Measure elapsed time
        # print(f"VisPy frame time: {frame_time:.10f} seconds")

    def on_draw(self, event):
        gloo.clear()
        self.program.draw("triangle_strip")

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.size)


# Parameters
sample_rate = 44100  # Sampling rate in Hz
block_size = 2048  # Number of samples per block
freq_min = 80  # Minimum frequency to display
freq_max = 44100  # Maximum frequency to display
time_window = 5  # Time window in seconds

# Start the SpectrogramCanvas
canvas = SpectrogramCanvas(sample_rate, block_size, freq_min, freq_max, time_window)
app.run()