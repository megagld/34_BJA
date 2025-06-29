class Line:

    def __init__(
        self,
        name,
        line_description=None,
        color=(0,0,0)):

        # podstawowe dane ustawień wykresu
        self.name = name
        self.line_description = line_description
        self.line_color = color

        # dane lini
        self.line_points   =   None    # słownik z key = klatka clipu, value = Point (!)
        self.line_points_smoothed   =   None   # lista z Point

        self.max_val = None
        self.min_val = None

        # dane dla przyjętego obrazu
        self.scale_factor = None
        
        self.line_points_to_draw = None    
        self.line_points_smoothed_to_draw   =   None
