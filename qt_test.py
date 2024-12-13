from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 with Fixed Amplitude Extents")

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Set up a vertical layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create a Matplotlib figure and canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # Add the canvas to the layout
        layout.addWidget(self.canvas)

        # Add a slider for frequency control
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(1, 2000)  # Frequency range in Hz
        self.freq_slider.setValue(1000)  # Default value
        self.freq_slider.setSingleStep(1)
        self.freq_slider.valueChanged.connect(self.update_plot)
        layout.addWidget(self.freq_slider)

        # Add a label to show the current frequency
        self.freq_label = QLabel("Frequency: 5 Hz")
        layout.addWidget(self.freq_label)

        # Add a slider for amplitude control
        self.amp_slider = QSlider(Qt.Horizontal)
        self.amp_slider.setRange(1, 1000)  # Amplitude range (scaled for slider granularity)
        self.amp_slider.setValue(500)  # Default value
        self.amp_slider.setSingleStep(1)
        self.amp_slider.valueChanged.connect(self.update_plot)
        layout.addWidget(self.amp_slider)

        # Add a label to show the current amplitude
        self.amp_label = QLabel("Amplitude: 0.5")
        layout.addWidget(self.amp_label)

        # Initial frequency and amplitude
        self.frequency = 5
        self.amplitude = 0.5

        # Fix the extents
        self.fixed_ylim = (-1.0, 1.0)

        self.plot_sine_wave()

    def plot_sine_wave(self):
        self.ax.clear()
        x = np.linspace(0, 2 * np.pi, 500)
        y = self.amplitude * np.sin(self.frequency * x)
        self.ax.plot(x, y, label=f"Sine Wave ({self.frequency} Hz, Amplitude {self.amplitude:.1f})")
        self.ax.legend()
        self.ax.set_title("Sine Wave")
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_ylim(self.fixed_ylim)  # Fix the y-axis limits
        self.canvas.draw()

    def update_plot(self):
        self.frequency = self.freq_slider.value()
        self.amplitude = self.amp_slider.value() / 10.0  # Scale amplitude back to range [0.1, 1.0]
        self.freq_label.setText(f"Frequency: {self.frequency} Hz")
        self.amp_label.setText(f"Amplitude: {self.amplitude:.1f}")
        self.plot_sine_wave()

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
