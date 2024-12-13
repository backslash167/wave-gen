import sounddevice

# noqa
# noinspection ALL


"""
# PyCharm Keyboard Shortcuts (Windows)

Text Selection:      Select Lines:          Shift + ↑ / ↓
Text Selection:      Block Selection:       Alt + Shift + Drag or Alt + Shift + ↑ / ↓
Line Movement:       Move Lines:            Alt + Shift + ↑ / ↓
Line Movement:       Duplicate Line:        Ctrl + D
Multiple Cursors:    Add Cursors (Mouse):   Alt + Click
Multiple Cursors:    Add Cursors (Keyboard):Ctrl + Alt + ↑ / ↓
Column Editing:      Enter Column Mode:     Ctrl + Shift + Insert
Deleting/Cutting:    Delete Lines:          Ctrl + Y
Deleting/Cutting:    Cut Lines:             Ctrl + X
Caret Movement:      Line Start/End:        Ctrl + ← / →
Caret Movement:      Word Start/End:        Ctrl + Shift + ← / →
Caret Movement:      Code Block Start/End:  Ctrl + [ / ]
Selection Expansion: Expand Selection:      Ctrl + W
Selection Expansion: Shrink Selection:      Ctrl + Shift + W
Clipboard:           Paste from History:    Ctrl + Shift + V
Navigation:          Navigate Back/Forward: Ctrl + Alt + ← / →
"""

#  pip install PyQt5 wxPython dearpygui pywebio prompt_toolkit

def tkinter_list(items, values):
    """
    Display a Tkinter list selection window and return the selected value.

    Args:
        items: List of strings to display in the Listbox.
        values: List of corresponding values to return when an item is selected.

    Returns:
        The value corresponding to the selected item, or None if no selection is made.
    """
    import tkinter as tk

    selected_value = None  # Variable to store the selected value

    def on_select():
        nonlocal selected_value
        selected_index = listbox.curselection()
        if selected_index:
            selected_value = values[selected_index[0]]  # Map index to the actual value
        root.destroy()  # Close the window after selection

    root = tk.Tk()
    root.title("Select an Item")

    # Dynamically calculate the width to fit the longest item
    max_length = max(len(item) for item in items)
    listbox_width = max_length + 2

    # Create a Listbox with the calculated width
    listbox = tk.Listbox(root, selectmode=tk.SINGLE, width=listbox_width)
    for item in items:
        listbox.insert(tk.END, item)

    listbox.pack(fill=tk.BOTH, expand=True)

    # Create and pack the button
    button = tk.Button(root, text="Select", command=on_select)
    button.pack()

    root.mainloop()

    return selected_value  # Return the selected value after the window is closed



