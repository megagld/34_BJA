import numpy as np
import cv2
import json
import time
import copy
from tabulate import tabulate
from PIL import Image
from unidecode import unidecode
import os

from utils.general import draw_line, transform_point, letterbox_calc
from .frame import Frame
from .chart import Chart
from .line import Line
from .point import Point


class Clip:
    def __init__(self, vid_name, file_path):

        self.name           = vid_name
        self.vid_path       = file_path
        self.kpts_json_path = f"{os.getcwd()}\\_analysed\\{self.name.replace('.mp4','_kpts.json')}"

        self.cap = cv2.VideoCapture(self.vid_path)

        self.compare_clip   = False

        self.draws_times = []

        # dane do korekty pozycji x y punktów - ze wzgledu na zmianę formatu video do rozpoznawania "letterbox"

        self.left_ofset = 0
        self.top_offset = 0
        self.frame_offsets = self.left_ofset, self.top_offset
        self.calc_frame_offset()

        # ustalenie współczynnika wysokości obrazu (wg rozdzielczości) - bazowy to 1080p
        self.frame_height = None
        self.frame_hight_factor = None
        self.calc_frame_hight_factor()

        self.rotation_angle = 0

        # zestawia wszyskie klatki clipu

        self.frames = {}
        self.colect_frames()

        self.frames_amount = len(self.frames)

        # współczynnik długość w pikselach/metry  - do obliczania prędkości

        self.speed_factor =139
    
        # 139 - dobry na pierwszy stolik- zweryfikowane
        # 170 - dorn 
        # 148  -  wartość przyjmowana do 03.2025  dla pierwszego stolika
        # 180px = 1,22m = 147,5 - pierwszy stolik

        self.obstacle_length = 470 # [cm]

        self.max_speed = 0
        self.brakout_point = None
        self.max_jump_height = None
        self.max_jump_height_point = None
        self.brakout_point_frame = None

        self.read_brakout_point()
        self.calk_brakout_point_frame()

        # aktualizuje klatki o obiekty poprzedzajace i generuje dane o prędkości

        self.update_frames()

        # dane do wykresów i linii
        self.avilable_charts = {
            "speed_chart": {
                "chart_description": "speed [km/h]",
                "range_min": 15,
                "range_max": 45,
                "reverse": False,
                "base_scale":2,
                "smoothed":True
            },
            "right_knee_ang_chart": {
                "chart_description": "right knee ang. [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "left_knee_ang_chart": {
                "chart_description": "left knee ang. [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "right_hip_ang_chart": {
                "chart_description": "right hip ang. [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "left_hip_ang_chart": {
                "chart_description": "left hip ang. [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "right_elbow_ang_chart": {
                "chart_description": "right elbow ang. [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "left_elbow_ang_chart": {
                "chart_description": "left elbow ang. [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "stack_reach_len_chart": {
                "chart_description": "stack/reach dist. [m]",
                "range_min": 50,
                "range_max": 120,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "stack_reach_ang_chart": {
                "chart_description": "stack/reach ang. [st.]",
                "range_min": 0,
                "range_max": 90,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            }
        }
        self.charts = {}
        self.generate_charts_data()
        
        self.bike_ang_cor = []

        self.avilable_lines = {
            "trace_line": {
                "line_description": "linia trasy",
                "frame_atr": 'trace_point',
                'line_color': (56, 231, 255)
            },
            "center_of_gravity_line": {
                "line_description": "inia środka ciężkości",
                "frame_atr": 'center_of_gravity',
                'line_color': (56, 231, 255)
            },
        }
        self.lines = {}
        self.generate_lines_data()
        self.calc_max_jump_height()

        # ustala zakres dla widgetu Scale

        self.scale_range_min = 0
        self.scale_range_max = self.frames_amount-1
        self.calculate_scale_range()

    def add_time_counter(self, description):
        self.draws_times.append([description,time.time()])

    def calculate_scale_range(self):
        # zakres suwaka ma być od pierwszej do ostaniej klatki na której jest wykryty szkielet
        self.scale_range_min = min(i for i,j in self.frames.items() if j.detected)
        self.scale_range_max = max(i for i,j in self.frames.items() if j.detected)

    def calc_frame_offset(self):

        self.cap.set(0, 1)
        _, img = self.cap.read()
        frame_width = int(self.cap.get(3))

        self.left_ofset, self.top_offset = letterbox_calc(img, 
                                                          (frame_width), 
                                                          stride=64, 
                                                          auto=True)

    def calc_frame_hight_factor(self):

        self.cap.set(0, 1)
        self.frame_height = int(self.cap.get(4))
        self.frame_hight_factor = self.frame_height/1080

    def colect_frames(self):

        # zestawia klatki w słownik gdzie key=numer klatki (od 0) a value= obiekt klatki Frame

        with open(self.kpts_json_path, "r") as f:
            data = json.load(f)

        for frame_count, data in enumerate(data.items(),start=0):

            frame_time, kpts = data
            frame_time = float(frame_time)

            self.frames[frame_count] = Frame(frame_count,
                                             frame_time,
                                             kpts,
                                             self.frame_offsets)
            
        success,image = self.cap.read() 
        frame_count = 1
        while success:
            try:
                success,image = self.cap.read() 
                self.frames[frame_count].image = image
            except:
                print(str(frame_count)+" błąd")
            frame_count += 1

    def update_frames(self):
        for frame in self.frames.values():
            try:
                frame.previous_frame = self.frames[frame.frame_count-1]
                frame.speed_factor = self.speed_factor
                frame.calc_speed()

            except:
                pass
    
    def read_brakout_point(self):
        # parse json 
        _brakout_points_path = f"{os.getcwd()}\\_analysed\\_brakout_points.json"
        with open(_brakout_points_path, "r") as f:
            data = json.load(f)
        
        main_vid_name = self.name[:18]
        
        if main_vid_name in (data.keys()):
            x, y= data[main_vid_name]
            self.brakout_point = Point(x, y)

    def calk_brakout_point_frame(self):
        if not self.brakout_point:return
        previous_trace_point_x = 0
        for frame in self.frames.values():
            if frame.trace_point:
                if frame.trace_point.x>self.brakout_point.x:
                    interpolation_factor = (self.brakout_point.x-previous_trace_point_x)/(frame.trace_point.x - previous_trace_point_x)
                    self.brakout_point_frame = frame.frame_count - (interpolation_factor<0.5)
                    break
                previous_trace_point_x = frame.trace_point.x

    def save_brakout_point(self):
        main_vid_name = self.name[:18]
        _brakout_points_path = f"{os.getcwd()}\\_analysed\\_brakout_points.json"
        with open(_brakout_points_path, "r") as f:
            data = json.load(f)

        data[main_vid_name] = self.brakout_point.pos_disp

        with open(_brakout_points_path, 'w') as f:
            json.dump(data, f)
        
    def generate_charts_data(self):
        # tworzenie obiektu wykresu
        for chart_name, chart_setup in self.avilable_charts.items():

            # sam pusty obiekt i jego setup:
            self.charts[chart_name] = Chart(
                name=chart_name,
                chart_description=chart_setup["chart_description"],
                range_min=chart_setup["range_min"],
                range_max=chart_setup["range_max"],
                reverse=chart_setup["reverse"],
                base_scale=chart_setup["base_scale"],
                smoothed=chart_setup["smoothed"],
                )
            if chart_name == 'speed_chart':
                self.charts['speed_chart'].speed_factor= self.speed_factor
            # dodanie do wykresu punkty z kolejnych klatek:
            tmp_chart_points_dict   =   {}

            for frame_number, frame_obj in self.frames.items():
                if frame_obj.detected:  # jeśli szkielet został wykryty na klatce

                    # tworzenie nazwy zmiennej do pobrania z obiektu klatki
                    frame_variable_name = chart_name.replace("_chart", "")

                    x_pos = int(frame_obj.skeleton_points[17].x)
                    y_pos = int(getattr(frame_obj, frame_variable_name))

                    tmp_chart_points_dict[frame_number] = Point(x_pos, y_pos)

                else:
                    pass

            self.charts[chart_name].chart_points = tmp_chart_points_dict
        
            # generowanie danych wykresu

            if self.charts[chart_name].smoothed == True:
                self.charts[chart_name].generate_spline_data()

            # wykonanie kopii obiektów z punktami do wyświetlenia - żeby przyspieszyć generowanie dany później
            
            self.charts[chart_name].chart_points_to_draw = copy.deepcopy(self.charts[chart_name].chart_points)
            self.charts[chart_name].chart_points_smoothed_to_draw = copy.deepcopy(self.charts[chart_name].chart_points_smoothed)

    def draw_clip_to_compare(self, image, frame_number, compare_clip):
        if compare_clip == None: return

        try:
            frame_number = frame_number - self.brakout_point_frame + compare_clip.brakout_point_frame
            compare_image = copy.deepcopy(compare_clip.frames[frame_number].image)
        
            b_channel, g_channel, r_channel = cv2.split(compare_image)
            alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 100
            compare_image = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

            x_offset = self.brakout_point.x_disp - compare_clip.brakout_point.x_disp
            y_offset = self.brakout_point.y_disp - compare_clip.brakout_point.y_disp

            base_x, base_y = compare_clip.brakout_point.pos_disp

            compare_image = self.shift_image(compare_image,
                                      x_offset=x_offset,
                                      y_offset=y_offset,
                                      rotation_angle=compare_clip.rotation_angle,
                                      scale=1,
                                      base_x=base_x,
                                      base_y=base_y)
            
            self.add_transparent_image(image, compare_image)

        except:
            pass

    def add_transparent_image(self, background, foreground, x_offset=0, y_offset=0):

        # usunąć obracanie

        bg_h, bg_w, bg_channels = background.shape
        fg_h, fg_w, fg_channels = foreground.shape

        assert bg_channels == 3, f'background image should have exactly 3 channels (RGB). found:{bg_channels}'
        assert fg_channels == 4, f'foreground image should have exactly 4 channels (RGBA). found:{fg_channels}'

        # center by default
        # if x_offset is None: x_offset = (bg_w - fg_w) // 2
        # if y_offset is None: y_offset = (bg_h - fg_h) // 2 

        w = min(fg_w, bg_w, fg_w + x_offset, bg_w - x_offset)
        h = min(fg_h, bg_h, fg_h + y_offset, bg_h - y_offset)

        if w < 1 or h < 1: return

        # clip foreground and background images to the overlapping regions
        bg_x = max(0, x_offset)
        bg_y = max(0, y_offset)
        fg_x = max(0, x_offset * -1)
        fg_y = max(0, y_offset * -1)
        
        foreground = foreground[fg_y:fg_y + h, fg_x:fg_x + w]
        background_subsection = background[bg_y:bg_y + h, bg_x:bg_x + w]

        # separate alpha and color channels from the foreground image
        foreground_colors = foreground[:, :, :3]
        alpha_channel = foreground[:, :, 3] / 255  # 0-255 => 0.0-1.0

        # construct an alpha_mask that matches the image shape
        alpha_mask = alpha_channel[:, :, np.newaxis]

        # combine the background with the overlay image weighted by alpha
        composite = background_subsection * (1 - alpha_mask) + foreground_colors * alpha_mask

        # overwrite the section of the background image that has been updated
        background[bg_y:bg_y + h, bg_x:bg_x + w] = composite    

    def shift_image(self, 
                    image,  
                    x_offset = 0, 
                    y_offset = 0, 
                    rotation_angle = 0, 
                    scale = 1, 
                    base_x = 0, 
                    base_y = 0):

        # przesuń obraz
        rows, cols = image.shape[:2]
        M = np.float32([[1, 0, x_offset], [0, 1, y_offset]])
        image = cv2.warpAffine(image, M, (cols, rows))

        # obróć obraz i przeskaluj
        rotation_point = (base_x, base_y)
        rot_mat = cv2.getRotationMatrix2D(rotation_point, rotation_angle, scale)
        image = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)

        return image

    def draw_charts(self, image, draws_states, frame_number):

        # ustalenie które wykresy mają być wyświetlane na podstawie obiektu Draws_states
        # ustalenie ilości wykresów  i zestawienie obiektów wykresów
        

        charts_to_draw = []

        self.add_time_counter('czyszczenie listy wykresów')

        # iteracja po dostępnych obiektach wykresów i porównanie z obiektem stan druku 'draws_states'
        for chart_name in self.charts.keys():
            chart_name_draw_state_atr = chart_name+'_draw_state'
            if getattr(draws_states, chart_name_draw_state_atr) == True:
                charts_to_draw.append(self.charts[chart_name])

        if not charts_to_draw: return

        self.add_time_counter('iteracja po wykresach')

        # generowanie danych wykresów

        # oblicznie pozycji y pierwszego wykresu
        charts_area_height = 0
        for chart in charts_to_draw:
            charts_area_height += (chart.range_max - chart.range_min) * self.frame_hight_factor * chart.base_scale

        charts_y_pos = self.frame_height - int(charts_area_height)

        # generowanie danych wykresów dla konkretnych miejsc na obrazie

        for chart in charts_to_draw:

            chart.chart_y_pos = charts_y_pos
            chart.scale_factor = self.frame_hight_factor
            chart.chart_height = (chart.range_max - chart.range_min) * int(self.frame_hight_factor) * chart.base_scale

            chart.generate_line_to_draw(chart.chart_points,
                                        chart.chart_points_to_draw)

            charts_y_pos += chart.chart_height

        self.add_time_counter('generowanie danych wykresów')

        # rysowanie bazy i linii ograniczajacych wykres

        if draws_states.charts_background_draw_state == True:

            for chart in charts_to_draw:

                self.draw_charts_base(image, chart)

        self.add_time_counter('rysowanie bazy i lini ograniczajach')

        # rysowanie linii wykresów

        for chart in charts_to_draw:

            if chart.smoothed == False:
                # setup
                line_thickness = int(2 * self.frame_hight_factor)
                line_color = (255, 128, 0)
            else:
                # setup
                line_thickness = int(1 * self.frame_hight_factor)
                line_color = (80, 80, 80)

            draw_line(image, chart.chart_points_to_draw, color=line_color, thickness=line_thickness)

        self.add_time_counter('rysowanie linii wykresów')

        # rysowanie spline wykresów - tylko dla prędkości !!!! - test

        if draws_states.speed_chart_draw_state == True:

            self.add_time_counter('przed generuje dane do krzywej')
        
            # generuje dane wygładzonej krzywej wykresu
            self.charts['speed_chart'].generate_smoothed_line_to_draw()

            self.add_time_counter('po generuje dane do krzywej')

            # self.charts['speed_chart'].generate_line_to_draw(self.charts['speed_chart'].chart_points_smoothed)
            line_to_draw = self.charts['speed_chart'].chart_points_smoothed_to_draw

            self.add_time_counter('rysowanie linii wykresów')

            # setup
            line_thickness = 2
            line_color = (255, 128, 0)

            draw_line(image, line_to_draw, color=line_color, thickness=line_thickness)

        self.add_time_counter('rysowanie linii spline speed')
            
        # rysowanie opisów

        if draws_states.charts_descriptions_draw_state == True:

            for chart in charts_to_draw:

                self.draw_charts_descriptions(image, chart, frame_number)

        self.add_time_counter('rysowanie opisów')
            
         

        # rysowanie spline wykresów


        # for chart_number, chart in enumerate(charts_to_draw):

        #     chart.generate_spline_data(chart.chart_y_pos, chart_number)
        #     spline_to_draw = chart.chart_spline

        #     # setup
        #     line_thickness = 2
        #     line_color = (255, 128, 0)

        #     (image, spline_to_draw, color=line_color, thickness=line_thickness)
        
    def generate_lines_data(self):

        # tworzenie obiektu lini
        for line_name, line_setup in self.avilable_lines.items():
            # sam pusty obiekt i jego setup:
            self.lines[line_name] = Line(
                name=line_name,
                line_description = line_setup["line_description"],
                color = line_setup["line_color"]
            )

            # dodanje do lini punkty z kolejnych klatek:
            tmp_line_points_dict = {}

            for frame_number, frame_obj in self.frames.items():
                if frame_obj.detected:  # jeśli szkielet został wykryty na klatce

                    # tworzenie nazwy zmiennej do pobrania z obiektu klatki
                    frame_variable_name = line_setup["frame_atr"]

                    x_pos = int(frame_obj.skeleton_points[17].x)
                    y_pos = int(getattr(frame_obj, frame_variable_name).y)

                    tmp_line_points_dict[frame_number] = Point(x_pos, y_pos)

                else:
                    pass

            self.lines[line_name].line_points = tmp_line_points_dict
           
            # wykonanie kopii obiektów z punktami do wyświetlenia - żeby przyspieszyć generowanie dany później
            
            self.lines[line_name].line_points_to_draw = copy.deepcopy(self.lines[line_name].line_points)
            self.lines[line_name].line_points_to_draw_to_draw = copy.deepcopy(self.lines[line_name].line_points_to_draw)

    def draw_brakout_point(self, image, draws_states):
        if self.brakout_point:
            # setup
            radius = 20
            thickness = 2
            color = (0, 0, 0)
            cross_size = radius * 0.75

            # współrzędne krzyża
            cross_x_start = transform_point(self.brakout_point, -cross_size, 0)
            cross_x_end   = transform_point(self.brakout_point,  cross_size, 0)

            cross_y_start = transform_point(self.brakout_point, 0, -cross_size)
            cross_y_end   = transform_point(self.brakout_point, 0,  cross_size)

            cross_hor = [cross_x_start, cross_x_end]
            cross_vert = [cross_y_start, cross_y_end]

            # rysowanie na image
            cv2.circle(image, self.brakout_point.pos_disp, radius, color=color, thickness=thickness) 
            draw_line(image, cross_hor, color=color, thickness= thickness)
            draw_line(image, cross_vert, color=color, thickness= thickness)

    def draw_speed_factor_verification(self, image):
        # rysowanie na image sprawdzanie poprawnośći przyjętego wsp. piksele-centymetry
        # setup
        thickness = 2
        color = (56, 231, 255)
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8 * self.frame_hight_factor
        text_color = (56, 231, 255)

        delta = self.speed_factor * self.obstacle_length / 100
        start_point = self.brakout_point.pos_disp
        end_point = transform_point(self.brakout_point, delta, 0).pos_disp


        cv2.arrowedLine(image, start_point, end_point, color=color, thickness=thickness, tipLength = .025) 
        cv2.arrowedLine(image, end_point, start_point, color=color, thickness=thickness, tipLength = .025) 
        text = str(int(self.obstacle_length)) + ' cm'
        description_loc = (int(self.brakout_point.x_disp+delta/2-50),
                           self.brakout_point.y_disp + 25)
        cv2.putText(
            image,
            text,
            description_loc,
            font,
            fontScale,
            text_color,
            thickness,
        )
        # rysowanie wymiarów max skoku
        start_point = self.max_jump_height_point.pos_disp
        end_point = transform_point(self.max_jump_height_point, 0, self.max_jump_height_px)
        end_point = end_point.pos_disp


        cv2.arrowedLine(image, start_point, end_point, color=color, thickness=thickness, tipLength = .1) 
        cv2.arrowedLine(image, end_point, start_point, color=color, thickness=thickness, tipLength = .1) 
        
        text = str(self.max_jump_height) + ' cm'
        description_loc = (self.max_jump_height_point.x_disp + 10,
                           int(self.max_jump_height_point.y + self.max_jump_height_px/2)+20)
        cv2.putText(
            image,
            text,
            description_loc,
            font,
            fontScale,
            text_color,
            thickness,
        )

    def calc_max_jump_height(self):
        # ustalenie max wysokości skoku
        if self.brakout_point != None:
            self.max_jump_height_point = [point for point in self.lines["trace_line"].line_points.values() if point.y == min(point.y for point in self.lines["trace_line"].line_points.values())][0]

            self.max_jump_height_px = self.brakout_point.y - self.max_jump_height_point.y
            self.max_jump_height = int(self.max_jump_height_px / self.speed_factor * 100)
        else:
            self.max_jump_height = '-'

    def calc_speeds(self):
        
        try:
            self.max_speed = round(self.charts['speed_chart'].max_val)
            self.min_speed = round(self.charts['speed_chart'].min_val)
            self.delta = self.max_speed - self.min_speed

        except:
            self.max_speed = '-'
            self.min_speed = '-'
            self.delta = '-'

    def draw_charts_base(self, image, chart):

        # rysowanie tła wykresu
        # ustalenie współrzędnych punktów wykresu
        x, y, w, h = (
            0,
            chart.chart_y_pos,
            image.shape[1],
            chart.chart_height,
        )
        sub_img = image[y : y + h, x : x + w]
        white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255

        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

        # Putting the image back to its position
        image[y : y + h, x : x + w] = res

        # rysowanie linii ograniczajacych wykres
        # setup
        chart_frame_color = (0, 0, 0)
        chart_frame_thickness = int(2 * chart.scale_factor)

        for line_numer in range(2):

            pos_1 = Point(0, chart.chart_y_pos + line_numer * chart.chart_height)
            pos_2 = Point(w, chart.chart_y_pos + line_numer * chart.chart_height)

            line_to_draw = [pos_1, pos_2]

            draw_line(image, line_to_draw, chart_frame_color, thickness=chart_frame_thickness)

    def draw_charts_descriptions(self, image, chart, frame_number):

        # opis wykresu

        # setup
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8 * self.frame_hight_factor
        text_color = (0, 0, 0)
        thickness = int(2 * self.frame_hight_factor)

        # ustalenie tekstu głównego opisu do wyświetlenia i jego pozycji
        # - do zmiany tak żeby się wyświetlały polskie znaki

        main_description = unidecode(chart.chart_description)

        x_pos = int(20 * self.frame_hight_factor)
        y_pos = chart.chart_y_pos + int(25 * self.frame_hight_factor)

        main_description_loc = (x_pos, y_pos)

        cv2.putText(
            image,
            main_description,
            main_description_loc,
            font,
            fontScale,
            text_color,
            thickness,
        )

        # opisy, tylko jeśli na ekranie jest wykryty szkielet tj. obiekt chart ma dane dla klatki
        # jeśli wykres jest wygładzony to opis wg chart_points_smoothed

        try:
            x_pos = int(chart.chart_points[frame_number].x) + int(20 * self.frame_hight_factor)
            y_pos = chart.chart_y_pos + chart.chart_height - int(20 * self.frame_hight_factor)

            if chart.smoothed == True:
                
                for point in chart.chart_points_smoothed:
                    if int(point.x) == int(self.frames[frame_number].trace_point.x):
                        chart_value_description = point.y
                        break

            else:
                chart_value_description = chart.chart_points[frame_number].y


            if chart.speed_factor != None:
                chart_value_description /= chart.speed_factor

            chart_value_description = str(round(chart_value_description))


            chart_value_description_loc = (x_pos, y_pos)

            cv2.putText(
                image,
                chart_value_description,
                chart_value_description_loc,
                font,
                fontScale,
                text_color,
                thickness,
            )

        except:
            pass

    def draw_lines(self, image, draws_states):

        # ustalenie które linie mają być wyświetlane na podstawie obiektu Draws_states
        # ustalenie ilości lini  i zestawienie obiektów wykresów

        # iteracja po dostępnych obiektach lini i porównanie z obiektem stan druku 'draws_states'
        for line_name, line in self.lines.items():
            line_name_draw_state_atr = line_name + '_draw_state'
            if getattr(draws_states, line_name_draw_state_atr) == True:

                # line.line_points_to_draw = line.generate_line_to_draw(line.line_points)
                line_to_draw = line.line_points_to_draw

                # setup
                line_thickness = 2
                line_color = line.line_color

                draw_line(image, line_to_draw, color=line_color, thickness=line_thickness)

        # do analizy czy nie lepiej pokazać rzeczywistą odległość kostka- biodro, 
        # zamiast odległosci w pionie, bo na wykresie myli

    def draw_main_frame_description(self,image, frame):

        # setup
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8 * self.frame_hight_factor
        text_color = (56, 231, 255)
        text_color = (0, 0, 0)

        thickness = int(2 * self.frame_hight_factor)

        # ustalenie tekstu głównego opisu do wyświetlenia i jego pozycji
        # - do zmiany tak żeby się wyświetlały polskie znaki
        try:
            speed_dist = round(frame.speed_dist_px / self.speed_factor,3)
            speed_time = round(frame.speed_time,1)
        except:
            speed_dist = 0
            speed_time = 0

        self.calc_speeds()


        # main_description = [f'czas - {round(frame.frame_time)} [ms]',
        #                     f'klatka - {frame.frame_count}/{self.frames_amount}',
        #                     f'{speed_dist} [m]/{speed_time} [ms]',
        #                     f'V max/min - {self.max_speed}/{self.min_speed} [km/h]',
        #                     f'wsp. dlugosci - {self.speed_factor} [px/metr]'
        #                     ]

        main_description = ['{:04d} [ms] | {:03d}/{} | {:.3f} [m]/{} [ms] | {} [px/metr]'.format(
                                    round(frame.frame_time),
                                    frame.frame_count,
                                    self.frames_amount,
                                    speed_dist,
                                    speed_time,
                                    self.speed_factor),

                            f'V max/min/delta : {self.max_speed} / {self.min_speed} / {self.delta} [km/h] | jump height : {self.max_jump_height} [cm]'
                            ]

        # rysowanie podkładu
        x, y, w, h = (
            0,
            0,
            int(935 * self.frame_hight_factor),
            int(50 * len(main_description) * self.frame_hight_factor),
            )
        sub_img = image[y : y + h, x : x + w]
        white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255

        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

        # Putting the image back to its position
        image[y : y + h, x : x + w] = res

        for row, text in enumerate(main_description):

            x_pos = int(40 * self.frame_hight_factor)
            y_pos = int((40 + 50 * row) * self.frame_hight_factor)

            main_description_loc = (x_pos, y_pos)

            cv2.putText(
                image,
                text,
                main_description_loc,
                font,
                fontScale,
                text_color,
                thickness,
            )

    def draw_times_table_in_terminal(self):

        main_description = []
        
        reference_time = self.draws_times[0][1]*1000

        for data in self.draws_times:
            data+=[round(1000*(data[1])-reference_time,2)]
            main_description.append(f'{data[0]} - {data[2]} [ms]')
            reference_time  = 1000 * (data[1])

        start_time = self.draws_times[0][1]*1000
        end_time = self.draws_times[-1][1]*1000

        self.draws_times.append(['całość',',',round(end_time-start_time,2)])

        print(tabulate([[i[0],i[2]] for i in self.draws_times], showindex="always"))

        self.draws_times.pop(-1)

    def display_frame(self, frame_number, draws_states, compare_clip = None, swich_id=False, x_offset = 0, y_offset = 0):

        # jeżeli nie było zmiany swich_id to obraz zostaje pobrany z obiektu Frame,
        # jeżeli była zmiana - obraz jest tworzony, a potem zapisany do obiektu Frame

        # print(f'{frame_number} - {swich_id}/ {self.frames[frame_number].swich_id}')

        self.draws_times = []

        if  swich_id == self.frames[frame_number].swich_id:

            self.add_time_counter('start - to samo id')

            self.montage_clip_image = self.frames[frame_number].montage_clip_image
            self.image = self.frames[frame_number].image_to_draw

            self.add_time_counter('koniec - to samo id')

        else:

            self.frames[frame_number].swich_id = swich_id

            self.add_time_counter('start')

            image = copy.deepcopy(self.frames[frame_number].image)

            self.add_time_counter('kopia image')

            # rysowanie klipu do porównania
            # if draws_states.compare_clip_draw_state:
            if compare_clip != None:

                self.draw_clip_to_compare(image, frame_number, compare_clip)

            if draws_states.main_frame_raw_view_draw_state == False:
                # rysowenie widoku bocznego

                if draws_states.side_frame_draw_state:
                    self.frames[frame_number].draw_side_view(image, draws_states, self.frame_hight_factor)
                
                self.add_time_counter('rysowanie widoku bocznego')
                            
                # rysowanie punktu wybicia
                
                if draws_states.brakout_point_draw_state == True:
                    self.draw_brakout_point(image, draws_states)

                # rysowanie weryfikacji wsp. piksele - metry
                if draws_states.speed_factor_verification_draw_state:
                    self.draw_speed_factor_verification(image)

                # rysowanie lini trasy/ środek ciężkości itp.
                
                self.draw_lines(image, draws_states)
                self.add_time_counter('linie trasy')

                # rysowanie lini pomocniczej - wiodącej

                if draws_states.leading_line_draw_state == True:
                    self.frames[frame_number].draw_leading_line(image)
                
                self.add_time_counter('linia pomocnicza')

                # rysowanie szkieletów na głównym widoku
                if draws_states.main_skeleton_right_draw_state == True:
                    self.frames[frame_number].draw_skeleton_right(image)

                if draws_states.main_skeleton_left_draw_state == True:
                    self.frames[frame_number].draw_skeleton_left(image)

                if draws_states.main_skeleton_draw_state == True:
                    self.frames[frame_number].draw_skeleton(image)

                self.add_time_counter('szkielety na glownej')

                # rysowanie wykresów

                self.draw_charts(image, draws_states, frame_number)

                self.add_time_counter('wykresy')

                # rysowanie głównego opisu na ramce

                if draws_states.main_frame_description == True:
                    self.draw_main_frame_description(image, self.frames[frame_number])
                
                self.add_time_counter('opis glowny')

            # tworzenie ostatecznego obrazu

            # przesuwanie obrazu jeśli jest zadany offset
            if x_offset or y_offset:
                image = self.shift_image(image,
                                         x_offset=x_offset,
                                         y_offset=y_offset,
                                         rotation_angle=self.rotation_angle,
                                         scale=1,
                                         base_x=self.brakout_point.x_disp,
                                         base_y=self.brakout_point.y_disp)

            self.montage_clip_image = image

            self.cv2_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # convert frame to RGB

            self.image = Image.fromarray(self.cv2_image)

            self.frames[frame_number].montage_clip_image = self.montage_clip_image
            self.frames[frame_number].image_to_draw = self.image


            self.add_time_counter('obróbka ostatecznego obrazu')

    def save_frame(self, frame_to_display):

        output_folder = "_clips"

        output_frame_file = "{}\\{}_{:03d}.jpg".format(
            output_folder,
            self.name.replace(".mp4", ""),
            frame_to_display
        )
        print(output_frame_file)

        # self.display_frame(frame_to_display, draws_states)

        cv2.imwrite(output_frame_file, self.montage_clip_image)

        print(f"{self.name} gotowe.")
