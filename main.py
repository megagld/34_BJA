import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from manager import *
from PIL import ImageTk
from uuid import uuid4
from PIL import ImageTk
import tkinter as tk


class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image = None
        self.image_id = None
        self.image = None

        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0

        self.resized_image_width = 0
        self.resized_image_height = 0
        
        self.orginal_image_width = 0
        self.orginal_image_height = 0

        self.bind('<Configure>', self.update_values)

        manager.checkboxes_changed.trace_add("write", manager.update_view)
        
        self.bind("<Button-1>", self._on_button_1)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-3>", self._on_button_3)
        self.bind("<Button-2>", self._on_button_2)

    def _on_button_1(self,event):

        # względna pozycja x myszy na obrazie przeskalowanym
        relative_mouse_position = (event.x - (self.width-self.resized_image_width)/2)/self.resized_image_width

        # bezwzględna pozycja myszy na obrazie orginalnym
        absolut_mouse_position_x = relative_mouse_position * self.orginal_image_width

        # znajduje najbliższą klatkę do 
        for frame_count, frame in manager.clip_a.clip.frames.items():
            if frame.detected and frame.trace_point.x > absolut_mouse_position_x:
                manager.frame_to_display = frame_count
                break

        #ustala scale na najbliższą klatkę
        manager.scale.set(manager.frame_to_display)

    def _on_button_3(self,event):

        manager.frame_cnt_change(1)
        
    def _on_button_2(self,event):
        # ustala punkt wybicia
        # względna pozycja x myszy na obnrazie przeskalowanym
        relative_mouse_position_x = (event.x - (self.width-self.resized_image_width)/2)/self.resized_image_width
        relative_mouse_position_y = (event.y - (self.height-self.resized_image_height)/2)/self.resized_image_height

        # bezwzględna pozycja myszy na obrazie orginalnym
        absolut_mouse_position_x = relative_mouse_position_x * self.orginal_image_width
        absolut_mouse_position_y = relative_mouse_position_y * self.orginal_image_height

        if 0 < absolut_mouse_position_x < self.orginal_image_width and 0 < absolut_mouse_position_y < self.orginal_image_height:
            manager.swich_id = uuid4()
            manager.set_brakout_point(absolut_mouse_position_x, 
                                      absolut_mouse_position_y)

        manager.scale.set(manager.frame_to_display)

    def _on_mousewheel(self, event):

        if event.delta<0:
            manager.frame_cnt_change(-5)
        elif event.delta>0:
            manager.frame_cnt_change(+5)
    
    def update_values(self, *_) -> None:

        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None:
            return
        self.delete_previous_image()
        self.resize_image()
        self.paste_image()

    def delete_previous_image(self) -> None:
        if self.image is None:
            return
        self.delete(self.image_id)
        self.image = self.image_id = None

    def resize_image(self) -> None:
        image_width, image_height = self.source_image.size
        width_ratio = self.width / image_width
        height_ratio = self.height / image_height
        ratio = min(width_ratio, height_ratio)

        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)
        scaled_image = self.source_image.resize((new_width, new_height))
        self.image = ImageTk.PhotoImage(scaled_image)

        self.resized_image_width = new_width
        self.resized_image_height = new_height

        self.orginal_image_width = image_width
        self.orginal_image_height = image_height

    def paste_image(self) -> None:
        self.image_id = self.create_image(
            self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:

        if not manager.clip_a.clip.image:
            return

        self.delete_previous_image()

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()


class Frame_right_top(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        #################################

        buttons_setup = [('load files',             manager.load_file,                          2, 2),
                         ('reload classes',         manager.reload_classes,                     0, 5),
                         ('count drawing times',    manager.count_drawing_times,                1, 5),
                         ('make clip',              manager.make_video_clip,                    0, 7),
                         ('save frame as jpg',      manager.save_frame,                         1, 7),
                         ('frame count -',          lambda: manager.frame_cnt_change(-1),       1, 9),
                         ('frame count +',          lambda: manager.frame_cnt_change(1),        1, 10),
                         ('bike rotation +1',       lambda : manager.bike_rotation_change(1),   0, 12),
                         ('bike rotation +5',       lambda : manager.bike_rotation_change(5),   1, 12),
                         ('bike rotation +10',      lambda : manager.bike_rotation_change(10),  2, 12),
                         ('set ang',                manager.set_ang,                            1, 13),
                         ('bike rotation -1',       lambda : manager.bike_rotation_change(-1),  0, 14),
                         ('bike rotation -5',       lambda : manager.bike_rotation_change(-5),  1, 14),
                         ('bike rotation -10',      lambda : manager.bike_rotation_change(-10), 2, 14),
                         ('image rotation +1',      lambda : manager.img_rotation_change(1),    1, 19),
                         ('image rotation -1',      lambda : manager.img_rotation_change(-1),   2, 19)]

        for text, command, row, column in buttons_setup:
            ttk.Button(self,
                       text=text,
                       command=command
                       ).grid(row=row,
                              column=column,
                              padx=5,
                              pady=5,
                              sticky='EWNS')

        #################################
        # do poprawy

        comboboxes_setups = [(manager.clip_a, manager.clip_a.combo_list_date,   manager.clip_a.date,    manager.set_dates_list_a,   0, 0),
                             (manager.clip_a, manager.clip_a.combo_list_time,   manager.clip_a.time,    manager.set_times_list_a,   1, 0),
                             (manager.clip_a, manager.clip_a.combo_list_count,  manager.clip_a.count,   manager.set_counts_list_a,  2, 0),
                             (manager.clip_b, manager.clip_a.combo_list_date,   manager.clip_b.date,    manager.set_dates_list_b,   0, 1),
                             (manager.clip_b, manager.clip_a.combo_list_time,   manager.clip_b.time,    manager.set_times_list_b,   1, 1),
                             (manager.clip_b, manager.clip_a.combo_list_count,  manager.clip_b.count,   manager.set_counts_list_b,  2, 1)]
        
        for  clip, combobox,  textvariable, postcommand, row, column  in comboboxes_setups:
            tmp = ttk.Combobox(self,
                                    width=15,
                                    textvariable=textvariable,
                                    postcommand=postcommand)
            tmp.grid(row=row, 
                     column=column, 
                     padx=5, 
                     pady=5)
            
            setattr(clip, 
                    combobox,
                    tmp)
            
        #################################
                
        labels_setup = [('speed factor :',      0, 16),
                        ('obstacle length :',   1, 16)]
        
        for text, row, column in labels_setup:
            ttk.Label(self,
                      text=text,
                      ).grid(row=row,
                             column=column,
                             padx=5,
                             pady=5,
                             sticky='ENS')
            
        #################################

        entrys_setup = [(manager.speed_factor,      0, 17),
                        (manager.obstacle_length,   1, 17)]

        for textvariable, row, column in entrys_setup:
            ttk.Entry(self,
                    textvariable=textvariable
                    ).grid(row=row, 
                           column=column, 
                           padx=5, 
                           pady=5, 
                           sticky='EWNS')
            
        #################################

        separators = [3, 6, 8, 11, 15, 18, 20]

        for separator_column in separators:
            ttk.Separator(self, 
                          orient='vertical'
                          ).grid(row=0,
                                 column=separator_column,
                                 rowspan=3,
                                 sticky='ns')

        #################################

        self.bind_all("<Return>", manager.update_values)


class Frame_right_bottom(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        manager.scale = ttk.Scale(self,
                                  orient='horizontal',
                                  command=manager.update_view)
        manager.scale.pack(side="top",
                           fill="x",
                           expand=False,
                           padx=0,
                           pady=5)

        manager.canvas = CanvasImage(self, 
                                     relief='sunken', 
                                     bd=2)
        manager.canvas.pack(expand=True, 
                            fill='both', 
                            padx=0, 
                            pady=5)


class Frame_left(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.create_widgets()

    def create_widgets(self):

        # tworzy switch do aktualizacji klatki po zmianie checkboxów,
        # zmienia się w lewym Frame, a funkcja zbindowana jest w canvie

        manager.checkboxes_changed = tk.BooleanVar()

        # obiekt zestawiający dane z lewej ramki - teksty do wyświetlenia i checkboxy oraz ich stan
        self.left_frame_widgets =manager.left_frame_widgets
        self.labels = self.left_frame_widgets.labels_to_display

        self.checkboxes_variables_a = {}
        self.checkboxes_variables_b = {}

        # rysowanie checkboxów z opisami. Checkboxy powstają na podstawie
        # labeli i są zestawiane na podstawie ich tekstu. Key = tekst labela

        for row_count, label in enumerate(self.labels, start=1):
            # dostosowuje nazwę do wyświetlenia - todo: dodać polskie tłumaczenia np.jako słownik
            text_to_display = label.replace(
                '_draw_state', '').replace('_', ' ').capitalize()

            if label != '':
                self.checkboxes_variables_a[label] = tk.IntVar()
                ttk.Checkbutton(self,
                                text='',
                                bootstyle="round-toggle",
                                variable=self.checkboxes_variables_a[label],
                                command=self.update_draws_states).grid(column=0,
                                                                       row=row_count,
                                                                       padx=(5,0))
                self.checkboxes_variables_b[label] = tk.IntVar()

                ttk.Checkbutton(self,
                                text=text_to_display,
                                bootstyle="round-toggle",
                                variable=self.checkboxes_variables_b[label],
                                command=self.update_draws_states).grid(column=1,
                                                                       row=row_count,
                                                                       sticky='W',
                                                                       padx=(0,5))
            else:
                ttk.Label(self, text=text_to_display).grid(column=0,
                                                           row=row_count)

        # ustalanie ich stanu checkboxów
        self.update_checkboxes_states()

    def update_checkboxes_states(self):

        # zaznacza checkboxy wg stanu z draw_states
        for checkbox_name, checkbox_variable in self.checkboxes_variables_a.items():
            checkbox_variable.set(getattr(manager.draws_states_a, checkbox_name))

        for checkbox_name, checkbox_variable in self.checkboxes_variables_b.items():
            checkbox_variable.set(getattr(manager.draws_states_b, checkbox_name))

    def update_draws_states(self):
        # aktualizuje obiekt draws_states wg stanu checkboksów i przeładowuje wyświetlaną klatkę
        for checkbox_name, checkbox_variable in self.checkboxes_variables_a.items():
            setattr(manager.draws_states_a, checkbox_name,
                    checkbox_variable.get())
        
        for checkbox_name, checkbox_variable in self.checkboxes_variables_b.items():
            setattr(manager.draws_states_b, checkbox_name,
                    checkbox_variable.get())
            
        # zmienia stan zmiennej dającej sygnal że stan chceckboxów sie zmienił
        
        manager.swich_id = uuid4()
        manager.checkboxes_changed.set(not manager.checkboxes_changed)


class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title('BikeJump Analyzer')

        # ustala styl widgetów
        style = tb.Style('minty')
            
        # ustala wymiary początkowe okna
        self.minsize(800, 600)

        # inicjuje obiety tkintera w managerze
        manager.init_tk_objects()

        # tworzy główne podokna
        self.frame_left = Frame_left(self)
        self.frame_right_top = Frame_right_top(self)
        self.frame_right_bottom = Frame_right_bottom(self)

        # umieszcza podokna w oknie głównym
        self.frame_left.pack(side='left', fill='both', expand=False)
        self.frame_right_top.pack(fill='both')
        self.frame_right_bottom.pack(fill='both', expand=True)


if __name__ == '__main__':
    # tworzy obiekt zarządzajacy całością
    manager = Manager()

    # tworzy główne okno
    window = Window()
    window.mainloop()
