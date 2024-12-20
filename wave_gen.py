import numpy as np
import sounddevice as sd
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, make_interp_spline
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables to store frequency, volume, and sample rate
frequency = 440
volume = 0.5
sample_rate = 44100
waveform_vertices = [(0, 0), (0.5, 1), (1, 0)]  # Initial sine-like waveform vertices
output_buffer = np.zeros(1024)  # Buffer for visualization

minimum_delta = 0.0001
num_points = 10
interpolation_type = "cubic"  # Default interpolation type


# Function to set waveform based on preset selection
def set_preset_waveform(waveform_type):
    '''
    :param waveform_type:
    :return:
    '''
    global waveform_vertices
    if waveform_type == 'sine':
        # Generate `num_points` vertices for a smooth sine wave
        x_points = np.linspace(0, 1, num_points)
        y_points = np.sin(2 * np.pi * x_points)
        waveform_vertices = list(zip(x_points, y_points))

    elif waveform_type == 'triangle':
        waveform_vertices = [(0, 0), (1 / 3, 1), (2 / 3, -1), (1, 0)]

    elif waveform_type == 'square':
        waveform_vertices = [(0, 1), (1 / 2, 1), ((1 / 2 + minimum_delta), -1), ((1 - minimum_delta), -1), (1, 1)]

    elif waveform_type == 'sawtooth':
        waveform_vertices = [(0, -1), (1 - minimum_delta, 1), (1, -1)]

    logging.info(f"Set waveform to {waveform_type} preset.")
    update_plot()  # Refresh the plot with the new vertices

current_phase = 0.0  # Tracks the current phase across callbacks

# Function to generate waveform from vertices using interpolation
def generate_custom_waveform(frames):
    global current_phase
    phase_increment = frequency / sample_rate

    x_points, y_points = zip(*waveform_vertices)

    # Remove duplicates by creating a dictionary (keeps last occurrence of each x value)
    unique_points = dict(zip(x_points, y_points))
    x_points, y_points = zip(*sorted(unique_points.items()))

    y_points = list(y_points)
    y_points[-1] = y_points[0]  # Ensure continuity by matching endpoints

    # Choose interpolation type based on the number of unique vertices
    try:
        if interpolation_type == "smooth":
            interpolator = make_interp_spline(x_points, y_points, k=min(3, len(x_points)-1))
        elif len(x_points) <=4:
            interpolator = interp1d(x_points, y_points, kind="linear", fill_value="extrapolate")
        else:
            interpolator = interp1d(x_points, y_points, kind=interpolation_type, fill_value="extrapolate")
    except ValueError as e:
        logging.error(f"Interpolation failed: {e}. Falling back to linear interpolation.")
        interpolator = interp1d(x_points, y_points, kind="linear", fill_value="extrapolate")

    # Generate time values for the current phase, ensuring continuity
    t = (np.arange(frames) * phase_increment + current_phase) % 1
    waveform = interpolator(t)
    waveform = np.clip(waveform, -1, 1)

    # Update the current phase to where this buffer ends
    current_phase = (current_phase + frames * phase_increment) % 1

    return waveform

# Function to plot output buffer for visualization
def plot_output_buffer():
    ax_output.clear()
    ax_output.plot(output_buffer, 'r-')
    ax_output.set_title("Output Buffer Waveform")
    ax_output.set_ylim(-1.0, 1.0)
    canvas_output.draw()


# Audio callback function
def audio_callback(outdata, frames, time, status):
    global volume, output_buffer
    waveform = generate_custom_waveform(frames)
    outdata[:, 0] = (waveform * volume).astype(np.float32) # left
    outdata[:, 1] = (waveform * 0).astype(np.float32) # right

    # Update output buffer for visualization and plot it
    output_buffer = waveform * volume  # Copy the waveform into the buffer
    plot_output_buffer()  # Update plot in real-time

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


# Function to update interpolation type
def update_interpolation_type(val):
    global interpolation_type
    interpolation_type = val
    logging.info(f"Interpolation type changed to {interpolation_type}")
    update_plot()


# Dropdown menu for interpolation type
interp_frame = tk.Frame(root)
interp_frame.pack(pady=10)
interp_label = tk.Label(interp_frame, text="Interpolation Type")
interp_label.pack(side="left")

interp_var = tk.StringVar(root)
interp_var.set("linear")
interp_dropdown_list = ["linear", "cubic", "nearest", "smooth"]

interp_dropdown = tk.OptionMenu(interp_frame, interp_var, *interp_dropdown_list, command=update_interpolation_type)
interp_dropdown.pack(side="left")

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
freq_slider = tk.Scale(freq_frame, from_=20, to=4000, orient='horizontal', command=update_frequency)
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
vol_slider = tk.Scale(vol_frame, from_=0, to=1, resolution=0.01, orient='horizontal', command=update_volume)
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
waveform_var.set("")  # Default to no preset waveform

dropdown_list = ["sine", "triangle", "square", "sawtooth", "custom"]

# Dropdown menu with waveform options
preset_dropdown = tk.OptionMenu(
    preset_frame, waveform_var, "", *dropdown_list, command=set_preset_waveform
)
preset_dropdown.pack(side="left")

# Matplotlib figure and canvas for interactive waveform editing
fig, ax = plt.subplots(figsize=(6, 3))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Plot initial waveform and set axis limits
line, = ax.plot(*zip(*waveform_vertices), 'bo-')  # plot vertices as blue circles connected by lines
ax.set_xlim(0, 1)
ax.set_ylim(-1.0, 1.0)

# Output buffer plot for visualizing waveform
fig_output, ax_output = plt.subplots(figsize=(6, 2))
canvas_output = FigureCanvasTkAgg(fig_output, master=root)
canvas_output.get_tk_widget().pack()

# Function to update the plot after modifying vertices
def update_plot():
    x_points, y_points = zip(*waveform_vertices)
    line.set_data(x_points, y_points)
    fig.canvas.draw()


# Vertex interaction management
selected_vertex = None
vertex_radius = 0.08  # Threshold distance to detect nearby vertices


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


minimum_delta = 0.01  # Define the minimum delta to keep vertices separated

# Mouse motion event to move a selected vertex
def on_motion(event):
    global selected_vertex
    if selected_vertex is None or event.inaxes != ax:
        return

    # Restrict movement for the first and last vertices to y-coordinate only
    if selected_vertex == 0:
        waveform_vertices[0] = (0, event.ydata)
    elif selected_vertex == len(waveform_vertices) - 1:
        waveform_vertices[-1] = (1, event.ydata)
    else:
        # Get the x-coordinates of neighboring vertices
        prev_x = waveform_vertices[selected_vertex - 1][0]
        next_x = waveform_vertices[selected_vertex + 1][0]

        # Constrain x within neighboring vertices with a minimum delta
        new_x = min(max(event.xdata, prev_x + minimum_delta), next_x - minimum_delta)

        # Update the selected vertex position with constrained x and new y
        waveform_vertices[selected_vertex] = (new_x, event.ydata)

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

# Connect Matplotlib events
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('button_release_event', on_release)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('button_press_event', on_right_click)

#stream = sd.OutputStream(callback=audio_callback, samplerate=sample_rate, channels=1)
stream = sd.OutputStream(
    callback=audio_callback,
    samplerate=sample_rate,
    channels=2,
    blocksize=(1024*2),
    latency='low',
    prime_output_buffers_using_stream_callback=True
)
stream.start()

# Run the Tkinter main loop
root.mainloop()
