import os
from pydub import AudioSegment, silence, effects
from tkinter import filedialog, messagebox, Toplevel, Label, StringVar, Entry, Button, OptionMenu, Scale, DoubleVar, HORIZONTAL
import numpy as np

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

def save_selected_chunk():
    try:
        selected_chunk_index = listbox.curselection()[0]
        unit_name = unit_name_var.get()
        command_type = command_type_var.get()
        export_format = export_format_var.get()
        lufs_target = lufs_var.get()

        if command_type == "Custom" and custom_command_type:
            command_type = custom_command_type

        if unit_name and command_type and export_format:
            save_chunk(audio_chunks[selected_chunk_index], unit_name, command_type, selected_chunk_index + 1, output_dir, export_format, lufs_target)
            messagebox.showinfo("Success", "Chunk saved successfully!")
        else:
            messagebox.showwarning("Input Error", "Please provide unit name, command type, and export format.")
    except IndexError:
        messagebox.showwarning("Selection Error", "Please select a chunk from the list.")
    except ValueError as ve:
        messagebox.showerror("Export Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save chunk: {str(e)}")

def export_all_chunks():
    unit_name = unit_name_var.get()
    command_type = command_type_var.get()
    export_format = export_format_var.get()
    lufs_target = lufs_var.get()
    
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
        
        def on_export():
            updated_unit_name = unit_name_var_dialog.get()
            updated_command_type = command_type_var_dialog.get()
            updated_export_format = export_format_var_dialog.get()
            updated_lufs_target = lufs_var_dialog.get()
            output_path = filedialog.askdirectory()

            if not output_path:
                messagebox.showwarning("Export Error", "Please select an output directory.")
                return
            
            if not updated_unit_name or not updated_command_type or not updated_export_format:
                messagebox.showwarning("Input Error", "Please provide unit name, command type, and export format.")
                return
            
            try:
                for i, chunk in enumerate(audio_chunks):
                    save_chunk(chunk, updated_unit_name, updated_command_type, i + 1, output_path, updated_export_format, updated_lufs_target)
                messagebox.showinfo("Success", "All chunks saved successfully!")
                dialog.destroy()
            except ValueError as ve:
                messagebox.showerror("Export Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chunks: {str(e)}")

        Button(dialog, text="Export", command=on_export).grid(row=4, column=0, columnspan=2, pady=10)

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
                save_chunk(chunk, unit_name, command_type, i + 1, output_path, export_format, lufs_target)
            messagebox.showinfo("Success", "All chunks saved successfully!")
        except ValueError as ve:
            messagebox.showerror("Export Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export chunks: {str(e)}")

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

def auto_detect():
    global sound
    if sound is None:
        messagebox.showwarning("Error", "Please load an audio file first.")
        return

    samples = np.array(sound.get_array_of_samples())
    silence_thresh = np.percentile(samples, 2)  # Use the 2nd percentile as a threshold
    lufs_target = -np.mean(samples)  # Use the mean of the samples as the LUFS target

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

def cut_audio(sound, silence_thresh):
    chunks = silence.split_on_silence(sound, min_silence_len=500, silence_thresh=silence_thresh)
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

def save_chunk(chunk, unit_name, command_type, index, output_dir, export_format, lufs_target):
    if lufs_target is not None:
        chunk = effects.normalize(chunk, headroom=lufs_target - chunk.dBFS)

    if not export_format:
        raise ValueError("Export format is not specified")

    file_name = f"{command_type}{index}_{unit_name}.{export_format}"
    output_path = os.path.join(output_dir, command_type)
    os.makedirs(output_path, exist_ok=True)
    chunk.export(os.path.join(output_path, file_name), format=export_format)
