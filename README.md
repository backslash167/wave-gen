# Interactive Waveform Editor

This project is an interactive audio waveform editor built using Python, Tkinter, Matplotlib, and Sounddevice. The editor allows users to design custom audio waveforms by adding, moving, and deleting points on a graph, with real-time audio playback of the waveform they create. Users can modify the waveform's frequency and volume through intuitive sliders, with the effect applied in real-time.

## Features

- **Interactive Waveform Design**: Add, move, and delete points on a graph to shape the waveform.
- **Real-Time Audio Playback**: Hear the waveform as you design it, with immediate feedback on changes.
- **Frequency and Volume Control**: Adjust the playback frequency and volume using sliders.
- **PEP-8 Compliant**: The code is written following PEP-8 standards for readability and maintainability.
- **Dynamic Updates**: The waveform is updated dynamically as you modify the vertices on the graph.

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - numpy
  - sounddevice
  - tkinter (usually included with Python installations)
  - matplotlib
  - scipy

You can install the necessary packages using pip:

pip install numpy sounddevice matplotlib scipy

## Usage

1. Clone or download the project files to your local machine.
2. Run the script by navigating to the project directory and executing:

python interactive_waveform_editor.py

### How to Use the Interface

1. **Frequency and Volume Sliders**:
   - Adjust the frequency slider to control the playback frequency of the waveform.
   - Adjust the volume slider to control the playback volume.
   - Both sliders have labels above to indicate their function, and a label below showing the current value.

2. **Waveform Graph**:
   - Left-click anywhere on the graph to add a new point.
   - Left-click and drag a point to move it. The first and last points can only move vertically to maintain waveform continuity.
   - Right-click on a point to delete it (except for the first and last points, which cannot be deleted).
   - Ctrl + Click to add a point exactly at the clicked location, even if it is close to another point.

3. **Audio Output**:
   - The audio plays continuously, reflecting any updates you make to the waveform.
   - Changes in the waveform, frequency, or volume take effect immediately.

4. **Closing the Application**:
   - To exit, simply close the window. The program will automatically stop the audio stream and exit.

## Project Structure

- interactive_waveform_editor.py: The main script that creates the interactive waveform editor with real-time audio playback.

## Code Overview

### Main Components

- **Waveform Generation (generate_custom_waveform)**:
  - Interpolates the points added to the graph to create a continuous waveform.
  - Supports both linear and cubic interpolation, depending on the number of points.

- **Audio Callback (audio_callback)**:
  - Generates the audio output based on the current waveform, frequency, and volume.
  - Utilizes Sounddevice’s real-time audio output functionality.

- **Tkinter GUI**:
  - The GUI is built using Tkinter and includes sliders for frequency and volume as well as a Matplotlib plot for waveform editing.
  - Dynamic labels show the current frequency and volume values.

### Design Considerations

- **Real-Time Feedback**:
  - Audio playback and waveform updates are designed to respond immediately to user input.
  
- **User Interface Layout**:
  - Sliders are organized side-by-side with labels centered, providing a clean, intuitive control panel for waveform design.

## Troubleshooting

- **No Audio Output**:
  - Make sure your sound device is configured correctly, and check that other applications can produce sound.
  - Ensure that the sounddevice library is correctly installed.

- **High CPU Usage**:
  - Real-time audio synthesis can be CPU-intensive, especially with frequent waveform updates. Try reducing the complexity of the waveform by minimizing the number of points.

## License

This project is open-source and available under the MIT License.
