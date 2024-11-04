import numpy as np
import sounddevice as sd
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables to store frequency, volume, and sample rate
frequency = 440
volume = 0.5
sample_rate = 44100
waveform_vertices = [(0, 0), (0.5, 1), (1, 0)]  # Initial sine-like waveform vertices

minimum_delta = 0.0001
num_points = 10

# Function to set waveform based on preset selection
def set_preset_waveform(waveform_type):
    global waveform_vertices
    if waveform_type == 'sine':
        # Generate `num_points` vertices for a smooth sine wave
        x_points = np.linspace(0, 1, num_points)  # Generate `num_points` evenly spaced x values from 0 to 1
        y_points = np.sin(2 * np.pi * x_points)   # Calculate corresponding y values for a sine wave
        waveform_vertices = list(zip(x_points, y_points))
    elif waveform_type == 'triangle':
        waveform_vertices = [(0, 0), (1/3, 1), (2/3, -1), (1, 0)]
    elif waveform_type == 'square':
        waveform_vertices = [(0, 1), (1/2, 1), ((1/2+minimum_delta), -1), ((1-minimum_delta), -1), (1, 1)]
    elif waveform_type == 'sawtooth':
        # Sawtooth wave vertices, ramping linearly from -1 to 1 over the period
        waveform_vertices = [(0, -1), (1-minimum_delta, 1), (1, -1)]

    logging.info(f"Set waveform to {waveform_type} preset.")
    update_plot()


# Function to generate waveform from vertices using interpolation
def generate_custom_waveform(frames):
    x_points, y_points = zip(*waveform_vertices)

    # Remove duplicates by creating a dictionary (keeps last occurrence of each x value)
    unique_points = dict(zip(x_points, y_points))
    x_points, y_points = zip(*sorted(unique_points.items()))  # Sort to maintain order

    # Ensure x_points covers exactly one period, from 0 to 1
    if x_points[0] != 0 or x_points[-1] != 1:
        raise ValueError("The x-axis should start at 0 and end at 1 for proper looping.")

    # Choose interpolation type based on the number of unique vertices
    if len(x_points) >= 4:
        interpolator = interp1d(x_points, y_points, kind="cubic", fill_value="extrapolate")
    else:
        interpolator = interp1d(x_points, y_points, kind="linear", fill_value="extrapolate")

    # Generate time values for the waveform period, using frequency to set the period implicitly
    t = np.arange(frames) / sample_rate
    t_scaled = (t * frequency) % 1  # Frequency now controls the repetition rate directly

    # Generate waveform from interpolated function
    waveform = interpolator(t_scaled)
    return waveform


# Audio callback function
def audio_callback(outdata, frames, time, status):
    global volume
    waveform = generate_custom_waveform(frames)
    outdata[:, 0] = (waveform * volume).astype(np.float32)


# Initialize the frame counter for the callback function
audio_callback.current_frame = 0

# Create the Tkinter window and layout
root = tk.Tk()
root.title("Interactive Waveform Editor")


# Function to properly close the application
def on_close():
    logging.info("Closing the application...")
    stream.stop()
    stream.close()
    root.quit()
    root.destroy()


# Bind the window close event to the on_close function
root.protocol("WM_DELETE_WINDOW", on_close)


# Function to update frequency and update the frequency label
def update_frequency(val):
    global frequency
    frequency = float(val)
    freq_value_label.config(text=str(frequency))  # Update the frequency value label
    logging.info(f"Frequency changed to {frequency} Hz")


# Function to update volume and update the volume label
def update_volume(val):
    global volume
    volume = float(val)
    vol_value_label.config(text=str(volume))  # Update the volume value label
    logging.info(f"Volume changed to {volume}")


# Create a frame to hold the sliders side by side
slider_frame = tk.Frame(root)
slider_frame.pack()

# Frequency slider frame
freq_frame = tk.Frame(slider_frame)
freq_frame.pack(side="left", padx=10)

# Frequency label at the top
freq_label = tk.Label(freq_frame, text="Frequency (Hz)")
freq_label.pack()

# Frequency slider
freq_slider = tk.Scale(
    freq_frame, from_=20, to=2000, orient='horizontal', command=update_frequency
)
freq_slider.set(frequency)
freq_slider.pack()

# Frequency value label below the slider
freq_value_label = tk.Label(freq_frame, text=str(frequency))
freq_value_label.pack()

# Volume slider frame
vol_frame = tk.Frame(slider_frame)
vol_frame.pack(side="left", padx=10)

# Volume label at the top
vol_label = tk.Label(vol_frame, text="Volume")
vol_label.pack()

# Volume slider
vol_slider = tk.Scale(
    vol_frame, from_=0, to=1, resolution=0.01, orient='horizontal', command=update_volume
)
vol_slider.set(volume)
vol_slider.pack()

# Volume value label below the slider
vol_value_label = tk.Label(vol_frame, text=str(volume))
vol_value_label.pack()

# Dropdown menu for waveform presets
preset_frame = tk.Frame(root)
preset_frame.pack(pady=10)
preset_label = tk.Label(preset_frame, text="Waveform Preset")
preset_label.pack(side="left")

waveform_var = tk.StringVar(root)
waveform_var.set("sine")  # Default to sine waveform

dropdown_list = ["sine", "triangle", "square", "sawtooth", "custom"]

# Dropdown menu with waveform options
preset_dropdown = tk.OptionMenu(
    preset_frame, waveform_var, dropdown_list[0], *dropdown_list[1:], command=set_preset_waveform
)
preset_dropdown.pack(side="left")


# Matplotlib figure and canvas for interactive waveform editing
fig, ax = plt.subplots(figsize=(6, 3))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Plot initial waveform and set axis limits
line, = ax.plot(*zip(*waveform_vertices), 'bo-')  # plot vertices as blue circles connected by lines
ax.set_xlim(0, 1)
ax.set_ylim(-1.5, 1.5)
ax.set_title("Edit the Waveform by Adding, Moving, and Deleting Points")

# Function to update the plot after modifying vertices
def update_plot():
    x_points, y_points = zip(*waveform_vertices)
    line.set_data(x_points, y_points)
    fig.canvas.draw()

# Rest of the vertex editing functions remain unchanged (on_click, on_motion, etc.)

# Start the audio stream
stream = sd.OutputStream(callback=audio_callback, samplerate=sample_rate, channels=1)
stream.start()

# Run the Tkinter main loop
root.mainloop()
