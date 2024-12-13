import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import utils

# --- Configurable Parameters ---
BLOCK_SIZE = 2048                # Size of audio buffer (FFT size)
SPECTROGRAM_FRAMES = 100         # Number of time frames in spectrogram
DEFAULT_FS = 44100               # Default sampling rate (can be overwritten by device info)
INTERVAL_MS = 5                  # Update interval in milliseconds
VMIN_DB = -90                    # Minimum dB value for spectrogram visualization
VMAX_DB = -30                      # Maximum dB value for spectrogram visualization
WAVEFORM_YMIN = -1               # Minimum amplitude for waveform plot
WAVEFORM_YMAX = 1                # Maximum amplitude for waveform plot
FREQ_MIN = 0                     # Minimum frequency for spectrogram (Hz)
FREQ_MAX = 44100//2              # Maximum frequency for spectrogram (Hz)
COLOR_MAP = "jet"              # Colormap for spectrogram
AXIS_FONT_SIZE = 12              # Font size for axis labels
TITLE_FONT_SIZE = 14             # Font size for titles
FIG_SIZE = (10, 8)               # Figure size for plots
AMPLITUDE_TO_DB_SCALE = 20       # Scale factor for converting amplitude to decibels

# Additional Parameters
AUDIO_BUFFER_CHANNEL_INDEX = 0   # Index of the audio channel to use
SMALL_VALUE = 1e-10              # Small value to prevent log(0)
PLOT_ROWS = 2                    # Number of rows in subplot grid
PLOT_COLUMNS = 1                 # Number of columns in subplot grid
WAVEFORM_XMIN = 0                # Minimum x value for waveform plot
WAVEFORM_TITLE = "Live Audio Stream - Waveform"
WAVEFORM_XLABEL = "Samples"
WAVEFORM_YLABEL = "Amplitude"
SPECTROGRAM_TITLE = "Live Audio Stream - Spectrogram"
SPECTROGRAM_XLABEL = "Time (frames)"
SPECTROGRAM_YLABEL = "Frequency (Hz)"
TIME_MIN = 0                     # Minimum time for spectrogram
SPECTROGRAM_ORIGIN = 'lower'     # Origin setting for spectrogram plot
SPECTROGRAM_ASPECT = 'auto'      # Aspect ratio for spectrogram plot
AUDIO_STREAM_CHANNELS = 1        # Number of audio channels
AUDIO_STREAM_DTYPE = 'float32'   # Data type for audio stream
AUDIO_STREAM_MESSAGE = "Audio stream started. Press Ctrl+C to stop."
AUDIO_STREAM_STOP_MESSAGE = "Audio stream stopped."
KEYBOARD_INTERRUPT_MESSAGE = "\nStopping the audio stream."
ERROR_MESSAGE = "An error occurred: {}"
STREAM_STATUS_MESSAGE = "Stream status: {}"

