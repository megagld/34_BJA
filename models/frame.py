import numpy as np
import cv2
import math

from utils import draw_line, transform_point, rotate_point, angle_between_vectors, get_dist
from .point import Point

class Frame:
    def __init__(self, frame_count, frame_time, kpts, frame_offsets):

        self.image              = None
        self.image_to_draw      = None
        self.montage_clip_image = None
        self.swich_id           = None

        self.frame_count        = frame_count
        self.frame_time         = frame_time
        self.kpts               = kpts
        self.detected           = kpts != []
        self.skeleton_points    = {}

        self.previous_frame     = None

        self.right_knee_ang     = None
        self.right_hip_ang      = None
        self.right_elbow_ang    = None

        self.left_knee_ang      = None
        self.left_hip_ang       = None
        self.left_elbow_ang     = None

        self.trace_point        = None
        self.center_of_gravity  = None
        self.center_of_bar      = None
        self.stack_reach_len    = None
        self.stack_reach_ang    = None
        self.bike_rotation      = None
        self.speed              = 30 # w pikselach/h

        self.side_view_size     = None
        self.size_factor        = None

        # real bike geometry
        self.bike_reach_len       = 485
        self.bike_stack_len       = 645
        self.bike_stack_reach_len = (self.bike_reach_len**2+self.bike_stack_len**2)**0.5  # wprowadzić pomiar albo dopasować
        self.bike_stack_reach_ang = math.degrees(math.atan(self.bike_stack_len/self.bike_reach_len))  # wprowadzić pomiar albo dopasować

        self.bike_real_s_r_ang    = 10  #korekta kąta ze względu na to że pomiar dotyczy nie dokładnie reachu i stacku
        self.bike_stack_reach_ang+= self.bike_real_s_r_ang

        self.bike_chain_stay = 428  # wprowadzić pomiar albo dopasować
        self.bike_wheel_base = 1243  # wprowadzić pomiar albo dopasować
        self.bike_wheel_size = 27.5*25.4

        self.frame_offsets = frame_offsets
        self.left_ofset = -1 * self.frame_offsets[0]
        self.top_offset = -1 * self.frame_offsets[1]

        self.update_data()

    def update_data(self):
        if self.detected:

            # organizuje pomierzone punkty kpts w słownik gdzie key= id szkieletu, a value= obiekt Point
            self.organize_skeleton_points()

            # oblicza kąty między zadanymi punktami, zestawia je w zmiennych self.___.ang
            self.calc_ang()

            # DO ANALIZY CZY LEPIEJ DAĆ ŚRODEK MIĘDZY PUNKTAMI CZY PUNKTY Z JEDNEJ STRONY
            # skorygować o zmianę jeśli film jest nagrywany z lewej strony roweru
            # może dodać zmienną - info o kierunku poruszania sie roweru i na tej podstawie która strona jest nagrywana

            self.trace_point        = self.skeleton_points[17]
            self.center_of_gravity  = self.skeleton_points[13]
            self.center_of_bar      = self.skeleton_points[11]

            # self.trace_point = self.get_mid(self.kpts, 16, 17)
            # self.center_of_gravity = self.get_mid(self.kpts,12, 13)
            # self.center_of_bar = self.get_mid(self.kpts, 10, 11)

            self.stack_reach_len    = get_dist(self.trace_point, 
                                               self.center_of_bar)

            self.stack_reach_ang    = self.stack_reach_ang_calc(self.trace_point, 
                                                                self.center_of_bar)

            self.calc_bike_rotation()
            self.calc_side_view_size()
            self.calc_size_factor()

    def organize_skeleton_points(self):
        # tworzy słownik ze współrzędnymi punktów szkieletu
        # koryguje wspórzędne o to że rozpoznanie było na zmienionym formacie filmu - letterbox

        steps = 3
        for sk_id in range(1, 18):
            pos_x   =   (self.kpts[(sk_id - 1) * steps])     + self.left_ofset
            pos_y   =   (self.kpts[(sk_id - 1) * steps + 1]) + self.top_offset

            self.skeleton_points[sk_id] = Point(pos_x, 
                                                pos_y, 
                                                sk_id)

    def calc_speed(self):
        # odległość

        self.speed_dist_px = get_dist(self.trace_point, self.previous_frame.trace_point)

        # czas
        self.speed_time = self.frame_time - self.previous_frame.frame_time

        # prędkość
        self.speed = int((self.speed_dist_px/self.speed_time) * 3600)

    def calc_ang(self):
        # tworzy słownik z danymi do wykresów

        # punkty obliczenia kątów
        # wierzchołek kąta trzeba podać w środku listy (b)
        # kąty są mierzone do 180 st. (!)

        angs_list = {
            "right_knee_ang": [13, 15, 17],
            "left_knee_ang": [12, 14, 16],
            "right_hip_ang": [7, 13, 15],
            "left_hip_ang": [6, 12, 14],
            "right_elbow_ang": [7, 9, 11],
            "left_elbow_ang": [6, 8, 10],
        }

        for name, (a, b, c) in angs_list.items():

            # tworzenie wektorów:
            u = (
                self.skeleton_points[a].x - self.skeleton_points[b].x,
                self.skeleton_points[a].y - self.skeleton_points[b].y,
            )
            v = (
                self.skeleton_points[c].x - self.skeleton_points[b].x,
                self.skeleton_points[c].y - self.skeleton_points[b].y,
            )

            # obliczneie kąta miedzy wektorami
            calculated_ang = angle_between_vectors(u, v)[1]

            setattr(self, name, calculated_ang)

    def draw_skeleton(self, image, skeleton_to_display=None, points_to_display=None, delta_x=0, delta_y=0):

        if self.detected:

            # rysuje wybrany szkielet na zadanym obrazie

            # cały szkielet
            skeleton = [
                [16, 14],
                [14, 12],
                [17, 15],
                [15, 13],
                [12, 13],
                [6, 12],
                [7, 13],
                [6, 7],
                [6, 8],
                [7, 9],
                [8, 10],
                [9, 11],
                [2, 3],
                [1, 2],
                [1, 3],
                [2, 4],
                [3, 5],
                [4, 6],
                [5, 7],
            ]

            key_points = list(range(1, 18))

            # części szkieletu do wyświetlenia
            if not skeleton_to_display:
                skeleton_to_display = skeleton

            if not points_to_display:
                points_to_display = key_points

            # Plot the skeleton and keypointsfor coco datatset
            palette = np.array(
                [
                    [255, 128, 0],
                    [255, 153, 51],
                    [255, 178, 102],
                    [230, 230, 0],
                    [255, 153, 255],
                    [153, 204, 255],
                    [255, 102, 255],
                    [255, 51, 255],
                    [102, 178, 255],
                    [51, 153, 255],
                    [255, 153, 153],
                    [255, 102, 102],
                    [255, 51, 51],
                    [153, 255, 153],
                    [102, 255, 102],
                    [51, 255, 51],
                    [0, 255, 0],
                    [0, 0, 255],
                    [255, 0, 0],
                    [255, 255, 255],
                ]
            )

            pose_limb_color = palette[
                [0, 9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]
            ]
            pose_kpt_color = palette[
                [0, 16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]
            ]
            radius = 4

            for kid in key_points:
                r, g, b = pose_kpt_color[kid]

                # ustalenie wsp i przesunięcie punktów o delta_x delta_y
                x_coord, y_coord = (
                    self.skeleton_points[kid].x_disp + delta_x,
                    self.skeleton_points[kid].y_disp + delta_y,
                )

                if not (x_coord % 640 == 0 or y_coord % 640 == 0):
                    if kid in points_to_display:
                        cv2.circle(
                            image,
                            (x_coord, y_coord),
                            radius,
                            (int(r), int(g), int(b)),
                            -1,
                        )

            for sk_id, sk in enumerate(skeleton, 1):
                r, g, b = pose_limb_color[sk_id]

                # ustalenie wsp i przesunięcie punktów o delta_x delta_y

                pos1 = (
                    self.skeleton_points[sk[0]].x_disp + delta_x,
                    self.skeleton_points[sk[0]].y_disp + delta_y,
                )
                pos2 = (
                    self.skeleton_points[sk[1]].x_disp + delta_x,
                    self.skeleton_points[sk[1]].y_disp + delta_y,
                )

                if (
                    pos1[0] % 640 == 0
                    or pos1[1] % 640 == 0
                    or pos1[0] < 0
                    or pos1[1] < 0
                ):
                    continue
                if (
                    pos2[0] % 640 == 0
                    or pos2[1] % 640 == 0
                    or pos2[0] < 0
                    or pos2[1] < 0
                ):
                    continue
                if sk in skeleton_to_display:
                    cv2.line(image, pos1, pos2, (int(r), int(g), int(b)), thickness=2)

    def draw_skeleton_right(self, image, delta_x=0, delta_y=0):
        # rysuje prawą stronę szkieletu
        skeleton_right_side = [
            [17, 15],
            [15, 13],
            [7, 13],
            [7, 9],
            [9, 11],
            [5, 7],
            [3, 5],
            [1, 3],
        ]

        points_to_display = [1, 3, 5, 7, 9, 11, 13, 15, 17]

        self.draw_skeleton(image, skeleton_right_side, points_to_display, delta_x=delta_x, delta_y=delta_y)

    def draw_skeleton_left(self, image, delta_x=0, delta_y=0):
        # rysuje lewą stronę szkieletu

        skeleton_left_side = [
            [16, 14],
            [14, 12],
            [6, 12],
            [6, 8],
            [8, 10],
            [4, 6],
            [2, 4],
            [1, 2],
        ]

        points_to_display = [1, 2, 4, 6, 8, 10, 12, 14, 16]

        self.draw_skeleton(image, skeleton_left_side, points_to_display, delta_x=delta_x, delta_y=delta_y)

    def stack_reach_ang_calc(self, trace_point, center_of_bar):

        # pomiar kąta względem poziomu - przeciwnie do wskazówek zegara
        # tworzenie wektorów:

        u = (
            center_of_bar.x - trace_point.x,
            center_of_bar.y - trace_point.y,
        )
        v = (1, 0)

        ang_to_add = angle_between_vectors(u, v)[1]

        return ang_to_add

    def draw_side_view(self, image, draws_states, scale_factor=1):

        # restet wielkości okna - zostawić funkcję do rozbudowania o opcję zmieny z poziomu programu
        self.calc_side_view_size()

        # boczne okno może być wyświetlane tylko jeśli jest wykryty szkielet
        if self.detected:

            self.side_view_size = int(self.side_view_size * scale_factor)
            # określenie zakresu do wyświetlenia

            # ustalenie punktów wycinka
            pose_y_cor = 0
            x, y, w, h = (
                int(self.trace_point.x) - self.side_view_size,
                int(self.trace_point.y) - pose_y_cor - self.side_view_size,
                self.side_view_size * 2,
                self.side_view_size * 2
            )

            # określenie średnicy koła do wyświetlenia bocznego obrazu

            x_circle = image.shape[1]- self.side_view_size
            y_circle = self.side_view_size

            # obraz boczny

            # maska dla obrazu bocznego

            sub_mask_rect = np.ones(image.shape, dtype=np.uint8) * 0

            cv2.circle(sub_mask_rect,(x_circle,y_circle),self.side_view_size, (255,255,255),-1)

            if draws_states.side_frame_background_draw_state:

                # wycięcie obrazu bocznego z głównej klatki image

                if any((x < 0,
                    (x + self.side_view_size * 2) > image.shape[1],
                    y < 0,
                    (x + self.side_view_size * 2) > image.shape[1])):

                    sub_crop_rect = self.crop_extended(image, x, y, w, h)

                else:
                    sub_crop_rect = image[y : y + h,
                                        x : x + w].copy()
            else:
                sub_crop_rect = np.ones((w,h,3), dtype=np.uint8) * 0

            sub_rect = np.ones(image.shape, dtype=np.uint8) * 0

            # rysowanie elementów wg draws_states

            self.draw_side_view_items(sub_crop_rect, 
                                      draws_states, 
                                      delta_x = -1 * x, 
                                      delta_y = -1 * y)

            # obrót wycinka

            rot_res = cv2.getRotationMatrix2D((self.side_view_size,self.side_view_size), self.bike_rotation, 1)

            img_rot = cv2.warpAffine(sub_crop_rect,rot_res,(2*self.side_view_size,2*self.side_view_size))

            # wklejenie zdjęcia na boku na czarny podkład sub_rect

            x_place = image.shape[1]-2*self.side_view_size
            y_place = 0

            sub_rect[y_place : y_place + h, x_place : x_place + w] = img_rot

            # wycinanie bocznego rysunku wg maski

            result = np.where(sub_mask_rect==0, image, sub_rect)

            # wklejanie rezultatu na główny obraz

            x,y,_ = image.shape
            image[0:x, 0:y] = result

            # rysowanie ramki wokół bocznego rysunka

            cv2.circle(image,(x_circle,y_circle),self.side_view_size, (0,0,0),5)

    def crop_extended(self, image, x, y, w, h):

        sub_crop_rect = np.ones((2*self.side_view_size,2*self.side_view_size,3), dtype=np.uint8) * 0

        # rozszerzenie wycinka jeśli wychodzi poza zakres image na wartości ujemne lub poza rozmiar

        ext_x_min = x * (x < 0)
        ext_x_max = (image.shape[1] -(x + 2*self.side_view_size)) * ((x + self.side_view_size * 2) > image.shape[1])

        ext_y_min = y * (y < 0)
        ext_y_max = (image.shape[0] - (y + 2*self.side_view_size)) * ((y + self.side_view_size * 2) > image.shape[0])

        tmp_x = x - ext_x_min
        tmp_y = y - ext_y_min

        tmp_w = w + ext_x_min + ext_x_max
        tmp_h = h + ext_y_min + ext_y_max

        tmp_sub_crop_rect = image[tmp_y : tmp_y + tmp_h,
                                    tmp_x : tmp_x + tmp_w].copy()

        sub_crop_rect[-1 * ext_y_min : -1 * ext_y_min + tmp_h,
                        -1 * ext_x_min : -1 * ext_x_min + tmp_w] = tmp_sub_crop_rect

        return sub_crop_rect

    def calc_side_view_size(self):
        self.side_view_size=250  

    def calc_bike_rotation(self):
        self.bike_rotation = self.bike_stack_reach_ang - self.stack_reach_ang

    def calc_size_factor(self):
        # temat do ogarnięcia!!!!
        self.size_factor = 0.25
        # self.size_factor=self.stack_reach_len/self.bike_stack_reach_len

    def draw_side_view_items(self, sub_crop_rect, draws_states, delta_x=0, delta_y=0):

        if draws_states.side_wheel_base_line_draw_state:
            self.draw_wheelbase_line(sub_crop_rect, delta_x, delta_y)
        if draws_states.side_head_leading_line_draw_state:
            self.draw_head_leading_line(sub_crop_rect, delta_x, delta_y)
        if draws_states.side_skeleton_draw_state:
            self.draw_skeleton(sub_crop_rect, delta_x=delta_x, delta_y=delta_y)
        if draws_states.side_skeleton_right_draw_state:
            self.draw_skeleton_right(sub_crop_rect, delta_x=delta_x, delta_y=delta_y)
        if draws_states.side_skeleton_left_draw_state:
            self.draw_skeleton_left(sub_crop_rect, delta_x=delta_x, delta_y=delta_y)

    def draw_head_leading_line(self, image, delta_x=0, delta_y=0):

        if self.detected:

            # określenie wsp. punktu głowy

            crop_head_point = transform_point(self.skeleton_points[1], delta_x, delta_y)

            # oblicznie wsp. rzednych lini wiodoącej na wycinku
            x1 = x2 = crop_head_point.x
            y1 = 0
            y2 = image.shape[1]

            start_point = Point(x1, y1)
            end_point = Point(x2, y2)

            # obrót lini wiodocej wzgledem głowy o kąt obrotu roweru
            start_point = rotate_point(crop_head_point,
                                           start_point,
                                           math.radians(self.bike_rotation))
            end_point = rotate_point(crop_head_point,
                                         end_point,
                                         math.radians(self.bike_rotation))

            # rysuj linie wiodącą głowy

            line_to_draw = [start_point, end_point]

            draw_line(image, line_to_draw, color=(255, 4, 0), thickness=3)

    def draw_wheelbase_line(self, image, delta_x=0, delta_y=0):

        # dodać skalowanie o scale vector

        if self.detected:

            central_point           = self.trace_point
            center_of_back_wheel    = transform_point(central_point, -self.bike_chain_stay*self.size_factor, 0)
            center_of_front_wheel   = transform_point(central_point, (-self.bike_chain_stay+self.bike_wheel_base)*self.size_factor, 0)

            # obliczenie kąta obrotu roweru w stosunku do poziomu
            # wartość dodatnia oznacza obrót zgodnie z ruchem wskazówek zegara

            center_of_back_wheel=rotate_point(central_point, center_of_back_wheel, math.radians(self.bike_rotation))
            center_of_front_wheel=rotate_point(central_point, center_of_front_wheel, math.radians(self.bike_rotation))

            center_of_back_wheel=transform_point(center_of_back_wheel, delta_x, delta_y)
            center_of_front_wheel=transform_point(center_of_front_wheel, delta_x, delta_y)

            # rysuj linie bazy kół

            line_to_draw = [center_of_back_wheel, center_of_front_wheel]

            draw_line(image, line_to_draw, color=(255, 4, 0), thickness=3)

            # rysuje koła na końcu bazy kół

            # cv2.circle(image, center_of_back_wheel.disp, int(self.bike_wheel_size/2*self.size_factor), (0,0,0), thickness=2)
            # cv2.circle(image, center_of_front_wheel.disp, int(self.bike_wheel_size/2*self.size_factor), (0,0,0), thickness=2)

    def draw_leading_line(self, image):
        # rysowanie linie wiodącej dla klatki, jeśli w ogóle jest szkielet
        if self.detected:

            # leading line setup
            leading_line_color = (0, 0, 0)
            leading_line_thickness= 2

            pos_1 = Point(self.trace_point.x, 0)
            pos_2 = Point(self.trace_point.x, image.shape[0])

            line_to_draw = [pos_1,pos_2]

            draw_line(image, line_to_draw, color=leading_line_color, thickness=leading_line_thickness)
