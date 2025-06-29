class Blender:
    def __init__(self, manager):
        self.canva = None
        self.clip_a = manager.clip_a
        self.clip_b = manager.clip_b
        self.draws_states_a = manager.draws_states_a
        self.draws_states_b = manager.draws_states_b
        self.frame_to_display = manager.frame_to_display
        self.clip_b_clip_frame_to_display = manager.clip_b_clip_frame_to_display
        self.swich_id = manager.swich_id
        self.rotation_angle = manager.rotation_angle

        self.source_image = None
        self.montage_clip_image = None

    def blend_clips(self):

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
            print('a')

        if self.draws_states_a.main_frame_draw_state == False and self.draws_states_b.main_frame_draw_state == True:
            self.clip_b.clip.display_frame(frame_number = self.frame_to_display + frame_number_shift,
                                         draws_states = self.draws_states_b,
                                         compare_clip = None,
                                         swich_id = self.swich_id,
                                         x_offset = x_offset,
                                         y_offset = y_offset)
            self.source_image = self.clip_b.clip.image
            self.montage_clip_image = self.clip_b.clip.montage_clip_image

            print('b')
            print(self.clip_b.rotation_angle)

        if self.draws_states_a.main_frame_draw_state == True and self.draws_states_b.main_frame_draw_state == True:
            self.clip_a.clip.display_frame(frame_number = self.frame_to_display,
                                         draws_states = self.draws_states_a,
                                         compare_clip = self.clip_b.clip,
                                         swich_id = self.swich_id)
            self.source_image = self.clip_a.clip.image
            self.montage_clip_image = self.clip_a.clip.montage_clip_image

            print(self.clip_b.clip.rotation_angle)
            print('ab')