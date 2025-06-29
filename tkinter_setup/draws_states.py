class DrawsStates:
    # ustala co ma być wyświetlane
    def __init__(self):

        #główna klatka
        self.main_frame_draw_state                      = True
        self.main_frame_raw_view_draw_state             = False
        self.main_frame_description                     = True

        # szkielet
        self.main_skeleton_draw_state                   = False
        self.main_skeleton_right_draw_state             = True
        self.main_skeleton_left_draw_state              = False

        # wykresy
        # kąty zgięcia
        self.right_knee_ang_chart_draw_state            = True
        self.right_hip_ang_chart_draw_state             = True
        self.right_elbow_ang_chart_draw_state           = False
        self.left_knee_ang_chart_draw_state             = False
        self.left_hip_ang_chart_draw_state              = False
        self.left_elbow_ang_chart_draw_state            = False

        # inne
        self.stack_reach_len_chart_draw_state           = False
        self.stack_reach_ang_chart_draw_state           = False
        self.speed_chart_draw_state                     = True

        # tło wykresów
        self.charts_background_draw_state               = True
        self.speed_factor_verification_draw_state       = False

        # opisy wykresów
        self.charts_descriptions_draw_state             = True

        # linia wiodąca pionowa, pomocnicza
        self.leading_line_draw_state                    = True

        # linie na głównej klatce
        self.trace_line_draw_state                      = True
        self.center_of_gravity_line_draw_state          = False

        self.brakout_point_draw_state                   = True

        #################################################
        # boczny widok - wycięta klatka
        self.side_frame_draw_state                      = False
        self.side_frame_background_draw_state           = True

        # szkielet na bocznym widoku
        self.side_skeleton_draw_state                   = False
        self.side_skeleton_right_draw_state             = True
        self.side_skeleton_left_draw_state              = False   

        # linia bazy kół na bocznym widoku
        self.side_wheel_base_line_draw_state            = True

        # pionowa linia wiodąca - głowa
        self.side_head_leading_line_draw_state          = True

