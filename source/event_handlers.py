from tkinter import StringVar, simpledialog
import numpy as np

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

def update_cut_points_list():
    for widget in cut_points_frame.winfo_children():
        widget.destroy()
    Label(cut_points_frame, text="Cut Points:").grid(row=0, column=0, columnspan=3)
    for i, (start, end) in enumerate(cut_points):
        Label(cut_points_frame, text=f"Chunk {i+1}").grid(row=i+1, column=0)
        Spinbox(cut_points_frame, from_=0, to=len(sound), increment=1, width=10, command=lambda i=i: update_start_point(i)).grid(row=i+1, column=1)
        Spinbox(cut_points_frame, from_=0, to=len(sound), increment=1, width=10, command=lambda i=i: update_end_point(i)).grid(row=i+1, column=2)

def update_start_point(i):
    global cut_points
    cut_points[i] = (int(cut_points_frame.grid_slaves(row=i+1, column=1)[0].get()), cut_points[i][1])
    plot_waveform(sound, silence_thresh_var.get(), figure.add_subplot(111))

def update_end_point(i):
    global cut_points
    cut_points[i] = (cut_points[i][0], int(cut_points_frame.grid_slaves(row=i+1, column=2)[0].get()))
    plot_waveform(sound, silence_thresh_var.get(), figure.add_subplot(111))
