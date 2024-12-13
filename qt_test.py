from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

import numpy as np
import sys
import threading
import time

import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt



class BlitManager:
    """
    Manages blitting for Matplotlib figures.
    """
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with. Must support `copy_from_bbox` and `restore_region`.

        animated_artists : Iterable[Artist]
            List of the artists to manage.
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # Grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None and event.canvas != cv:
                print("Canvas mismatch during draw event.")
                return  # Ignore events from a different canvas
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist
            The artist to be added. Will be set to 'animated'.
        """
        if art.figure != self.canvas.figure:
            raise RuntimeError("Artist must be in the same figure as the canvas.")
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # print("Updating plot with blitting...")
        # Paranoia in case we missed the draw event
        if self._bg is None:
            self.on_draw(None)
        else:
            # Restore the background
            cv.restore_region(self._bg)
            # Draw all the animated artists
            self._draw_animated()
            # Update the GUI state
            cv.blit(fig.bbox)
        # Let the GUI event loop process anything it has to do
        cv.flush_events()


class SineWavePlot:
    def __init__(self):
        self.figure, self.ax = plt.subplots()
        self.fixed_ylim = (-1.0, 1.0)  # Fix the y-axis limits

        # Create an animated line for the sine wave
        x = np.linspace(0, 2 * np.pi, 500)
        y = 0.5 * np.sin(5 * x)
        self.line, = self.ax.plot(x, y, label="Sine Wave", animated=True)
        self.ax.set_xlim(0, 2 * np.pi)  # Set static x-limits
        self.ax.set_ylim(self.fixed_ylim)  # Set static y-limits
        self.ax.legend(loc="upper right")  # Fix legend position

        # Create the blit manager
        self.bm = BlitManager(self.figure.canvas, [self.line])
        # Cache the background
        self.figure.canvas.draw()
        self.bm.on_draw(None)

        # Initialize plot frame count and start time
        self.plot_frame_count = 0
        self.start_time = time.time()

        print(f"Line added to Axes: {self.line in self.ax.lines}")

    def get_canvas(self):
        """
        Returns the Matplotlib canvas to embed in the UI.
        """
        return FigureCanvas(self.figure)

    def plot(self, frequency, amplitude):
        """
        Updates the sine wave data and redraws it using the BlitManager.
        """
        # print(f"Updating plot: Frequency={frequency}, Amplitude={amplitude}")
        # Update sine wave data
        x = np.linspace(0, 2 * np.pi, 500)
        y = amplitude * np.sin(frequency * x)
        self.line.set_data(x, y)

        print(f"Updating plot: Frequency={frequency}, Amplitude={amplitude}")
        print(f"x: {x[:5]} ... {x[-5:]}")
        print(f"y: {y[:5]} ... {y[-5:]}")
        print(f"y min: {np.min(y)}, y max: {np.max(y)}")

        self.line.set_data(x, y)
        self.figure.canvas.draw_idle()  # Force full redraw

        # Update the plot using the blit manager
        # self.bm.update()

        self.plot_frame_count += 1

        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            return self.plot_frame_count / elapsed_time
        return 0


class WorkerSignals(QObject):
    """
    Signals for thread-to-main communication.
    """
    update = pyqtSignal(float, float, float)  # frequency, amplitude, math_rate


class SineWaveThread(threading.Thread):
    """
    Background thread to simulate real-time waveform computation.
    """
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.running = True
        self.frequency = 1000
        self.amplitude = 0.5
        self.math_frame_count = 0
        self.start_time = time.time()

    def run(self):
        while self.running:
            # Simulate computation
            self.math_frame_count += 1
            elapsed_time = time.time() - self.start_time
            math_rate = self.math_frame_count / elapsed_time if elapsed_time > 0 else 0

            time.sleep(0.05)  # ~20 Hz updates
            self.signals.update.emit(self.frequency, self.amplitude, math_rate)

    def set_frequency(self, frequency):
        self.frequency = frequency

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    """
    The main application window.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 with Threaded Updates")

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Initialize components
        self.sine_wave_plot = SineWavePlot()
        self.control_panel = ControlPanel(
            layout,
            on_frequency_change=self.update_frequency,
            on_amplitude_change=self.update_amplitude
        )

        # Add Matplotlib canvas
        layout.addWidget(self.sine_wave_plot.get_canvas())

        # Add update rate labels
        self.math_rate_label = QLabel("Math Update Rate: 0.0 Hz")
        layout.addWidget(self.math_rate_label)
        self.plot_rate_label = QLabel("Plot Update Rate: 0.0 Hz")
        layout.addWidget(self.plot_rate_label)

        # Start background thread with signals
        self.signals = WorkerSignals()
        self.signals.update.connect(self.update_plot_from_thread)
        self.sine_wave_thread = SineWaveThread(self.signals)
        self.sine_wave_thread.start()

        # Add QTimer for additional periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.trigger_plot_update)
        self.update_timer.start(50)  # Update every 50 ms (~20 Hz)

    def trigger_plot_update(self):
        """
        Periodically update the plot (optional debugging or backup mechanism).
        """
        frequency = self.control_panel.get_frequency()
        amplitude = self.control_panel.get_amplitude()
        self.sine_wave_plot.plot(frequency, amplitude)

    def update_frequency(self):
        """
        Update the frequency in the thread.
        """
        frequency = self.control_panel.get_frequency()
        self.sine_wave_thread.set_frequency(frequency)

    def update_amplitude(self):
        """
        Update the amplitude in the thread.
        """
        amplitude = self.control_panel.get_amplitude()
        self.sine_wave_thread.set_amplitude(amplitude)

    def update_plot_from_thread(self, frequency, amplitude, math_rate):
        """
        Update the sine wave plot and math update rate from the background thread.
        """
        # print(f"Thread Update: Frequency={frequency}, Amplitude={amplitude}, Math Rate={math_rate}")
        plot_rate = self.sine_wave_plot.plot(frequency, amplitude)
        self.math_rate_label.setText(f"Math Update Rate: {math_rate:.2f} Hz")
        self.plot_rate_label.setText(f"Plot Update Rate: {plot_rate:.2f} Hz")

    def closeEvent(self, event):
        """
        Ensure the thread stops when the window is closed.
        """
        self.sine_wave_thread.stop()
        self.sine_wave_thread.join()
        super().closeEvent(event)


