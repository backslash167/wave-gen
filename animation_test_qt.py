import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import sounddevice as sd


class SineWaveApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Sine Wave with PyQtGraph")

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # PyQtGraph plot widget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.audio_buffer_plot = pg.PlotWidget()
        layout.addWidget(self.audio_buffer_plot)

        self.buffer_size = 1024*2

        # PyQtGraph plot setup for audio buffer
        self.buffer_x = np.arange(self.buffer_size)  # X-axis for the buffer plot
        self.buffer_y = np.zeros(self.buffer_size)  # Initialize buffer data
        self.buffer_plot = self.audio_buffer_plot.plot(self.buffer_x, self.buffer_y, pen=pg.mkPen('r', width=2))
        self.audio_buffer_plot.setLimits(yMin=-1, yMax=1)
        self.audio_buffer_plot.setRange(yRange=(-1.0, 1.0))

        # Sine wave parameters
        self.frequency = 440  # Hz
        self.amplitude = 0.5
        self.phase = 0.0
        self.sample_rate = 44100  # Samples per second
        self.duration = 1.0
        self.x = np.linspace(0, 2 * np.pi, self.sample_rate)
        self.y = self.amplitude * np.sin(self.x)
        self.pvel = 0

        # PyQtGraph plot setup
        self.plot = self.plot_widget.plot(self.x, self.y, pen=pg.mkPen('r', width=3))

        # Fix extents
        self.plot_widget.setLimits(xMin=0, xMax=2 * np.pi, yMin=-1, yMax=1)
        self.plot_widget.getPlotItem().setRange(xRange=(0, 2 * np.pi), yRange=(-1.0, 1.0))
        self.ploti = self.plot_widget.getPlotItem()
        # self.ploti.showGrid(0, 1, 1.0)
        self.ploti.showAxis('top')

        # Sliders for frequency and amplitude
        self.pvel_slider = QSlider(Qt.Horizontal)
        self.pvel_slider.setRange(-2000, 2000)  # Frequency range: 1 Hz to 20 Hz
        self.pvel_slider.setValue(self.pvel)  # Default: 1 Hz
        self.pvel_slider.valueChanged.connect(self.update_pvel)
        layout.addWidget(QLabel("phase_velocity (Hz/s)"))
        layout.addWidget(self.pvel_slider)

        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(1, 20000)  # Frequency range: 1 Hz to 20 Hz
        self.freq_slider.setValue(self.frequency)  # Default: 1 Hz
        self.freq_slider.setSingleStep(1)
        self.freq_slider.valueChanged.connect(self.update_frequency)
        layout.addWidget(QLabel("Frequency (Hz)"))
        layout.addWidget(self.freq_slider)

        self.amp_slider = QSlider(Qt.Horizontal)
        self.amp_slider.setRange(1, 100)  # Amplitude range: 1 to 10
        self.amp_slider.setValue(50)  # Default: 10
        self.amp_slider.valueChanged.connect(self.update_amplitude)
        layout.addWidget(QLabel("Amplitude"))
        layout.addWidget(self.amp_slider)

        self.zero_axis = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('grey', width=1))
        self.plot_widget.addItem(self.zero_axis)

        # Timer for updating the sine wave
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(16)  # ~60 FPS

        # Start audio stream
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.audio_callback,
            blocksize=self.buffer_size
        )
        self.stream.start()


    def update_frequency(self, value):
        self.frequency = value

    def update_amplitude(self, value):
        self.amplitude = value / self.amp_slider.maximum()

    def update_pvel(self, value):
        self.pvel = value

    def audio_callback(self, outdata, frames, time, status):
        """
        Callback for sounddevice. Generates audio samples dynamically.
        """
        if status:
            print(status)

        # Generate audio samples with frequency, amplitude, and phase
        t = np.arange(frames) / self.sample_rate
        samples = self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase)

        samples = samples * np.sin(2 * np.pi * t + self.phase)

        # Update the buffer plot
        self.buffer_y = samples
        self.buffer_plot.setData(self.buffer_x, self.buffer_y)

        # Update phase for continuity
        self.phase += 2 * np.pi * self.frequency * frames / self.sample_rate

        # Output audio buffer
        outdata[:, 0] = samples


    def update_plot(self):
        # self.phase += (2 * np.pi * self.frequency / self.sample_rate)
        self.phase += 2 * np.pi * (200*self.pvel) / self.sample_rate
        self.y = self.amplitude * np.sin(2 * np.pi * (self.frequency/500) * self.x + self.phase)
        # self.y = self.amplitude * np.sin(self.x + self.phase)
        self.plot.setData(self.x, self.y)

    def closeEvent(self, event):
        """
        Ensure the audio stream stops when the window is closed.
        """
        self.stream.stop()
        self.stream.close()
        super().closeEvent(event)


class Audio():
    def __init__(self):
        super()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SineWaveApp()
    window.resize(2560, 1440)
    window.show()
    sys.exit(app.exec_())
