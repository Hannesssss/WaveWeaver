import os
from tkinter import Tk, Frame, Label, Entry, StringVar, OptionMenu, Listbox, Scrollbar, Button, Scale, HORIZONTAL, Checkbutton, BooleanVar, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui_widgets import Tooltip, toggle_tooltips
from audio_processing import load_file, load_files_from_folder, next_file, prev_file, save_selected_chunk, export_all_chunks, update_waveform, auto_detect
from event_handlers import on_command_type_change, on_file_select, update_file_dropdown, onpick, onmotion, onrelease, update_cut_points_list

# Global variables
loaded_files = []
current_file_index = 0
custom_command_type = None
update_timer = None
tooltips_enabled = True
lines = []
drag_data = {'line': None, 'x': 0}

root = Tk()
root.title("Audio Clip Cutter")

# Create frames for organization
control_frame = Frame(root)
control_frame.grid(row=0, column=0, padx=10, pady=10, sticky='n')

plot_frame = Frame(root)
plot_frame.grid(row=0, column=1, padx=10, pady=10, sticky='n')

cut_points_frame = Frame(root)
cut_points_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='n')

# Define GUI components
Label(control_frame, text="Unit Name:").grid(row=0, column=0, sticky='W', pady=5)
unit_name_var = StringVar()
unit_name_entry = Entry(control_frame, textvariable=unit_name_var)
unit_name_entry.grid(row=0, column=1, pady=5)
Tooltip(unit_name_entry, "Enter the unit name for the audio chunk.")

Label(control_frame, text="Command Type:").grid(row=1, column=0, sticky='W', pady=5)
command_type_var = StringVar()
command_types = ["Select", "Move", "Attack", "Ability", "Assist", "Death", "Guard", "Custom"]
command_type_var.trace('w', on_command_type_change)
command_type_menu = OptionMenu(control_frame, command_type_var, *command_types)
command_type_menu.grid(row=1, column=1, pady=5)
Tooltip(command_type_menu, "Select the command type for the audio chunk.")

Label(control_frame, text="Export Format:").grid(row=2, column=0, sticky='W', pady=5)
export_format_var = StringVar()
export_formats = ["mp3", "wav", "ogg", "flac"]
export_format_menu = OptionMenu(control_frame, export_format_var, *export_formats)
export_format_menu.grid(row=2, column=1, pady=5)
Tooltip(export_format_menu, "Select the export format for the audio chunk.")

Label(control_frame, text="LUFS Target:").grid(row=3, column=0, sticky='W', pady=5)
lufs_var = DoubleVar()
lufs_scale = Scale(control_frame, from_=-30, to=0, orient=HORIZONTAL, resolution=0.1, variable=lufs_var, showvalue=True)
lufs_scale.set(-11)
lufs_scale.grid(row=3, column=1, pady=5)
Tooltip(lufs_scale, "Set the LUFS target for audio normalization.")

lufs_entry = Entry(control_frame, textvariable=lufs_var)
lufs_entry.grid(row=4, column=1, pady=5)
Tooltip(lufs_entry, "Enter the LUFS target for audio normalization.")

Label(control_frame, text="Silence Threshold (dB):").grid(row=5, column=0, sticky='W', pady=5)
silence_thresh_var = DoubleVar()
silence_thresh_scale = Scale(control_frame, from_=-60, to=0, orient=HORIZONTAL, variable=silence_thresh_var, showvalue=True)
silence_thresh_scale.set(-40)
silence_thresh_scale.grid(row=5, column=1, pady=5)
Tooltip(silence_thresh_scale, "Adjust the silence threshold for splitting audio chunks.")

silence_thresh_entry = Entry(control_frame, textvariable=silence_thresh_var)
silence_thresh_entry.grid(row=6, column=1, pady=5)
Tooltip(silence_thresh_entry, "Enter the silence threshold for splitting audio chunks.")

silence_thresh_var.trace('w', update_waveform)

load_file_button = Button(control_frame, text="Load Audio File", command=lambda: load_file(filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav;*.mp4")])))
load_file_button.grid(row=7, column=0, columnspan=2, pady=10)
Tooltip(load_file_button, "Load a single audio file.")

load_folder_button = Button(control_frame, text="Load Folder", command=load_files_from_folder)
load_folder_button.grid(row=8, column=0, columnspan=2, pady=10)
Tooltip(load_folder_button, "Load all audio files from a folder.")

prev_file_button = Button(control_frame, text="Previous File", command=prev_file)
prev_file_button.grid(row=9, column=0, pady=10)
Tooltip(prev_file_button, "Load the previous audio file.")

next_file_button = Button(control_frame, text="Next File", command=next_file)
next_file_button.grid(row=9, column=1, pady=10)
Tooltip(next_file_button, "Load the next audio file.")

Label(control_frame, text="Loaded file:").grid(row=10, column=0, pady=5)
file_label = Label(control_frame, text="None")
file_label.grid(row=10, column=1, pady=5)
Tooltip(file_label, "Displays the name of the currently loaded audio file.")

file_list_var = StringVar()
file_list_var.trace('w', on_file_select)
file_dropdown = OptionMenu(control_frame, file_list_var, "")
file_dropdown.grid(row=11, column=0, columnspan=2, pady=5)
Tooltip(file_dropdown, "Select a file from the loaded folder.")

scrollbar = Scrollbar(control_frame)
scrollbar.grid(row=12, column=2, sticky='ns', pady=10)
listbox = Listbox(control_frame, yscrollcommand=scrollbar.set)
listbox.grid(row=12, column=0, columnspan=2, pady=10)
scrollbar.config(command=listbox.yview)
Tooltip(listbox, "Displays the detected audio chunks.")

save_chunk_button = Button(control_frame, text="Save Selected Chunk", command=save_selected_chunk)
save_chunk_button.grid(row=13, column=0, columnspan=2, pady=10)
Tooltip(save_chunk_button, "Save the selected audio chunk.")

export_chunks_button = Button(control_frame, text="Export All Chunks", command=export_all_chunks)
export_chunks_button.grid(row=14, column=0, columnspan=2, pady=10)
Tooltip(export_chunks_button, "Export all detected audio chunks.")

auto_detect_button = Button(control_frame, text="Auto Detect", command=auto_detect)
auto_detect_button.grid(row=15, column=0, columnspan=2, pady=10)
Tooltip(auto_detect_button, "Automatically detect optimal settings for silence threshold and LUFS target.")

figure = plt.Figure(figsize=(10, 4))
canvas = FigureCanvasTkAgg(figure, master=plot_frame)
canvas.get_tk_widget().grid(row=0, column=0, pady=10)
Tooltip(canvas.get_tk_widget(), "Displays the waveform of the loaded audio file.")

output_dir = os.path.join(os.getcwd(), "output")
os.makedirs(output_dir, exist_ok=True)

# Checkbox to toggle tooltips
tooltip_var = BooleanVar(value=True)
tooltip_checkbox = Checkbutton(control_frame, text="Enable Tooltips", variable=tooltip_var, command=toggle_tooltips)
tooltip_checkbox.grid(row=16, column=0, columnspan=2, pady=5)
Tooltip(tooltip_checkbox, "Toggle tooltips on or off.")

canvas.mpl_connect('pick_event', onpick)
canvas.mpl_connect('motion_notify_event', onmotion)
canvas.mpl_connect('button_release_event', onrelease)

root.mainloop()