class ControlPanel:
    """
    Manages the sliders and labels for controlling frequency and amplitude.
    """
    def __init__(self, layout, on_frequency_change, on_amplitude_change):
        # Frequency Slider
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(1, 2000)  # Frequency range in Hz
        self.freq_slider.setValue(1000)  # Default value
        self.freq_slider.setSingleStep(1)
        self.freq_slider.valueChanged.connect(on_frequency_change)
        layout.addWidget(self.freq_slider)

        self.freq_label = QLabel("Frequency: 1000 Hz")
        layout.addWidget(self.freq_label)

        # Amplitude Slider
        self.amp_slider = QSlider(Qt.Horizontal)
        self.amp_slider.setRange(1, 1000)  # Amplitude range (scaled for slider granularity)
        self.amp_slider.setValue(500)  # Default value
        self.amp_slider.setSingleStep(1)
        self.amp_slider.valueChanged.connect(on_amplitude_change)
        layout.addWidget(self.amp_slider)

        self.amp_label = QLabel("Amplitude: 0.5")
        layout.addWidget(self.amp_label)

    def update_frequency_label(self, frequency):
        self.freq_label.setText(f"Frequency: {frequency} Hz")

    def update_amplitude_label(self, amplitude):
        self.amp_label.setText(f"Amplitude: {amplitude:.1f}")

    def get_frequency(self):
        return self.freq_slider.value()

    def get_amplitude(self):
        return self.amp_slider.value() / 10.0  # Scale back to range [0.1, 1.0]


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
