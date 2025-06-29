import numpy as np
import time
from tabulate import tabulate

from .point import Point

class Chart:
    def __init__(self,
                 name,
                 chart_description = None,
                 range_min = None,
                 range_max = None,
                 reverse = None,
                 smoothed = None,
                 base_scale = 1):

        # podstawowe dane ustawień wykresu
        self.name = name
        self.chart_description = chart_description
        self.range_min = range_min
        self.range_max = range_max
        self.reverse = reverse
        self.base_scale = base_scale #przeskalowanie wartości wykresu przy wyświetlaniu (niezależna od rozdzielczości)
        self.smoothed = smoothed
        self.speed_factor = None

        # dane wykresu
        self.chart_points   =   None    # słownik z key = klatka clipu, value = Point (!)
        self.chart_points_smoothed   =   None   # lista z Point

        self.max_val = None
        self.min_val = None

        # dane dla przyjętego obrazu
        self.chart_y_pos = None
        self.chart_height = None
        self.scale_factor = None
        
        self.chart_points_to_draw = None    
        self.chart_points_smoothed_to_draw   =   None

        self.draws_times = []

    def generate_line_to_draw(self, source, target):
        
        if isinstance(target, dict):     

            for frame, point in target.items():
                # skalowanie wykresu
                point.y = source[frame].y * self.scale_factor * self.base_scale

                # jeżeli wprowadzono speed_factor - to do wartość do przeskalowania
                if self.speed_factor:
                    point.y /= self.speed_factor

                # redukcja do wartości minimalnej
                point.y = point.y - self.range_min * self.scale_factor * self.base_scale
                    
                # odwracanie wykresu
                if not self.reverse:
                    point.y = -1 * point.y + (self.range_max - self.range_min) * self.scale_factor * self.base_scale
                
                # ustalenie pozycji wykresu
                point.y = point.y + self.chart_y_pos

        else: # jeśli dane są w listach
            for source_point, target_point in zip(source, target):
                # skalowanie wykresu
                target_point.y = source_point.y * self.scale_factor * self.base_scale

                # jeżeli wprowadzono speed_factor - to do wartość do przeskalowania
                if self.speed_factor:
                    target_point.y /= self.speed_factor
    
                # redukcja do wartości minimalnej
                target_point.y = target_point.y - self.range_min * self.scale_factor * self.base_scale
                    
                # odwracanie wykresu
                if not self.reverse:
                    target_point.y = -1 * target_point.y + (self.range_max - self.range_min) * self.scale_factor * self.base_scale
                
                # ustalenie pozycji wykresu
                target_point.y = target_point.y + self.chart_y_pos

    def generate_spline_data(self):

        # przygpotowanie punktów do oblicznia splina ( x musi być rosnący !
        # pobranie danych

        all_x, all_y = [], []

        for point in [point for _,point in sorted(self.chart_points.items())]:

            all_x.append(point.x)
            all_y.append(point.y)

        # usunięcie 4 początkowych i 2 koncowych punktów  - zazwyczaj są niedokładne   

        x = np.array(all_x[4:-2])
        y = np.array(all_y[4:-2])

        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.linear_model import LinearRegression
        
        #specify degree of _ for polynomial regression model
        #include bias=False means don't force y-intercept to equal zero
        poly = PolynomialFeatures(degree=4, include_bias=False)

        #reshape data to work properly with sklearn
        poly_features = poly.fit_transform(x.reshape(-1, 1))

        #fit polynomial regression model
        poly_reg_model = LinearRegression()
        poly_reg_model.fit(poly_features, y)

        # ustalenie wartości dla osi x i oblicznie y wg. fit polynomial
        x_range = np.array(range(min(all_x), max(all_x)))
        
        y_pred_values = poly_reg_model.predict(poly.fit_transform(x_range.reshape(-1, 1)))

        self.chart_points_smoothed = [Point(x,y) for x,y in zip(x_range, y_pred_values)]

        # aktualizacja danych o max i min
        self.calc_min_max()

    def generate_smoothed_line_to_draw(self):

        # przeskalowanie krzywej do wyświetlanego obrazu

        self.generate_line_to_draw(self.chart_points_smoothed,
                                   self.chart_points_smoothed_to_draw)

    def calc_min_max(self):
        # oblicza prędkość max dla pierwszej połowy odcinka (na dojezdzie)
        # oblicza prędkość min z pominięciem początku i końca (+-0,5m)

        try:
            if self.smoothed == True:
                self.max_val = max(point.y for point in self.chart_points_smoothed[:len(self.chart_points_smoothed)//2])
                self.min_val = min(point.y for point in self.chart_points_smoothed[3:-3])
            else:
                self.max_val = max(point.y for point in self.chart_points.values()[:len(self.chart_points.values())//2])
                self.min_val = min(point.y for point in self.chart_points.values()[3:-3])
        except:
            pass

        if self.speed_factor:
            self.max_val /= self.speed_factor
            self.min_val /= self.speed_factor

    def add_time_counter(self, description):
        self.draws_times.append([description,time.time()])

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
        self.draws_times =[]
    