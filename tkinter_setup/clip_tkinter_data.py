import tkinter as tk

class ClipTkinterData:
    def __init__(self):

        # listy rozwijane
        self.combo_list_date = 'combo_list_date'
        self.combo_list_time = 'combo_list_time'
        self.combo_list_count = 'combo_list_count'

        # podręczna lista plików do załadowania wg danych z list rozwijanych
        self.handy_files_dict = {}

        # dane do tworzenia nazwy pliku do załadownia
        self.date = None
        self.time = None
        self.count = None

        # nazwa pliku
        self.file_to_load = None

        # clip
        self.clip = None

        # obiekt draw state
        self.draws_states = None

        self.frame_to_display = None

        self.rotation_angle = 0

    def init_tk_objects(self):
        self.date = tk.StringVar()
        self.time = tk.StringVar()
        self.count = tk.StringVar()

        # self.combo_list_date = ttk.Combobox()
        # self.combo_list_time = ttk.Combobox()
        # self.combo_list_count = ttk.Combobox()

        # self.date.set("Select date")
        # self.time.set("Select time")
        # self.count.set("Select file number")
