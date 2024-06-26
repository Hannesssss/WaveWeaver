from tkinter import Toplevel, Label, BooleanVar

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if tooltip_var.get():
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25
            self.tooltip = Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = Label(self.tooltip, text=self.text, background="yellow", relief="solid", borderwidth=1, padx=5, pady=3)
            label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def toggle_tooltips():
    global tooltips_enabled
    tooltips_enabled = not tooltips_enabled

tooltip_var = BooleanVar(value=True)
