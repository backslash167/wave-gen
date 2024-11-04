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

    # Generate time values for the waveform period, scaled by the frequency
    t = np.arange(frames) / sample_rate
    t_scaled = (t * frequency) % 1  # Repeat the waveform every period

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
freq_frame.pack(side="left", padx=10)  # Adds padding between sliders

# Frequency label at the top
freq_label = tk.Label(freq_frame, text="Frequency (Hz)")
freq_label.pack()

# Frequency slider
freq_slider = tk.Scale(
    freq_frame, from_=20, to=2000, orient='horizontal', command=update_frequency
)
freq_slider.set(frequency)
freq_slider.pack()

# Frequency value label below the slider, updated dynamically
freq_value_label = tk.Label(freq_frame, text=str(frequency))
freq_value_label.pack()

# Volume slider frame
vol_frame = tk.Frame(slider_frame)
vol_frame.pack(side="left", padx=10)  # Adds padding between sliders

# Volume label at the top
vol_label = tk.Label(vol_frame, text="Volume")
vol_label.pack()

# Volume slider
vol_slider = tk.Scale(
    vol_frame, from_=0, to=1, resolution=0.01, orient='horizontal', command=update_volume
)
vol_slider.set(volume)
vol_slider.pack()

# Volume value label below the slider, updated dynamically
vol_value_label = tk.Label(vol_frame, text=str(volume))
vol_value_label.pack()

# Matplotlib figure and canvas for interactive waveform editing
fig, ax = plt.subplots(figsize=(6, 3))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Plot initial waveform and set axis limits
line, = ax.plot(*zip(*waveform_vertices), 'bo-')  # plot vertices as blue circles connected by lines
ax.set_xlim(0, 1)
ax.set_ylim(-1.5, 1.5)
ax.set_title("Edit the Waveform by Adding, Moving, and Deleting Points")

# Vertex interaction management
selected_vertex = None
vertex_radius = 0.08  # Increased distance threshold to detect nearby vertices


# Function to update the plot after modifying vertices
def update_plot():
    x_points, y_points = zip(*waveform_vertices)
    line.set_data(x_points, y_points)
    fig.canvas.draw()


# Mouse click event to add points anywhere on the graph or move existing ones
def on_click(event):
    global selected_vertex
    if event.inaxes != ax or event.button != 1:  # Only respond to left-clicks
        return

    # Detect if Ctrl key is held for forced point addition
    ctrl_held = event.key == 'control' if event.key is not None else False

    # Add a new vertex if Ctrl is held, regardless of proximity
    if ctrl_held:
        waveform_vertices.append((event.xdata, event.ydata))
        waveform_vertices.sort()  # Keep vertices ordered by x
        logging.info(f"Ctrl+Click: Added vertex at ({event.xdata:.2f}, {event.ydata:.2f})")
        update_plot()
        return

    # Check if click is near an existing vertex to move
    for i, (x, y) in enumerate(waveform_vertices):
        if abs(x - event.xdata) < vertex_radius and abs(y - event.ydata) < vertex_radius:
            selected_vertex = i  # Select this vertex for moving
            logging.info(f"Selected vertex at ({x:.2f}, {y:.2f}) for moving")
            return

    # Add new vertex at the click location if not near any vertex
    waveform_vertices.append((event.xdata, event.ydata))
    waveform_vertices.sort()  # Keep vertices ordered by x
    selected_vertex = waveform_vertices.index((event.xdata, event.ydata))  # Track the new vertex
    logging.info(f"Added vertex at ({event.xdata:.2f}, {event.ydata:.2f})")
    update_plot()


# Mouse release event to release the selected vertex
def on_release(event):
    global selected_vertex
    selected_vertex = None  # Deselect the vertex after releasing


# Mouse motion event to move a selected vertex
def on_motion(event):
    global selected_vertex
    if selected_vertex is None or event.inaxes != ax:
        return

    # Prevent horizontal movement for the first and last vertices
    if selected_vertex == 0 or selected_vertex == len(waveform_vertices) - 1:
        new_y = event.ydata
        waveform_vertices[0] = (0, new_y)
        waveform_vertices[-1] = (1, new_y)  # Keep the last point at the same y-coordinate
        logging.info(f"Moved first and last vertices to y={new_y:.2f}")
    else:
        # Allow free movement for other vertices
        old_x, old_y = waveform_vertices[selected_vertex]
        new_x, new_y = event.xdata, event.ydata
        waveform_vertices[selected_vertex] = (new_x, new_y)
        logging.info(f"Moved vertex from ({old_x:.2f}, {old_y:.2f}) to ({new_x:.2f}, {new_y:.2f})")

    update_plot()


# Right-click event to remove a vertex
def on_right_click(event):
    global waveform_vertices
    if event.inaxes != ax or event.button != 3:  # Only respond to right-clicks
        return

    # Prevent deletion of the first and last vertices
    for i, (x, y) in enumerate(waveform_vertices):
        if i == 0 or i == len(waveform_vertices) - 1:
            continue  # Skip deletion for the first and last vertices

        if abs(x - event.xdata) < vertex_radius and abs(y - event.ydata) < vertex_radius:
            logging.info(f"Removed vertex at ({x:.2f}, {y:.2f})")
            del waveform_vertices[i]
            update_plot()
            break


# Connect Matplotlib events for adding, moving, and removing vertices
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('button_release_event', on_release)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('button_press_event', on_right_click)

# Start the audio stream
stream = sd.OutputStream(callback=audio_callback, samplerate=sample_rate, channels=1)
stream.start()

# Run the Tkinter main loop
root.mainloop()
