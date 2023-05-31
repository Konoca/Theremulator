from HandTracking import HandTracking
from synthesizer import Synthesizer

import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from time import sleep

class Theremulator:
    def __init__(self, webcam_id: int = 0):
        self.event = threading.Event()

        self.synth = Synthesizer(minimum_octave=3, maximum_octave=5)
        self.ht = HandTracking(self.synth, webcam_id=webcam_id, event=self.event)

        # start synth + hand tracking on seperate thread
        self.theremin_thread = threading.Thread(target=self.ht.main)
        self.theremin_thread.start()

        # start interface on seperate thread
        #self.ui_thread = threading.Thread(target=self.main_interface)
        #self.ui_thread.start()

        self.main_interface()

        self.exit()

    def menu_bar(self, root):
        menu_bar = tk.Menu(root)

        # create the file menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New")
        file_menu.add_command(label="Open Project")
        file_menu.add_command(label="Save")
        file_menu.add_command(label="Save As")
        file_menu.add_command(label="Export As")
        menu_bar.add_cascade(label="File", menu=file_menu)

        # create the edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Reconfigure Camera")
        edit_menu.add_command(label="Import Audio")
        edit_menu.add_command(label="Import Settings")
        edit_menu.add_command(label="Export Settings")
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # create the help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Manual")
        help_menu.add_command(label="About")
        help_menu.add_command(label="Issue Reporting")
        menu_bar.add_cascade(label="Help", menu=help_menu)

        root.config(menu=menu_bar)

    def video_stream(self):
        while self.ht.img == []:
            sleep(1)

        img = Image.fromarray(self.ht.img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_feed.imgtk = imgtk
        self.video_feed.configure(image=imgtk)
        self.video_feed.after(1, self.video_stream)

    def settings_panel(self):
        settings = ttk.Frame(self.root)
        settings.grid(column=1, row=0, stick=tk.E)
        settings.columnconfigure(0, weight=3)

        # waveform setting
        waveform_label = ttk.Label(settings, text='Select Waveform')
        waveform_label.grid(column=0, row=0, pady=5)

        waveform_dropdown = ttk.OptionMenu(settings, self.waveform_var, 'sine', *self.synth.get_waveforms())
        self.waveform_var.trace('w', self.change_waveform)
        waveform_dropdown.grid(column=0, row=1, pady=5)

        ttk.Label(settings).grid(column=0, row=2, pady=5)

        # range setting
        range_label = ttk.Label(settings, text='Select Range')
        range_label.grid(column=0, row=3, pady=5)

        range_opts = ttk.Frame(settings)
        range_opts.grid(column=0, row=4, pady=5, ipadx=2)

        r_min = [str(i) for i in range(0, 8)] # 0-7
        r_max = [str(i) for i in range(1, 9)] # 1-8
        range_min = ttk.OptionMenu(range_opts, self.range_min_var, '3', *r_min)
        range_max = ttk.OptionMenu(range_opts, self.range_max_var, '5', *r_max)
        self.range_min_var.trace('w', self.change_range)
        self.range_max_var.trace('w', self.change_range)
        range_min.grid(column=0, row=0)
        range_max.grid(column=1, row=0)

        ttk.Label(settings).grid(column=0, row=5, pady=5)

        # perfect pitch setting
        ppitch_toggle = ttk.Button(settings, text='Toggle Perfect Pitch', command=self.synth.toggle_perfect_pitch)
        ppitch_toggle.grid(column=0, row=6)

    def change_waveform(self, *args):
        self.synth.change_waveform(self.waveform_var.get())

    def change_range(self, *args):
        r_min = int(self.range_min_var.get())
        r_max = int(self.range_max_var.get())

        if r_max <= r_min:
            self.range_max_var.set(r_min + 1)
            r_max = r_min + 1

        self.synth.calculate_note_frequencies(minimum_octave=r_min, maximum_octave=r_max)

    def exit(self):
        self.event.set()

    def main_interface(self):
        self.root = tk.Tk()
        self.root.title('Theremulator')
        #self.root.geometry('800x600')
        #self.root.config(bg='#121212')
        self.root.config(bg='#282c34')

        self.waveform_var = tk.StringVar(self.root)
        self.range_min_var = tk.IntVar(self.root)
        self.range_max_var = tk.IntVar(self.root)

        self.root.columnconfigure(0, weight=5)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(1, weight=0)

        self.menu_bar(self.root)

        self.video_feed = ttk.Label(self.root)
        #self.video_feed.pack()
        self.video_feed.grid(column=0, row=0, stick=tk.W)
        self.video_stream()

        self.settings_panel()

        self.root.mainloop()
