import numpy as np
import sounddevice as sd
import tkinter as tk

# Global variables to store frequency, volume, and waveform type
frequency = 440  # Default frequency
volume = 0.5     # Default volume
waveform_type = "sine"  # Default waveform type
sample_rate = 44100


# Waveform generator functions
def sine_wave(t, frequency):
    return np.sin(2 * np.pi * frequency * t)


def square_wave(t, frequency):
    return np.sign(np.sin(2 * np.pi * frequency * t))


def triangle_wave(t, frequency):
    return 2 * np.abs(2 * ((frequency * t) % 1) - 1) - 1


# Function to select the appropriate waveform function based on waveform type
def get_waveform_function(waveform_type):
    if waveform_type == "sine":
        return sine_wave
    elif waveform_type == "square":
        return square_wave
    elif waveform_type == "triangle":
        return triangle_wave
    else:
        raise ValueError("Unsupported waveform type")


# Audio callback function
def audio_callback(outdata, frames, time, status):
    global frequency, volume, waveform_type

    # Generate time values for the audio buffer
    t = (np.arange(frames) + audio_callback.current_frame) / sample_rate

    # Get the waveform function based on the selected type
    waveform_function = get_waveform_function(waveform_type)

    # Generate the waveform using the selected function
    wave = waveform_function(t, frequency)

    # Apply volume and output the waveform
    outdata[:, 0] = (wave * volume).astype(np.float32)
    audio_callback.current_frame += frames


# Initialize the frame counter for the callback function
audio_callback.current_frame = 0


# Function to update the frequency based on the slider value
def update_frequency(val):
    global frequency
    frequency = float(val)


# Function to update the volume based on the slider value
def update_volume(val):
    global volume
    volume = float(val)


# Function to update the waveform type based on the dropdown selection
def update_waveform(selection):
    global waveform_type
    waveform_type = selection


# Create GUI with Tkinter
root = tk.Tk()
root.title("Real-time Wave Generator")

# Frequency slider
freq_slider = tk.Scale(root, from_=20, to=2000, orient='horizontal', label="Frequency (Hz)", command=update_frequency)
freq_slider.set(frequency)  # Set default frequency
freq_slider.pack()

# Volume slider
vol_slider = tk.Scale(root, from_=0, to=1, resolution=0.01, orient='horizontal', label="Volume", command=update_volume)
vol_slider.set(volume)  # Set default volume
vol_slider.pack()

# Waveform selection dropdown
waveform_options = ["sine", "square", "triangle"]
waveform_var = tk.StringVar(root)
waveform_var.set(waveform_type)  # Set default waveform type
waveform_dropdown = tk.OptionMenu(root, waveform_var, *waveform_options, command=update_waveform)
waveform_dropdown.config(width=10)
waveform_dropdown.pack()
waveform_label = tk.Label(root, text="Select Waveform")
waveform_label.pack()

# Start the audio stream with the callback function
stream = sd.OutputStream(callback=audio_callback, samplerate=sample_rate, channels=1)
stream.start()

# Run the GUI loop
root.mainloop()

# Stop the audio stream when GUI is closed
stream.stop()
stream.close()
