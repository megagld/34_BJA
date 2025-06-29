class Point:
    def __init__(self, pos_x, pos_y, sk_id=None):
        self.sk_id = sk_id

        self.x = pos_x
        self.y = pos_y
        self.pos = (self.x, self.y)

        self.x_disp = int(self.x)
        self.y_disp = int(self.y)
        self.pos_disp   = (self.x_disp, self.y_disp)

    def disp_pos(self):
        return (int(self.x), int(self.y))