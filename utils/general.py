import numpy as np
import math
import cv2

from models.point import Point


def letterbox_calc(img, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    # Resize and pad image while meeting stride-multiple constraints
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better test mAP)
        r = min(r, 1.0)

    # Compute padding

    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))

    return left, top

def angle_between_vectors(u, v):
    dot_product = sum(i * j for i, j in zip(u, v))
    norm_u = math.sqrt(sum(i**2 for i in u))
    norm_v = math.sqrt(sum(i**2 for i in v))
    cos_theta = dot_product / (norm_u * norm_v)
    angle_rad = math.acos(cos_theta)
    angle_deg = math.degrees(angle_rad)
    return angle_rad, angle_deg

def rotate_point(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin.x, origin.y
    px, py = point.x, point.y

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

    return Point(qx, qy)

def transform_point(origin, delta_x, delta_y):

    ox, oy = origin.x, origin.y

    qx = ox + delta_x
    qy = oy + delta_y

    return Point(qx, qy)

def get_dist(pkt_1, pkt_2):
    # zwraca dystans między dwoma punktami
    pos_x_1, pos_y_1 = pkt_1.x, pkt_1.y
    pos_x_2, pos_y_2 = pkt_2.x, pkt_2.y

    return ((pos_x_2 - pos_x_1) ** 2 + (pos_y_2 - pos_y_1) ** 2) ** 0.5

def get_mid(kpts, sk_id_1, sk_id_2):
    # zwraca punkt środkowy między dwoma punktami szkieletu
    steps = 3
    pos_x_1, pos_y_1 = (kpts[(sk_id_1 - 1) * steps]), (
                        kpts[(sk_id_1 - 1) * steps + 1])
    pos_x_2, pos_y_2 = (kpts[(sk_id_2 - 1) * steps]), (
                        kpts[(sk_id_2 - 1) * steps + 1] )

    return Point((pos_x_2 + pos_x_1) / 2, (pos_y_2 + pos_y_1) / 2)

def draw_line(image, line_to_draw, color=(0, 0, 0), thickness=3):

    if isinstance(line_to_draw, dict):     
        line_to_draw = [point for _,point in sorted(line_to_draw.items())]

    # rysowanie wykresu na podstawie listy punktów

    for x_axis_point in range(len(line_to_draw)-1):

        pos_1 = line_to_draw[x_axis_point]
        pos_2 = line_to_draw[x_axis_point+1]

        pos_1 = pos_1.disp_pos()             
        pos_2 = pos_2.disp_pos()      

        cv2.line(image, pos_1, pos_2, color, thickness)
     