def wxpython_list(items):
    import wx

    class MyFrame(wx.Frame):
        def __init__(self, items):
            super().__init__(None, title="Select Items", size=(300, 200))
            panel = wx.Panel(self)

            vbox = wx.BoxSizer(wx.VERTICAL)
            self.listbox = wx.ListBox(panel, style=wx.LB_MULTIPLE, choices=items)
            vbox.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 10)

            button = wx.Button(panel, label="Show Selection")
            button.Bind(wx.EVT_BUTTON, self.show_selection)
            vbox.Add(button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

            panel.SetSizer(vbox)

        def show_selection(self, event):
            selected_items = [self.listbox.GetString(i) for i in self.listbox.GetSelections()]
            wx.MessageBox(f"You selected: {', '.join(selected_items)}", "Selection")

    app = wx.App()
    frame = MyFrame(items)
    frame.Show()
    app.MainLoop()


def pyqt5_list(items):
    import sys
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox
    )
    from PyQt5.QtGui import QFont
    from PyQt5.QtCore import Qt

    def show_selection():
        try:
            # Extract the row indices from selectedIndexes()
            selected_items = [list_widget.item(index.row()).text() for index in list_widget.selectedIndexes()]
            if not selected_items:
                QMessageBox.warning(window, "No Selection", "No items selected!")
                return
            QMessageBox.information(window, "Selection", f"You selected: {', '.join(selected_items)}")
        except Exception as e:
            print(f"Error in show_selection: {e}")
            QMessageBox.critical(window, "Error", "An unexpected error occurred.")

    # Initialize QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    # Main window setup
    window = QWidget()
    window.setWindowTitle("Select Items")
    window.setMinimumWidth(400)
    window.setMinimumHeight(300)
    window.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;
            font-family: Arial;
            font-size: 14px;
        }
        QListWidget {
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #4caf50;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b41;
        }
    """)

    # Layout setup
    layout = QVBoxLayout()

    # List widget
    list_widget = QListWidget()
    list_widget.setSelectionMode(QListWidget.MultiSelection)
    list_widget.addItems(items)
    list_widget.setFont(QFont("Arial", 12))
    list_widget.setStyleSheet("""
        QListWidget::item {
            padding: 5px;
        }
        QListWidget::item:selected {
            background-color: #4caf50;
            color: white;
        }
    """)

    # Button widget
    button = QPushButton("Show Selection")
    button.clicked.connect(show_selection)
    button.setFont(QFont("Arial", 12))

    # Add widgets to layout
    layout.addWidget(list_widget)
    layout.addWidget(button)
    layout.setSpacing(20)  # Add spacing between widgets

    # Finalize window
    window.setLayout(layout)
    window.show()

    # Execute the application
    try:
        app.exec()
    except Exception as e:
        print(f"Error in app.exec: {e}")



def dearpygui_list(items):
    import dearpygui.dearpygui as dpg

    # Callback to display the selected items
    def show_selection(sender, app_data):
        selected_items = [item for item, tag in zip(items, item_tags) if dpg.get_value(tag)]
        dpg.show_item("message_box")
        dpg.set_value("message_text", f"You selected: {', '.join(selected_items)}")

    # Create Dear PyGui context and viewport
    dpg.create_context()
    dpg.create_viewport(title="List Selector", width=400, height=300)
    dpg.setup_dearpygui()

    # Define a unique tag for each item
    item_tags = [f"checkbox_{i}" for i in range(len(items))]

    # Main window with checkboxes
    with dpg.window(label="Select Items", width=400, height=250):
        for item, tag in zip(items, item_tags):
            dpg.add_checkbox(label=item, tag=tag)  # Add a checkbox for each item
        dpg.add_button(label="Show Selection", callback=show_selection)

    # Hidden message box window
    with dpg.window(label="Message Box", show=False, tag="message_box"):
        dpg.add_text("", tag="message_text")

    # Show the viewport and start the event loop
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


def pywebio_list(items):
    from pywebio import start_server
    from pywebio.input import select, actions
    from pywebio.output import put_text
    import threading

    def app():
        # Prompt user to select items
        selected = select("Select items", items, multiple=True)
        put_text(f"You selected: {', '.join(selected)}")

        # Add an "OK" button to allow the user to confirm
        actions(label="Action", buttons=[{"label": "OK", "value": "ok", "color": "primary"}])

        # Signal to stop the server by stopping the event loop
        threading.Thread(target=exit_server).start()

    def exit_server():
        """Stop the server after completing the session."""
        import os
        import signal

        os.kill(os.getpid(), signal.SIGINT)

    # Run the PyWebIO server in a thread for a single session
    start_server(app, port=8080, auto_close=False)





def prompt_toolkit_list(items):
    from prompt_toolkit.shortcuts import checkboxlist_dialog

    def main():
        values = [(item, item) for item in items]
        result = checkboxlist_dialog(
            title="Select Items",
            text="Choose your items:",
            values=values
        ).run()

        if result:
            print(f"You selected: {', '.join(result)}")
        else:
            print("No items selected.")

    main()


# Example usage for any function:
items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]

# Uncomment the desired function call:
# tkinter_list(items)          # Very lightweight, built-in GUI library for Python, simple and quick to use.
# pyqt5_list(items)            # Rich, feature-heavy library with Python bindings for Qt; great for advanced GUI applications.
# wxpython_list(items)         # Simpler API, creates native-looking GUIs using wxWidgets (C++ wrapper); good for smaller projects.
# dearpygui_list(items)        # Modern, GPU-accelerated GUI library for Python; focuses on speed and aesthetics.
# pywebio_list(items)          # Opens in a web browser; suitable for lightweight web-based GUIs without HTML/CSS/JS knowledge. Designed to keep server open forever!
# prompt_toolkit_list(items)   # Must run in cmd/terminal; creates a DOS-style interactive prompt, ideal for CLI applications.

import inspect
from pprint import pprint

from pprint import pprint

# Example with a sounddevice list
import sounddevice as sd

devices = sd.query_devices()

# Explore the list of sound devices
#explore(devices)

# from rich import pretty
# from rich import print
#
# pretty.install()
# print(devices)

# [print(d.attr()) for d in devices[0]]
# print(type(devices))
# print(len(devices))
# print(type(devices[0]))
# print(devices[0].keys())
# print(devices[0].keys())

# def get_variable_name(obj, namespaces):
#     """Find the variable name of an object in given namespaces."""
#     names = []
#     for name, value in namespaces.items():
#         if id(value) == id(obj):  # Match by memory address
#             names.append(name)
#     return names
#
# # Example Usage
# #devices = [{"name": "Device1"}, {"name": "Device2"}]
# print(get_variable_name(devices, locals()))  # Output: ['devices']
#
# def getname(x): return [name for name, value in locals().items() if id(value) == id(x)]
def get_variable_names(obj):
    return [name for name, value in globals().items() if id(value) == id(obj)] or \
           [name for name, value in locals().items() if id(value) == id(obj)]

def get_variable_name(obj):
    names = get_variable_names(obj)
    return names[0] if names else None

def explore(obj, depth=1, indent=0, max_items=None):
    """
    Recursively explore an object, printing its type, length, and content.

    Args:
        obj: The object to explore.
        depth: Maximum recursion depth (default: 1).
        indent: Current indentation level for pretty printing.
        max_items: Maximum number of items to print per level (default: None for no limit).
    """
    spacer = "  " * indent  # Adjust indentation for compact alignment
    try:
        # Print the name only for the root object
        obj_name = get_variable_name(obj) if indent == 0 else None
        obj_info = f"{type(obj).__name__}: {len(obj)}" if hasattr(obj, "__len__") else type(obj).__name__
        if obj_name:
            print(f"{obj_name} = {{{obj_info}}}")
        else:
            print(f"{{{obj_info}}}")
    except Exception as e:
        print(f"(Could not determine length: {e})")

    # Stop recursion if depth is 0
    if depth <= 0:
        return

    # Explore based on type
    if isinstance(obj, dict):
        for i, (key, value) in enumerate(obj.items()):
            if max_items is not None and i >= max_items:
                print(f"{spacer}  ... ({len(obj) - i} more keys)")
                break
            print(f"{spacer} '{key}' = ", end="")
            if isinstance(value, (dict, list, tuple, set)):
                explore(value, depth - 1, indent + 1, max_items)
            else:
                print(f"{{{type(value).__name__}}} {repr(value)}")
    elif isinstance(obj, (list, tuple, set)):
        for i, item in enumerate(obj):
            if max_items is not None and i >= max_items:
                print(f"{spacer}  ... ({len(obj) - i} more items)")
                break
            # Avoid printing = if the list item has no variable name
            print(f"{spacer} [{i}] = ", end="")
            if isinstance(item, (dict, list, tuple, set)):
                explore(item, depth - 1, indent + 1, max_items)
            else:
                print(f"{{{type(item).__name__}}} {repr(item)}")
    else:
        # Print the object itself for non-iterables
        print(f"{{{type(obj).__name__}}} {repr(obj)}")


# import rich
# #rich.inspect(devices)
# rich.inspect(rich.inspect)
# help(rich.inspect)
# explore(devices, depth=5, max_items=8)

# from rich.pretty import Pretty
# from rich import print

# print(Pretty(devices, max_depth=4, max_length=5, expand_all=True))
# explore_type_hierarchy(dl)



#
import numpy as np
import sounddevice as sd
# dl = sounddevice.query_devices()
# device_names = [device['name'] for device in dl]
# device_values = dl  # Full device information
