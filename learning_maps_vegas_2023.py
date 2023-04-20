from datetime import datetime, timedelta
from calendar_view.core import data
from calendar_view.config import style
from calendar_view.core.config import CalendarConfig
from calendar_view.calendar import Calendar
from calendar_view.core.event import Event
from calendar_view.core.event import EventStyles
from calendar_view.core.event import EventStyle
import requests
import os
from multiprocessing.pool import ThreadPool as Pool
import threading
from typing import List, Type
import json


class Learning_Map:
    def __init__(self, category, name, id):
        self.category = category
        self.name = name.replace('/', '-')
        self.id = id

    def __str__(self):
        return f'{self.category = } -- {self.name = } -- {self.id = }'


    @staticmethod
    def get_learning_maps() -> List[Type['Learning_Map']]:

        '''
        Use the Rainfocus API and compute the dictionary of all learning_maps in JSON format.
        Return a list of instances of Learning_Map.
        '''

        url = "https://events.rainfocus.com/api/search"

        payload={'type': 'session',
        'catalogDisplay': 'list'}

        headers = {
        'rfapiprofileid': credentials['rfapiprofileid'],
        'referer': 'https://www.ciscolive.com/'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        learning_maps_json = list(filter(lambda d: d.get('id') == 'learningmap', response.json()['attributes']))[0]
        
        learning_maps = []

        for value in learning_maps_json['values']:

            category = value['id'].rstrip().replace('\u200e', '')

            for child in value['child']['values']:
                id = child['id']
                name = child['name']

                learning_maps.append(Learning_Map(category, name, id))

        return learning_maps


    @staticmethod
    def get_categories(learning_maps) -> List[str]:

        '''
        Computes a list of learning_maps and return a list of each unique category.
        '''

        categories = [learning_map.category for learning_map in learning_maps]
        categories = list(set(categories))

        return categories

    
    def get_sessions(self):
        '''
        Take a learning map and returns the associated sessions in a json object.
        '''

        url = "https://events.rainfocus.com/api/search"

        payload =   {'search.learningmap': self.id,
                    'type': 'session'}

        headers = {
        'rfapiprofileid': credentials['rfapiprofileid'],
        'referer': 'https://www.ciscolive.com/'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.json()


class Session():

    def __init__(self, session_json):
        self.type = session_json['type']
        try:
            self.start = datetime.strptime(session_json['times'][0]['utcStartTime'], '%Y/%m/%d %H:%M:%S') - timedelta(hours=7)
            self.end = datetime.strptime(session_json['times'][0]['utcEndTime'], '%Y/%m/%d %H:%M:%S') - timedelta(hours=7)
        except KeyError:
            self.start = 'Null'
            self.end = 'Null'
        self.name = session_json['title']
        self.id = session_json['code']
        match int(self.id.split('-')[1][0]):
            case 1: self.level = 'Introductory'
            case 2: self.level = 'Intermediate'
            case 3: self.level = 'Advanced'
            case 4: self.level = 'General'
        
    def __str__(self):
        return self.name


def make_folder(folder_path: str) -> None:
    '''
    The learning maps files will be created in a folder for each category.
    Verifies such folders exist or create them.
    '''

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def make_calendar_view(learning_map: Learning_Map) -> None:
    '''
    For given learning_map;
    Makes a .png calendar view inside the learning_map.category folder.
    '''

    folder = LEARNING_MAPS_FOLDER + '/' + learning_map.category
    
    sessions_json = learning_map.get_sessions()
    sessions = []

    for session in sessions_json['sectionList'][0]['items']:
        sessions.append(Session(session))

    style.hour_height = 500
    style.day_width = 1500
    style.event_notes_color = '#0D274D'
    style.title_font = style.image_font(250)
    style.hour_number_font = style.image_font(50)
    style.day_of_week_font = style.image_font(150)
    style.event_title_font = style.image_font(80)
    style.event_notes_font = style.image_font(60)

    config = data.CalendarConfig(
        lang='en',
        title=learning_map.name,
        dates='2023-06-04 - 2023-06-08',
        show_date=True,
        mode='working_hours',
        title_vertical_align='top',
    )

    events = []

    for session in sessions:

        if session.type != 'Walk-in Lab':
            match session.level:
                    case 'Introductory': 
                        color = EventStyle(event_border=(116, 191, 75, 240), event_fill=(116, 191, 75, 180))
                    case 'Intermediate': 
                        color = EventStyle(event_border=(251, 171, 44, 240), event_fill=(251, 171, 44, 180))
                    case 'Advanced': 
                        color = EventStyle(event_border=(227, 36, 27, 240), event_fill=(227, 36, 27, 180))
                    case 'General': 
                        color = EventStyle(event_border=(0, 188, 235, 240), event_fill=(0, 188, 235, 180))
                    
            if session.id == 'BRKSPG-2028': 
                print('toto')

            if session.start == 'Null' or session.end == 'Null':
                print(session.name, 'has not a valid time start or end: Null!')
            else:
                events.append(Event(day=session.start.strftime('%Y-%m-%d'), 
                                    start=session.start.strftime('%H:%M'), 
                                    end=session.end.strftime('%H:%M'), 
                                    title=session.id,
                                    notes=session.name,
                                    style=color))

    calendar = Calendar.build(config)
    calendar.add_events(events)
    calendar.save(folder + '/' + learning_map.name + ".png")
    
    return learning_map.name


if __name__ == '__main__':

    with open('credentials.json') as file:
        credentials = json.load(file)
    
    LEARNING_MAPS_FOLDER = './learning_maps/'
    
    learning_maps = Learning_Map.get_learning_maps()
    print('Done collecting all learning map sessions. Generating .png for each learning_map')

    folders = Learning_Map.get_categories(learning_maps)

    # in case the folders to store learning_maps don't already exist
    for folder in folders:
        make_folder(LEARNING_MAPS_FOLDER + folder)
    
    # 1 thread: 5 minutes and 4 seconds
    # 5 threads: 68 seconds
    # 10 threads: 52 seconds
    # 20 threads: 57 seconds
    with Pool(10) as pool:
        for done in pool.imap_unordered(make_calendar_view, learning_maps):
            print(f'-- DONE {done} --')