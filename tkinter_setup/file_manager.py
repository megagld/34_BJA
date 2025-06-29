import os
import regex as re

class VideoFile:
    def __init__(self, file, file_path):
        self.name = file
        self.file_path = file_path
        self.analized = False
        self.date = None
        self.time = None
        self.count = None

class VideoFiles:
    def __init__(self):

        self.video_files = []
        self.analized_files = []
        self.dropdown_lists_data = {}

        self.dropdown_list_dates_a = []
        self.dropdown_list_times_a = []
        self.dropdown_list_counts_a = []

        self.handy_files_dict_a = {}

        self.dropdown_list_dates_b = []
        self.dropdown_list_times_b = []
        self.dropdown_list_counts_b = []

        self.handy_files_dict_b = {}

        # parsuj pliki video
        self.get_video_files_list()       

        # parsuj pliki analizy
        self.get_analysed_files_list()
    
        # oznacz przeanalizowane
        self.set_analized()

        # przypisz date, czas i liczniki
        self.set_date_time_count()

        # stwórz dane do list rozwijanych 
        self.make_dropdown_list_data()

    def get_video_files_list(self):

        input_dir = os.getcwd()
        input_data_dir = '{}\\{}'.format(input_dir, '_data')
    
        # pobiera pliki z katalogu _data i podkatalogów
            
        for root, _, files in os.walk(input_data_dir):
            for file in files:
                if file.endswith('.mp4'):
                    self.video_files.append(VideoFile(file, os.path.join(root, file)))

    def get_analysed_files_list(self):
        
        input_dir = os.getcwd()
        input_analized_dir = '{}\\{}'.format(input_dir, '_analysed')

        # pobiera pliki z katalogu _analized
        for file in next(os.walk(input_analized_dir), (None, None, []))[2]:
            if file.endswith('.json'):
                self.analized_files.append(file[:-10])

    def set_analized(self):
        # sprawdz i oznacza które pliki video mają analizę
        for video_file in self.video_files:
            video_file.analized = video_file.name[:-4] in self.analized_files
    
    def set_date_time_count(self):
        # ustalenie daty, czasu i numeru wg nazwy video

        regex = r'(.*)(20\d{2})([0-1]\d)([0-3]\d)(.*)([0-2]\d)([0-5]\d)([0-5]\d)(.*)(\d{3})(.*)'

        for video_file in self.video_files:
            match = re.match(regex, video_file.name)
            if match:
                video_file.date = f'{match.group(2)}-{match.group(3)}-{match.group(4)}'
                video_file.time = f'{match.group(6)}:{match.group(7)}:{match.group(8)}'
                video_file.count = f'{match.group(10)}'

    def make_dropdown_list_data(self):
        # dostępne obiekty plików w postaci zagniezdzonego słownika - do list rozwijanych
        for video in self.video_files:
            if not video.date:
                try:
                    self.dropdown_lists_data['unclassified'][video.name]=video
                except:
                     self.dropdown_lists_data['unclassified']=dict()
                     self.dropdown_lists_data['unclassified'][video.name]=video                            
            else:
                try:
                    self.dropdown_lists_data[video.date][video.time][video.count] = video

                except KeyError:
                    if video.date not in self.dropdown_lists_data:
                        self.dropdown_lists_data[video.date] = dict()
                        self.dropdown_lists_data[video.date][video.time]= dict()                    
                    elif video.time not in self.dropdown_lists_data[video.date]:
                        self.dropdown_lists_data[video.date][video.time] = dict()                    
                    self.dropdown_lists_data[video.date][video.time][video.count] = video

    def get_dates(self):
        self.dropdown_list_dates = ['unclassified'] + sorted(date for date in self.dropdown_lists_data if date)

    def get_times(self, date):
        self.dropdown_list_times = sorted(time for time in self.dropdown_lists_data[date] if date)

    def get_counts_a(self, date, time):
        self.dropdown_list_counts_a = sorted(count for count in self.dropdown_lists_data[date][time] if date)

    def get_counts_b(self, date, time):
        self.dropdown_list_counts_b = sorted(count for count in self.dropdown_lists_data[date][time] if date)

    def make_handy_files_dict(self, date, time, dropdown_list_counts):
        return {count:self.dropdown_lists_data[date][time][count] for count in dropdown_list_counts}

    def get_others(self):
        return sorted(file.name for file in self.dropdown_lists_data if not file.date)







##################################################################


    # analized_files = []

    # input_analized_dir = '{}\\{}'.format(input_dir, '_analysed')
    # # pobiera pliki z katalogu _analized
    # for i in next(os.walk(input_analized_dir), (None, None, []))[2]:
    #     if i.endswith('.json'):
    #         analized_files.append(i[:-10])