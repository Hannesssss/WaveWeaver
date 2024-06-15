import os
from pydub import AudioSegment, silence, effects
from tkinter import Tk, Label, Button, Entry, filedialog, StringVar, OptionMenu, Listbox, Scrollbar, messagebox, Scale, HORIZONTAL, Frame, simpledialog, DoubleVar, Checkbutton, BooleanVar, Toplevel, Spinbox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Set the path to FFmpeg binaries
ffmpeg_path = r"C:\Program Files\ffmpeg-7.0.1-essentials_build\bin"
AudioSegment.ffmpeg = os.path.join(ffmpeg_path, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")

# Global variables
sound = None
audio_chunks = []
cut_points = []
loaded_files = []
current_file_index = 0
custom_command_type = None
update_timer = None  # Timer for delayed updates
tooltips_enabled = True
lines = []  # To store line references for draggable cut points

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        global tooltips_enabled
        if not tooltips_enabled:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = Tk()
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify='left',
                      background="#ffffe0", relief='solid', borderwidth=1,
                      wraplength=200)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

def toggle_tooltips():
    global tooltips_enabled
    tooltips_enabled = tooltip_var.get()

def cut_audio(sound, silence_thresh=-40, min_silence_len=500):
    chunks = silence.split_on_silence(
        sound, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    global cut_points
    cut_points = []
    start = 0
    for chunk in chunks:
        end = start + len(chunk)
        cut_points.append((start, end))
        start = end
    return chunks

def plot_waveform(sound, silence_thresh, ax):
    samples = sound.get_array_of_samples()
    ax.clear()
    ax.plot(samples, label='Waveform', color='blue')
    ax.axhline(y=silence_thresh, color='r', linestyle='--', label='Silence Threshold')
    ax.axhline(y=-silence_thresh, color='r', linestyle='--')
    
    for line in lines:
        line.remove()
    lines.clear()
    
    for start, end in cut_points:
        line_start = ax.axvline(x=start, color='yellow', linestyle='--', lw=2, picker=5)
        line_end = ax.axvline(x=end, color='yellow', linestyle='--', lw=2, picker=5)
        lines.append(line_start)
        lines.append(line_end)
    
    ax.legend()
    canvas.draw()

def save_chunk(chunk, unit_name, command_type, index, output_dir, export_format, lufs_target, include_eng_suffix):
    if lufs_target is not None:
        chunk = effects.normalize(chunk, headroom=lufs_target - chunk.dBFS)

    if not export_format:
        raise ValueError("Export format is not specified")

    suffix = "_ENG" if include_eng_suffix else ""
    file_name = f"{unit_name}_{command_type}{index}{suffix}.{export_format}"
    output_path = os.path.join(output_dir, command_type)
    os.makedirs(output_path, exist_ok=True)
    chunk.export(os.path.join(output_path, file_name), format=export_format)

def load_file(file_path):
    global sound, audio_chunks
    if file_path:
        try:
            sound = AudioSegment.from_file(file_path)
            update_waveform()
            file_label.config(text=f"Loaded file: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio file: {str(e)}")

def load_files_from_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        global loaded_files, current_file_index
        loaded_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.mp3', '.wav', '.mp4'))]
        if loaded_files:
            current_file_index = 0
            file_list_var.set(loaded_files[current_file_index])
            update_file_label()
            load_file(loaded_files[current_file_index])
            update_file_dropdown()

def next_file():
    global current_file_index
    if current_file_index < len(loaded_files) - 1:
        current_file_index += 1
        load_file(loaded_files[current_file_index])
        update_file_label()

def prev_file():
    global current_file_index
    if current_file_index > 0:
        current_file_index -= 1
        load_file(loaded_files[current_file_index])
        update_file_label()

def update_file_label():
    file_label.config(text=f"Loaded file: {os.path.basename(loaded_files[current_file_index])}")

def save_selected_chunk():
    try:
        selected_chunk_index = listbox.curselection()[0]
        unit_name = unit_name_var.get()
        command_type = command_type_var.get()
        export_format = export_format_var.get()
        lufs_target = lufs_var.get()
        include_eng_suffix = eng_var.get()

        if command_type == "Custom" and custom_command_type:
            command_type = custom_command_type

        if unit_name and command_type and export_format:
            save_chunk(audio_chunks[selected_chunk_index], unit_name, command_type, selected_chunk_index + 1, output_dir, export_format, lufs_target, include_eng_suffix)
            messagebox.showinfo("Success", "Chunk saved successfully!")
        else:
            messagebox.showwarning("Input Error", "Please provide unit name, command type, and export format.")
    except IndexError:
        messagebox.showwarning("Selection Error", "Please select a chunk from the list.")
    except ValueError as ve:
        messagebox.showerror("Export Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save chunk: {str(e)}")

def update_waveform(*args):
    global update_timer
    if sound is None:
        return

    if update_timer is not None:
        root.after_cancel(update_timer)
    
    update_timer = root.after(500, perform_waveform_update)

def perform_waveform_update():
    silence_thresh = silence_thresh_var.get()
    global audio_chunks
    audio_chunks = cut_audio(sound, silence_thresh=silence_thresh)
    listbox.delete(0, 'end')
    for i, chunk in enumerate(audio_chunks):
        listbox.insert('end', f"Chunk {i+1}")
    plot_waveform(sound, silence_thresh, figure.add_subplot(111))
    update_cut_points_list()

def manual_update_waveform(event=None):
    try:
        silence_thresh = silence_thresh_var.get()
        update_waveform()
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid integer for the silence threshold.")

def export_all_chunks():
    unit_name = unit_name_var.get()
    command_type = command_type_var.get()
    export_format = export_format_var.get()
    lufs_target = lufs_var.get()
    include_eng_suffix = eng_var.get()
    
    # Check if any of the required fields are missing
    if not unit_name or not command_type or not export_format:
        dialog = Toplevel(root)
        dialog.title("Export Settings")

        Label(dialog, text="Unit Name:").grid(row=0, column=0, sticky='W', pady=5)
        unit_name_var_dialog = StringVar(value=unit_name)
        unit_name_entry_dialog = Entry(dialog, textvariable=unit_name_var_dialog)
        unit_name_entry_dialog.grid(row=0, column=1, pady=5)

        Label(dialog, text="Command Type:").grid(row=1, column=0, sticky='W', pady=5)
        command_type_var_dialog = StringVar(value=command_type)
        command_types = ["Select", "Move", "Attack", "Ability", "Assist", "Death", "Guard", "Custom"]
        command_type_menu_dialog = OptionMenu(dialog, command_type_var_dialog, *command_types)
        command_type_menu_dialog.grid(row=1, column=1, pady=5)

        Label(dialog, text="Export Format:").grid(row=2, column=0, sticky='W', pady=5)
        export_format_var_dialog = StringVar(value=export_format)
        export_formats = ["mp3", "wav", "ogg", "flac"]
        export_format_menu_dialog = OptionMenu(dialog, export_format_var_dialog, *export_formats)
        export_format_menu_dialog.grid(row=2, column=1, pady=5)

        Label(dialog, text="LUFS Target:").grid(row=3, column=0, sticky='W', pady=5)
        lufs_var_dialog = DoubleVar(value=lufs_target)
        lufs_scale_dialog = Scale(dialog, from_=-30, to=0, orient=HORIZONTAL, resolution=0.1, variable=lufs_var_dialog, showvalue=True)
        lufs_scale_dialog.set(-11)
        lufs_scale_dialog.grid(row=3, column=1, pady=5)

        eng_var_dialog = BooleanVar(value=include_eng_suffix)
        eng_checkbox_dialog = Checkbutton(dialog, text="Include _ENG Suffix", variable=eng_var_dialog)
        eng_checkbox_dialog.grid(row=4, column=0, columnspan=2, pady=5)
        
        def on_export():
            updated_unit_name = unit_name_var_dialog.get()
            updated_command_type = command_type_var_dialog.get()
            updated_export_format = export_format_var_dialog.get()
            updated_lufs_target = lufs_var_dialog.get()
            updated_include_eng_suffix = eng_var_dialog.get()
            output_path = filedialog.askdirectory()

            if not output_path:
                messagebox.showwarning("Export Error", "Please select an output directory.")
                return
            
            if not updated_unit_name or not updated_command_type or not updated_export_format:
                messagebox.showwarning("Input Error", "Please provide unit name, command type, and export format.")
                return
            
            try:
                for i, chunk in enumerate(audio_chunks):
                    save_chunk(chunk, updated_unit_name, updated_command_type, i + 1, output_path, updated_export_format, updated_lufs_target, updated_include_eng_suffix)
                messagebox.showinfo("Success", "All chunks saved successfully!")
                dialog.destroy()
            except ValueError as ve:
                messagebox.showerror("Export Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chunks: {str(e)}")

        Button(dialog, text="Export", command=on_export).grid(row=5, column=0, columnspan=2, pady=10)

        dialog.transient(root)
        dialog.grab_set()
        root.wait_window(dialog)
    else:
        output_path = filedialog.askdirectory()
        if not output_path:
            messagebox.showwarning("Export Error", "Please select an output directory.")
            return
        
        try:
            for i, chunk in enumerate(audio_chunks):
                save_chunk(chunk, unit_name, command_type, i + 1, output_path, export_format, lufs_target, include_eng_suffix)
            messagebox.showinfo("Success", "All chunks saved successfully!")
        except ValueError as ve:
            messagebox.showerror("Export Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export chunks: {str(e)}")

def on_command_type_change(*args):
    global custom_command_type
    command_type = command_type_var.get()
    if command_type == "Custom":
        custom_command_type = simpledialog.askstring("Input", "Please enter custom command type:")
        if custom_command_type:
            command_types[-1] = custom_command_type  # Update the last item in the list to the new custom command
            command_type_var.set(custom_command_type)
        else:
            custom_command_type = None
            command_type_var.set(command_types[0])  # Reset to default if no input

def on_file_select(*args):
    global current_file_index
    selected_file = file_list_var.get()
    current_file_index = loaded_files.index(selected_file)
    load_file(loaded_files[current_file_index])
    update_file_label()

def update_file_dropdown():
    file_menu = file_dropdown["menu"]
    file_menu.delete(0, "end")
    for file in loaded_files:
        file_menu.add_command(label=os.path.basename(file), command=lambda value=file: file_list_var.set(value))

def onpick(event):
    if event.artist in lines:
        line = event.artist
        drag_data['line'] = line
        drag_data['x'] = event.mouseevent.xdata

def onmotion(event):
    if drag_data['line'] is not None:
        x = event.xdata
        drag_data['line'].set_xdata([x, x])
        canvas.draw()

def onrelease(event):
    if drag_data['line'] is not None:
        x = event.xdata
        drag_data['line'].set_xdata([x, x])
        cut_index = lines.index(drag_data['line']) // 2
        if lines.index(drag_data['line']) % 2 == 0:  # Adjusting start point
            cut_points[cut_index] = (x, cut_points[cut_index][1])
        else:  # Adjusting end point
            cut_points[cut_index] = (cut_points[cut_index][0], x)
        drag_data['line'] = None
        canvas.draw()
    update_cut_points_list()

def auto_detect():
    global sound
    if sound is None:
        messagebox.showwarning("Error", "Please load an audio file first.")
        return

    silence_thresh = -40  # Fixed threshold for simplicity
    lufs_target = -11  # Typical broadcast standard LUFS

    silence_thresh_var.set(silence_thresh)
    lufs_var.set(lufs_target)

    silence_thresh = silence_thresh_var.get()
    global audio_chunks
    audio_chunks = cut_audio(sound, silence_thresh=silence_thresh)
    listbox.delete(0, 'end')
    for i, chunk in enumerate(audio_chunks):
        listbox.insert('end', f"Chunk {i+1}")
    plot_waveform(sound, silence_thresh, figure.add_subplot(111))
    update_cut_points_list()

def update_cut_points_list():
    for widget in cut_points_frame.winfo_children():
        widget.destroy()
    Label(cut_points_frame, text="Cut Points:").grid(row=0, column=0, columnspan=3)
    for i, (start, end) in enumerate(cut_points):
        Label(cut_points_frame, text=f"Chunk {i+1}").grid(row=i+1, column=0)
        start_spinbox = Spinbox(cut_points_frame, from_=0, to=len(sound), increment=1, width=10)
        start_spinbox.delete(0, 'end')
        start_spinbox.insert(0, int(start))
        start_spinbox.grid(row=i+1, column=1)
        start_spinbox.bind("<Return>", lambda event, i=i: update_start_point(i, start_spinbox.get()))
        end_spinbox = Spinbox(cut_points_frame, from_=0, to=len(sound), increment=1, width=10)
        end_spinbox.delete(0, 'end')
        end_spinbox.insert(0, int(end))
        end_spinbox.grid(row=i+1, column=2)
        end_spinbox.bind("<Return>", lambda event, i=i: update_end_point(i, end_spinbox.get()))

def update_start_point(i, value):
    global cut_points
    cut_points[i] = (int(value), cut_points[i][1])
    plot_waveform(sound, silence_thresh_var.get(), figure.add_subplot(111))

def update_end_point(i, value):
    global cut_points
    cut_points[i] = (cut_points[i][0], int(value))
    plot_waveform(sound, silence_thresh_var.get(), figure.add_subplot(111))

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

eng_var = BooleanVar(value=True)
eng_checkbox = Checkbutton(control_frame, text="Include _ENG Suffix", variable=eng_var)
eng_checkbox.grid(row=4, column=0, columnspan=2, pady=5)
Tooltip(eng_checkbox, "Toggle the inclusion of the _ENG suffix in file names.")

auto_detect_button = Button(control_frame, text="Auto Detect", command=auto_detect)
auto_detect_button.grid(row=5, column=0, columnspan=2, pady=10)
Tooltip(auto_detect_button, "Automatically detect optimal settings for silence threshold and LUFS target.")

Label(control_frame, text="Silence Threshold (dB):").grid(row=6, column=0, sticky='W', pady=5)
silence_thresh_var = DoubleVar()
silence_thresh_scale = Scale(control_frame, from_=-60, to=0, orient=HORIZONTAL, variable=silence_thresh_var, showvalue=True)
silence_thresh_scale.set(-40)
silence_thresh_scale.grid(row=6, column=1, pady=5)
Tooltip(silence_thresh_scale, "Adjust the silence threshold for splitting audio chunks.")

silence_thresh_entry = Entry(control_frame, textvariable=silence_thresh_var)
silence_thresh_entry.grid(row=7, column=1, pady=5)
Tooltip(silence_thresh_entry, "Enter the silence threshold for splitting audio chunks.")

silence_thresh_var.trace('w', update_waveform)

load_file_button = Button(control_frame, text="Load Audio File", command=lambda: load_file(filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav;*.mp4")])))
load_file_button.grid(row=8, column=0, columnspan=2, pady=10)
Tooltip(load_file_button, "Load a single audio file.")

load_folder_button = Button(control_frame, text="Load Folder", command=load_files_from_folder)
load_folder_button.grid(row=9, column=0, columnspan=2, pady=10)
Tooltip(load_folder_button, "Load all audio files from a folder.")

prev_file_button = Button(control_frame, text="Previous File", command=prev_file)
prev_file_button.grid(row=10, column=0, pady=10)
Tooltip(prev_file_button, "Load the previous audio file.")

next_file_button = Button(control_frame, text="Next File", command=next_file)
next_file_button.grid(row=10, column=1, pady=10)
Tooltip(next_file_button, "Load the next audio file.")

Label(control_frame, text="Loaded file:").grid(row=11, column=0, pady=5)
file_label = Label(control_frame, text="None")
file_label.grid(row=11, column=1, pady=5)
Tooltip(file_label, "Displays the name of the currently loaded audio file.")

file_list_var = StringVar()
file_list_var.trace('w', on_file_select)
file_dropdown = OptionMenu(control_frame, file_list_var, "")
file_dropdown.grid(row=12, column=0, columnspan=2, pady=5)
Tooltip(file_dropdown, "Select a file from the loaded folder.")

scrollbar = Scrollbar(control_frame)
scrollbar.grid(row=13, column=2, sticky='ns', pady=10)
listbox = Listbox(control_frame, yscrollcommand=scrollbar.set)
listbox.grid(row=13, column=0, columnspan=2, pady=10)
scrollbar.config(command=listbox.yview)
Tooltip(listbox, "Displays the detected audio chunks.")

save_chunk_button = Button(control_frame, text="Save Selected Chunk", command=save_selected_chunk)
save_chunk_button.grid(row=14, column=0, columnspan=2, pady=10)
Tooltip(save_chunk_button, "Save the selected audio chunk.")

export_chunks_button = Button(control_frame, text="Export All Chunks", command=export_all_chunks)
export_chunks_button.grid(row=15, column=0, columnspan=2, pady=10)
Tooltip(export_chunks_button, "Export all detected audio chunks.")

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