def main():
    """Main function to run the live audio stream visualization."""
    # Get the list of audio devices
    device_list = sd.query_devices()
    device_names = [device['name'] for device in device_list]
    device_values = device_list  # Full device information

    # Tkinter-based list selection (assuming tkinter_list is already defined)
    selected_device = utils.tkinter_list(device_names, device_values)

    # Ensure a device was selected
    if selected_device is None:
        print("No device selected. Exiting.")
        return

    # Print the selected device name
    print(f"Selected device: {selected_device['name']}")

    # Use selected device's sample rate
    fs = int(selected_device.get("default_samplerate", DEFAULT_FS))

    # --- Frequency Bin Calculations ---
    freq_bins = np.fft.rfftfreq(BLOCK_SIZE, d=1.0 / fs)
    # Find indices corresponding to FREQ_MIN and FREQ_MAX
    freq_indices = np.where((freq_bins >= FREQ_MIN) & (freq_bins <= FREQ_MAX))[0]
    # Update freq_bins to include only the desired frequencies
    freq_bins = freq_bins[freq_indices]
    freq_max = freq_bins[-1]  # Update freq_max based on actual data

    # Initialize audio buffer and spectrogram data
    audio_buffer = np.zeros(BLOCK_SIZE, dtype=AUDIO_STREAM_DTYPE)
    spectrogram_data = np.zeros((len(freq_indices), SPECTROGRAM_FRAMES))

    # --- Audio Callback ---
    def audio_callback(indata, frames, time, status):
        """Callback function for the audio input stream."""
        if status:
            print(STREAM_STATUS_MESSAGE.format(status))  # Print stream errors/warnings
        audio_buffer[:] = indata[:, AUDIO_BUFFER_CHANNEL_INDEX]  # Update audio buffer with specified channel data

        # Compute FFT for the spectrogram
        spectrum = np.abs(np.fft.rfft(audio_buffer, n=BLOCK_SIZE)) / BLOCK_SIZE
        spectrum = spectrum[freq_indices]  # Select frequencies within the desired range
        decibel_spectrum = AMPLITUDE_TO_DB_SCALE * np.log10(spectrum + SMALL_VALUE)
        spectrogram_data[:, :-1] = spectrogram_data[:, 1:]  # Shift data for scrolling effect
        spectrogram_data[:, -1] = np.clip(decibel_spectrum, VMIN_DB, VMAX_DB)  # Update the latest column

    # --- Plotting Functions ---
    def update_waveform(frame):
        """Update function for the waveform plot."""
        waveform_line.set_ydata(audio_buffer)  # Update the y-data of the line
        return waveform_line,

    def update_spectrogram(frame):
        """Update function for the spectrogram plot."""
        spectrogram_image.set_array(spectrogram_data)
        return spectrogram_image,

    # --- Visualization Setup ---
    fig, (ax_waveform, ax_spectrogram) = plt.subplots(PLOT_ROWS, PLOT_COLUMNS, figsize=FIG_SIZE)

    # Waveform plot
    waveform_line, = ax_waveform.plot(audio_buffer)
    ax_waveform.set_ylim(WAVEFORM_YMIN, WAVEFORM_YMAX)  # Amplitude range
    ax_waveform.set_xlim(WAVEFORM_XMIN, len(audio_buffer))  # Match the x-axis to the buffer length
    ax_waveform.set_title(WAVEFORM_TITLE, fontsize=TITLE_FONT_SIZE)
    ax_waveform.set_xlabel(WAVEFORM_XLABEL, fontsize=AXIS_FONT_SIZE)
    ax_waveform.set_ylabel(WAVEFORM_YLABEL, fontsize=AXIS_FONT_SIZE)

    # Spectrogram plot
    extent = [TIME_MIN, SPECTROGRAM_FRAMES, FREQ_MIN, freq_max]
    spectrogram_image = ax_spectrogram.imshow(
        spectrogram_data,
        aspect=SPECTROGRAM_ASPECT,
        origin=SPECTROGRAM_ORIGIN,
        extent=extent,
        cmap=COLOR_MAP,
        vmin=VMIN_DB,
        vmax=VMAX_DB
    )
    ax_spectrogram.set_title(SPECTROGRAM_TITLE, fontsize=TITLE_FONT_SIZE)
    ax_spectrogram.set_xlabel(SPECTROGRAM_XLABEL, fontsize=AXIS_FONT_SIZE)
    ax_spectrogram.set_ylabel(SPECTROGRAM_YLABEL, fontsize=AXIS_FONT_SIZE)

    # --- Audio Stream Configuration ---
    try:
        with sd.InputStream(
            device=selected_device['index'],
            channels=AUDIO_STREAM_CHANNELS,
            samplerate=fs,
            callback=audio_callback,
            blocksize=BLOCK_SIZE,
            dtype=AUDIO_STREAM_DTYPE
        ):
            # Start the stream
            print(AUDIO_STREAM_MESSAGE)

            # Use FuncAnimation for live updating both plots
            ani_waveform = FuncAnimation(
                fig, update_waveform, interval=INTERVAL_MS, blit=True
            )
            ani_spectrogram = FuncAnimation(
                fig, update_spectrogram, interval=INTERVAL_MS, blit=True
            )

            plt.tight_layout()
            plt.show()

            print(AUDIO_STREAM_STOP_MESSAGE)

    except KeyboardInterrupt:
        # Gracefully handle exit on Ctrl+C
        print(KEYBOARD_INTERRUPT_MESSAGE)

    except Exception as e:
        # Handle errors
        print(ERROR_MESSAGE.format(e))


if __name__ == "__main__":
    main()
