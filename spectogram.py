from vispy import app, scene
import numpy as np
import sounddevice as sd
from scipy.signal import spectrogram

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QSlider, QWidget
from PyQt6.QtCore import Qt


class SpectrogramCanvasWithScale(scene.SceneCanvas):
    def __init__(self, sample_rate, block_size, freq_min, freq_max, time_window):
        super().__init__(keys="interactive", size=(2560, 1440))

        # Allow adding new attributes
        self.unfreeze()

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

        # Create a grid layout
        self.grid = self.central_widget.add_grid(spacing=0)

        # Add a view to the grid for the spectrogram
        self.view = self.grid.add_view(row=0, col=1, camera='panzoom', border_color='white')
        self.view.camera.aspect = 1  # Keep aspect ratio consistent

        height = 1440//2
        width = 2560

        # Compute initial spectrogram shape
        _, _, initial_Sxx = spectrogram(np.zeros(block_size), fs=sample_rate,  nperseg=2<<12, noverlap=128)
        self.data = np.zeros((width, height), dtype=np.float32)

        # Create an image visual for the spectrogram
        self.image = scene.visuals.Image(
            self.data,
            parent=self.view.scene,
            cmap='viridis',
            clim=(0, 1),  # Normalize intensity range between 0 and 1
        )

        # Dynamically adjust the view rectangle
        self.view.camera.rect = (0, 0, self.data.shape[1], self.data.shape[0])

        # Add x-axis (time) and y-axis (frequency)
        #self.x_axis = scene.AxisWidget(orientation='bottom', text_color='white')
        self.y_axis = scene.AxisWidget(orientation='left', text_color='white')

        # Add axes to the grid
        #self.grid.add_widget(self.x_axis, row=1, col=1)  # X-axis
        self.grid.add_widget(self.y_axis, row=0, col=0)  # Y-axis

        # Set stretch factors
        self.grid.stretch = (1, 0.2)  # Stretch for x-axis
        self.grid.stretch = (0.2, 1)  # Stretch for y-axis

        # Link axes to the spectrogram view
        #self.x_axis.link_view(self.view)
        self.y_axis.link_view(self.view)

        # Create a timer for updating the spectrogram
        self.timer = app.Timer(0.01, connect=self.update_spectrogram, start=True)

        self.show()

    def audio_callback(self, indata, frames, time, status):
        """Audio callback function to capture real-time audio data."""
        if status:
            print(f"Audio stream status: {status}")
        self.audio_buffer = np.copy(indata[:, 0])  # Copy the audio data to the buffer

    def update_spectrogram(self, event):
        """Update the spectrogram with audio data."""
        # Use real-time audio data
        audio_data = self.audio_buffer

        # Compute spectrogram
        f, t, Sxx = spectrogram(audio_data, fs=self.sample_rate, nperseg=2<<12, noverlap=128)

        # Convert to dB and normalize
        Sxx = 10 * np.log10(Sxx + 1e-10)
        Sxx = np.clip((Sxx - np.min(Sxx)) / (np.max(Sxx) - np.min(Sxx)), 0, 1)

        # Shift spectrogram data
        self.data[:, :-1] = self.data[:, 1:]  # Shift left
        self.data[:Sxx.shape[0], -1] = Sxx.mean(axis=1)  # Add new column
        if Sxx.shape[0] < self.data.shape[0]:  # Zero remaining rows if Sxx has fewer rows
            self.data[Sxx.shape[0]:, -1] = 0

        # Update texture with new data
        self.image.set_data(self.data)
        self.update()

class SliderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slider Example")
        self.setGeometry(100, 100, 400, 300)

        # Create a central widget and set a layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Example sliders
        self.create_slider(layout, "Frequency Min", 0, 1000, 80)
        self.create_slider(layout, "Frequency Max", 1000, 8000, 8000)
        self.create_slider(layout, "Gain", 0, 100, 50)
        self.create_slider(layout, "Time Window", 1, 10, 5)

    def create_slider(self, layout, label_text, min_value, max_value, initial_value):
        """Create a labeled slider and add it to the layout."""
        # Add a label
        label = QLabel(f"{label_text}: {initial_value}")
        layout.addWidget(label)

        # Create the slider
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_value, max_value)
        slider.setValue(initial_value)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval((max_value - min_value) // 10)
        layout.addWidget(slider)

        # Connect slider's valueChanged signal to update the label and print value
        slider.valueChanged.connect(lambda value: self.slider_changed(label, label_text, value))

    def slider_changed(self, label, label_text, value):
        """Update the label and print the slider value."""
        label.setText(f"{label_text}: {value}")
        print(f"{label_text}: {value}")


# Parameters
sample_rate = 44100  # Sampling rate in Hz
block_size = 2048  # Number of samples per block
freq_min = 0  # Minimum frequency to display
freq_max = 8000  # Maximum frequency to display
time_window = 5  # Time window in seconds

# Start the SpectrogramCanvas
# slider_app = QApplication([])
# window = SliderWindow()
# window.show()
# slider_app.exec()


canvas = SpectrogramCanvasWithScale(sample_rate, block_size, freq_min, freq_max, time_window)
app.run()
