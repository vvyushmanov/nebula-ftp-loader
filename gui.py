import sys
import time
import tkinter as tk
from tkinter import ttk, Tk
from tkinter.scrolledtext import ScrolledText
from os import path

from PIL.Image import Resampling

from core import Core
from utils import Product, BuildType, ExitError, get_platform
import threading

from PIL import Image, ImageTk


class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Scroll to latest message

    def flush(self):
        pass


class FTPLoaderGUI:
    window: Tk

    def __init__(self):
        self.window = tk.Tk()
        self.cleanup_checkbox = None
        self.install_checkbox = None
        self.branch_label = None
        self.build_type_label = None
        self.s_radiobutton = None
        self.g_radiobutton = None
        self.product_label = None
        self.image_label = None
        self.progressbar = None
        self.speed_thread = None
        self.speed_label = None
        self.progress_var = tk.DoubleVar()
        self.core = None
        self.core_thread = None
        self.download_button = None
        self.log_text = None
        self.install_var = None
        self.branch_entry = None
        self.build_type_combobox = None
        self.product = None
        self.delete_var = None
        self.build_type_var = None
        self.branch_var = None
        self.in_progress = False
        self.time_remaining = tk.IntVar()
        self.time_remaining.set(0)
        self.download_speed = tk.DoubleVar()
        self.download_speed.set(0)
        self.window.title("T.Nebula")
        self.font = ("Arial", 12)
        self.set_icon()
        self.create_widgets()
        sys.stdout = TextRedirector(self.log_text)

    def set_icon(self):
        if get_platform() == "win":
            icon_path = path.abspath(path.join(path.dirname(__file__), "t-nebula.ico"))
            self.window.iconbitmap(icon_path)
        else:
            icon_path = path.abspath(path.join(path.dirname(__file__), "t-nebula.gif"))
            img = tk.PhotoImage(file=icon_path)
            self.window.tk.call("wm", "iconphoto", self.window._w, img)

    def set_product_widget(self):
        self.product = tk.StringVar(value=Product.TG.value)
        self.product_label = ttk.Label(self.window, text="Product:", font=self.font)

        self.g_radiobutton = tk.Radiobutton(
            self.window,
            text="T.G",
            variable=self.product,
            value=Product.TG.value,
            font=self.font,
        )
        self.s_radiobutton = tk.Radiobutton(
            self.window,
            text="T.S",
            variable=self.product,
            value=Product.TS.value,
            font=self.font,
        )

    def set_build_type_widget(self):
        self.build_type_var = tk.StringVar(value=BuildType.DEV.value)
        self.build_type_label = ttk.Label(
            self.window, text="Build Type:", font=self.font
        )
        values = ["DEV", "RC", "RELEASE"]
        self.build_type_combobox = ttk.OptionMenu(
            self.window, self.build_type_var, values[0], *values
        )
        self.build_type_var.trace("w", self.on_build_type_change)

    def set_branch_widgets(self):
        max_chars = 50

        def validate_entry(input_symbols):
            if len(input_symbols) <= max_chars:
                return True
            return False

        validate_func = self.window.register(validate_entry)

        self.branch_var = tk.StringVar()
        self.branch_label = ttk.Label(self.window, text="Branch:", font=self.font)
        self.branch_entry = ttk.Entry(
            self.window,
            textvariable=self.branch_var,
            validate="key",  # Валидация при каждом нажатии клавиши
            validatecommand=(validate_func, "%P"),
            state="normal",
            width=23,
        )

    def update_cleanup_checkbox(self):
        if "selected" in self.install_checkbox.state():
            self.delete_var.set(True)
            self.cleanup_checkbox.config(state="normal")
        else:
            self.delete_var.set(False)
            self.cleanup_checkbox.config(state="disabled")

    def set_checkbox_widgets(self):
        self.install_var = tk.BooleanVar(value=True)
        self.delete_var = tk.BooleanVar(value=True)
        self.install_checkbox = ttk.Checkbutton(
            self.window,
            text="Install",
            variable=self.install_var,
            command=self.update_cleanup_checkbox,
        )
        self.cleanup_checkbox = ttk.Checkbutton(
            self.window, text="Cleanup", variable=self.delete_var
        )

    def set_download_widgets(self):
        self.download_button = ttk.Button(
            self.window, text="Download", command=self.start_button_clicked
        )
        # Progress bar
        self.progressbar = ttk.Progressbar(
            self.window, variable=self.progress_var, maximum=100
        )
        # Stats
        self.speed_label = ttk.Label(
            self.window,
            text=f"{round(self.download_speed.get(), 2)} Mb/s, {self.time_remaining.get() // 60} m {self.time_remaining.get() % 60} s",
            width=20,
        )

    def set_log_box_widget(self):
        self.log_text = ScrolledText(
            self.window,
            height=15,
            width=70,
            bg="black",
            fg="#00ff00",
            insertbackground="#00ff00",
        )
        self.log_text.bind("<Key>", lambda event: "break")
        self.log_text.bind("<Control-c>", self.copy_text)

    def set_mascot_image_widget(self):
        image_path = path.abspath(path.join(path.dirname(__file__), "T-chan.png"))
        image = Image.open(image_path)
        scale_percent = 25
        original_width, original_height = image.size
        new_width = int(original_width * scale_percent / 100)
        new_height = int(original_height * scale_percent / 100)
        new_size = (new_width, new_height)
        resized_image = image.resize(new_size, Resampling.BICUBIC)
        photo = ImageTk.PhotoImage(resized_image)

        self.image_label = ttk.Label(self.window, image=photo)
        self.image_label.image = photo

    def set_widgets_grid(self):
        # Column and row grid config
        self.window.grid_columnconfigure(0, weight=0)
        self.window.grid_columnconfigure(1, weight=0)
        self.window.grid_columnconfigure(2, weight=0)
        self.window.grid_columnconfigure(3, weight=100)
        self.window.grid_rowconfigure(6, weight=1)

        # Product widgets grid
        self.product_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.g_radiobutton.grid(row=0, column=1, pady=5, sticky="w")
        self.s_radiobutton.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # Build type widgets grid
        self.build_type_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.build_type_combobox.grid(row=1, column=1, columnspan=2, sticky="w")

        # Branch widgets grid
        self.branch_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.branch_entry.grid(row=2, column=1, columnspan=2, sticky="w")

        # Checkbox widgets grid
        self.install_checkbox.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.cleanup_checkbox.grid(row=3, column=1, sticky="w")

        # Download progress widgets grid
        # Progress bar grid (row=5) is set separately in self.update_download_progress(), is hidden by default!
        self.download_button.grid(row=4, column=0, pady=10, padx=10, sticky="w")

        # Log box widget
        self.log_text.grid(
            row=6, column=0, columnspan=5, padx=10, pady=10, sticky="nsew"
        )

        # Image widget
        self.image_label.grid(
            row=0, column=3, columnspan=2, rowspan=5, padx=10, pady=10, sticky="nse"
        )

    def create_widgets(self):
        # Dropdowns for product, build type, and branch
        self.set_product_widget()
        self.set_build_type_widget()
        self.set_branch_widgets()
        # Checkboxes for install and delete options
        self.set_checkbox_widgets()
        # Download button, progress bar, download stats
        self.set_download_widgets()
        # Text box for logs
        self.set_log_box_widget()
        # T-chan
        self.set_mascot_image_widget()
        # Weights for columns and rows
        self.set_widgets_grid()

    def on_build_type_change(self, *args):
        if self.build_type_var.get() == "DEV":
            self.branch_entry.config(state="normal")
        else:
            self.branch_entry.config(state="disabled")
            self.branch_var.set("")

    def copy_text(self, event):
        try:
            selected_text = self.log_text.selection_get()
            self.window.clipboard_clear()
            self.window.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return "break"

    def start_button_clicked(self):
        self.download_speed.set(0)
        self.time_remaining.set(0)
        self.progress_var.set(0)
        # Starting main downloading function in a separate thread
        self.core_thread = threading.Thread(target=self.execute, daemon=True)
        self.core_thread.start()

    def show_progress_widgets(self):
        self.progressbar.grid(
            row=5, column=0, columnspan=4, padx=10, pady=10, sticky="ew"
        )
        self.speed_label.grid(row=5, column=4, padx=10, pady=10)

    def hide_progress_widgets(self):
        self.speed_label.grid_forget()
        self.progressbar.grid_forget()

    def update_download_progress(self):
        self.window.after(0, self.show_progress_widgets)
        self.in_progress = True
        while self.in_progress:
            self.speed_label.config(
                text=f"{round(self.download_speed.get(), 2)} Mb/s, "
                f"{self.time_remaining.get() // 60} m {self.time_remaining.get() % 60} s"
            )
            time.sleep(1)
        self.window.after(0, self.hide_progress_widgets)

    def cancel_download(self):
        self.window.after(0, self.download_button_state_switch)
        self.in_progress = False
        thread = threading.Thread(target=self.cancel_thread, name="cancellation")
        thread.start()

    def cancel_thread(self):
        self.core.stop_download()
        print("\nDownload cancelled")
        # Revert the button to initial state
        time.sleep(1)
        self.window.after(0, self.download_button_state_switch)

    def download_button_state_switch(self):
        if "disabled" in self.download_button.state():
            self.download_button.config(
                text="Download", command=self.start_button_clicked, state="normal"
            )
        else:
            self.download_button.config(state="disabled", text="Stopping...")

    def execute(self):
        # Setting branch to "develop" as default for DEV builds
        if (
            self.build_type_var.get() == BuildType.DEV.value
            and not self.branch_var.get()
        ):
            self.branch_var.set("develop")

        # Update download button to be become Cancel button
        self.download_button.config(text="Cancel", command=self.cancel_download)

        self.in_progress = True

        product = self.product.get()
        build_type = self.build_type_var.get()
        branch = self.branch_var.get()
        install = self.install_var.get()
        cleanup = self.delete_var.get()

        self.speed_thread = threading.Thread(
            target=self.update_download_progress, daemon=True
        )
        self.speed_thread.start()

        self.core = Core(
            product=product,
            build_type=build_type,
            branch=branch,
            install=install,
            delete=cleanup,
            gui=True,
            progress_var=self.progress_var,
            gui_window=self.window,
            download_speed=self.download_speed,
            time_remaining=self.time_remaining,
            progressbar=self.progressbar,
        )
        self.log_text.delete("1.0", "end")
        print("Connecting...")

        try:
            self.core.execute()
        except ExitError as e:
            if self.in_progress:
                print(e)
            else:
                pass
        self.in_progress = False
        self.download_button.config(text="Download", command=self.start_button_clicked)

    def run(self):
        self.window.mainloop()
