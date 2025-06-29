from uuid import uuid4
import cv2
import tkinter as tk

from models import Clip, Point
from tkinter_setup import DrawsStates, LeftFrameWidgets, ClipTkinterData, VideoFiles


class Manager:
    def __init__(self):

        self.clip_a = ClipTkinterData()

        self.frame_to_display = 0
        
        self.clip_b = ClipTkinterData()
        self.clip_b_clip_frame_to_display = 0
        self.swich_id = uuid4()

        # tworzy obiekt ze stanem pozycji do wyświetlenia
        self.draws_states_a = DrawsStates()
        self.draws_states_b = DrawsStates()

        # obiekt tworzony razem z Combobox w widgecie - nazwa pliku do stworzenia clipu
        self.date_a = None
        self.time_a = None
        self.count_a = None
        self.date_b = None
        self.time_b = None
        self.count_b = None
        self.file_a_to_load = None
        self.file_b_to_load = None

        self.rotation_angle = None

        # obiekty tworzone po stworzeniu głównego okna:

        # lewe okno 
        self.left_frame_widgets = LeftFrameWidgets()
 
        # switch do kontroli checkboxów
        self.checkboxes_changed = None

        # suwak
        self.scale = None

        # głowny obraz do wyświetlania
        self.canvas = None

        # manager plików
        self.avilable_files = VideoFiles()

        # listy rozwijane
        self.avilable_files.get_dates()
        self.files = self.avilable_files.dropdown_list_dates
        self.combo_list_date_a = None
        self.combo_list_time_a = None
        self.combo_list_count_a = None

        self.combo_list_date_b = None
        self.combo_list_time_b = None
        self.combo_list_count_b = None

        self.speed_factor = None
        self.obstacle_length = None

    def init_tk_objects(self):
        self.clip_a.init_tk_objects()
        self.clip_b.init_tk_objects()

        self.speed_factor = tk.IntVar()
        self.obstacle_length = tk.IntVar()


        # do usunięcia
        # **********************************
        self.clip_a.date.set("2025-02-09")
        self.clip_a.time.set("13:25:12")
        self.clip_a.count.set("003")

        self.clip_b.date.set("2025-03-12")
        self.clip_b.time.set("14:38:46")
        self.clip_b.count.set("005")
        # **********************************

    def frame_cnt_change(self, amount):

        self.frame_to_display += amount
        self.frame_to_display = min(
            self.frame_to_display, 
            self.clip_a.clip.scale_range_max)
        self.frame_to_display = max(
            self.frame_to_display, 
            self.clip_a.clip.scale_range_min)
        self.scale.set(self.frame_to_display)

    def count_drawing_times(self):

        self.frame_cnt_change(1)
        self.clip_a.draw_times_table_in_terminal()

    def load_file(self):

        for clip in (self.clip_a, self.clip_b):

            if clip.date.get() in ("Select file number",'-'):
                break  

            elif clip.date.get() == 'unclassified':            
                video_file = self.avilable_files.dropdown_lists_data['unclassified'][clip.time.get()]
            else:
                if not clip.handy_files_dict:
                    self.set_counts_list_a()
                    self.set_counts_list_b()
                video_file = clip.handy_files_dict[clip.count.get()]


            self.filename = video_file.name

            self.load_path = video_file.file_path
            
            clip.clip=Clip(self.filename, self.load_path)



        # do zmiany
        self.speed_factor.set(self.clip_a.clip.speed_factor)
        self.obstacle_length.set(self.clip_a.clip.obstacle_length)

        self.calc_scale_range()
        self.scale.set(self.clip_a.clip.scale_range_min)

        self.clip_b.clip.compare_clip = True

    def calc_scale_range(self):

        self.scale_from = self.clip_a.clip.scale_range_min
        self.scale_to = self.clip_a.clip.scale_range_max

        self.scale.config(from_=self.scale_from)
        self.scale.config(to=self.scale_to)

    def bike_rotation_change(self, amount):
        self.swich_id = uuid4()
        self.clip_a.clip.frames[self.frame_to_display].bike_rotation += amount
        self.update_view()
        self.scale.set(self.frame_to_display)  # po co to? do kontroli

    def img_rotation_change(self, amount):
        self.swich_id = uuid4()
        self.clip_b.clip.rotation_angle += amount
        self.update_view()
        self.scale.set(self.frame_to_display)  # po co to? do kontroli

    def set_ang(self):
        self.clip_a.bike_ang_cor.append((self.frame_to_display,
                                          self.clip_a.frames[self.frame_to_display].bike_rotation))

    def save_frame(self):
        self.clip_a.clip.save_frame(self.frame_to_display)

    def set_dates_list_a(self):

        self.clip_a.combo_list_date['values'] = self.avilable_files.dropdown_list_dates

        self.clip_a.combo_list_count['values'] = []

        self.clip_a.time.set("Select time")
        self.clip_a.count.set("Select file number")

    def set_times_list_a(self):

        try:
            self.avilable_files.get_times(self.clip_a.date.get())
            self.clip_a.combo_list_time['values'] = self.avilable_files.dropdown_list_times
            self.clip_a.count.set("Select file number")
        except:
            print('błąd przy pobieraniu czasów')

    def set_counts_list_a(self):
        try:
            self.avilable_files.get_counts_a(self.clip_a.date.get(), self.clip_a.time.get())
            self.clip_a.combo_list_count['values'] = self.avilable_files.dropdown_list_counts_a

            self.clip_a.handy_files_dict = self.avilable_files.make_handy_files_dict(self.clip_a.date.get(), 
                                                                                     self.clip_a.time.get(),
                                                                                     self.avilable_files.dropdown_list_counts_a)
            pass
        except:
            print('błąd przy pobieraniu liczników a')

    def set_dates_list_b(self):

        self.clip_b.combo_list_date['values'] = self.avilable_files.dropdown_list_dates

        self.clip_b.combo_list_count['values'] = []

        self.clip_b.time.set("Select time")
        self.clip_b.count.set("Select file number")

    def set_times_list_b(self):

        try:
            self.avilable_files.get_times(self.clip_b.date.get())
            self.clip_b.combo_list_time['values'] = self.avilable_files.dropdown_list_times
            self.clip_b.count.set("Select file number")
        except:
            print('błąd przy pobieraniu czasów')

    def set_counts_list_b(self):

        try:
            self.avilable_files.get_counts_b(self.clip_b.date.get(), self.clip_b.time.get())
            self.clip_b.combo_list_count['values'] = self.avilable_files.dropdown_list_counts_b            
            self.clip_b.handy_files_dict = self.avilable_files.make_handy_files_dict(self.clip_b.date.get(), 
                                                                                    self.clip_b.time.get(),
                                                                                    self.avilable_files.dropdown_list_counts_b)  

        except:
            print('błąd przy pobieraniu liczników b')

    def set_compare_counts_list(self):

        try:
            self.avilable_files.get_counts_b(self.date_a.get(), self.time_a.get())
            self.combo_list_compare_count['values'] = self.avilable_files.dropdown_list_counts
        except:
            print('błąd przy pobieraniu liczników pliku do porównania')

    def reload_classes(self):

        print('napraw mnie')

        # importlib.reload(classes)
        # self.load_file()

    def update_view(self, *_) -> None:

        # jeśli pierwszy przekazany argument jest liczbą - to przyjmuje że to numer klatki
        try:
            self.frame_to_display = int(float(_[0]))
        except:
            pass

        self.make_source_image()

        self.canvas.source_image = self.source_image

        self.canvas.open_image()

    def set_brakout_point(self, x, y):

        self.clip_a.clip.brakout_point = Point(x, y)
        self.clip_a.clip.calc_max_jump_height()
        self.update_view(self.frame_to_display)
        self.clip_a.clip.save_brakout_point()

    def update_values(self, event):

        self.clip_a.clip.speed_factor = self.speed_factor.get()
        self.clip_a.clip.obstacle_length = self.obstacle_length.get()
        self.clip_a.clip.charts['speed_chart'].speed_factor = self.clip_a.clip.speed_factor
        self.clip_a.clip.charts['speed_chart'].calc_min_max()
        self.clip_a.clip.calc_max_jump_height()
        self.swich_id = uuid4()
        self.scale.set(self.frame_to_display)

    def make_source_image(self):

        try:
            x_offset = self.clip_a.clip.brakout_point.x_disp - self.clip_b.clip.brakout_point.x_disp
            y_offset = self.clip_a.clip.brakout_point.y_disp - self.clip_b.clip.brakout_point.y_disp
            frame_number_shift = self.clip_b.clip.brakout_point_frame - self.clip_a.clip.brakout_point_frame
        except:
            x_offset, y_offset = 0, 0

        if self.draws_states_a.main_frame_draw_state == True and self.draws_states_b.main_frame_draw_state == False:
            self.clip_a.clip.display_frame(frame_number = self.frame_to_display,
                                         draws_states = self.draws_states_a,
                                         compare_clip = None,
                                         swich_id = self.swich_id)
            self.source_image = self.clip_a.clip.image
            self.montage_clip_image = self.clip_a.clip.montage_clip_image


        if self.draws_states_a.main_frame_draw_state == False and self.draws_states_b.main_frame_draw_state == True:
            self.clip_b.clip.display_frame(frame_number = self.frame_to_display + frame_number_shift,
                                         draws_states = self.draws_states_b,
                                         compare_clip = None,
                                         swich_id = self.swich_id,
                                         x_offset = x_offset,
                                         y_offset = y_offset)
            self.source_image = self.clip_b.clip.image
            self.montage_clip_image = self.clip_b.clip.montage_clip_image

        if self.draws_states_a.main_frame_draw_state == True and self.draws_states_b.main_frame_draw_state == True:
            self.clip_a.clip.display_frame(frame_number = self.frame_to_display,
                                         draws_states = self.draws_states_a,
                                         compare_clip = self.clip_b.clip,
                                         swich_id = self.swich_id)
            self.source_image = self.clip_a.clip.image
            self.montage_clip_image = self.clip_a.clip.montage_clip_image

    def make_video_clip(self):

        output_folder = "_clips"

        output_video_clip_file = "{}\\{}".format(
            output_folder, self.clip_a.clip.name.replace(".mp4", "_analized.mp4")
        )

        out = cv2.VideoWriter(
            output_video_clip_file, cv2.VideoWriter_fourcc(*"mp4v"), 30, (1920, 1080)
        )

        start_frame = max(self.scale_from-5, 0)
        # do zmiany żeby uwzględniało clip_b 
        end_frame = min(self.scale_to+6, self.clip_a.clip.frames_amount)


        for frame_number in range(start_frame, end_frame):

            self.frame_to_display = frame_number

            self.make_source_image()
            # self.save_frame()

            out.write(self.montage_clip_image)  # writing the video frame

        import time
        time.sleep(20)

        # file_from = f'{os.getcwd()}\\{output_video_clip_file}'
        # file_to = file_from.replace('.mp4','_60fps.mp4')

        # print(file_from)
        # print(file_to)
        # print(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")

        # os.system(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")

        print(f"{self.clip_a.clip.name} gotowe.")   
        self.frame_to_display = 0

