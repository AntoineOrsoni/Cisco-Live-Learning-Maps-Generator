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
from typing import List


class Learning_Map:
    def __init__(self, category, name, id):
        self.category = category
        self.name = name
        self.id = id

    def __str__(self):
        return f'{self.category = } -- {self.name = } -- {self.id = }'


def get_learning_maps_json():

    '''
    Uses the Rainfocus API to return the dictionary of all learning_maps in JSON format.
    '''
    
    url = "https://events.rainfocus.com/api/search"

    payload={'type': 'session',
    'catalogDisplay': 'list'}

    headers = {
    'rfapiprofileid': '0wnUkT1BBZK3JR2t3yc5huPwNQCS8C3n',
    'referer': 'https://www.ciscolive.com/'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return list(filter(lambda d: d.get('id') == 'learningmap', response.json()['attributes']))[0]


def get_learning_maps():

    '''
    Uses the get_learning_maps_json() API and return a list of instances of Learning_Map.
    '''
    
    learning_maps_json = get_learning_maps_json()
    learning_maps = []

    for value in learning_maps_json['values']:

        category = value['id'].rstrip().replace('\u200e', '')

        for child in value['child']['values']:
            name = child['name'].replace('\u200b', '').replace('/', ' ')
            id = child['id']

            learning_maps.append(Learning_Map(category, name, id))

    return learning_maps


def get_categories(learning_maps) -> List[str]:

    '''
    Computes a list of learning_maps and return a list of each unique category.
    '''

    categories = [learning_map.category for learning_map in learning_maps]
    categories = list(set(categories))

    return categories


def get_sessions(learning_map: str):
    '''
    Take a learning map and returns the associated sessions in a json object.
    '''

    url = "https://events.rainfocus.com/api/search"

    payload =   {'search.learningmap': learning_map,
                'type': 'session'}

    headers = {
    'rfapiprofileid': '0wnUkT1BBZK3JR2t3yc5huPwNQCS8C3n',
    'referer': 'https://www.ciscolive.com/'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


class Session():

    def __init__(self, session_json):
        self.type = session_json['type']
        try:
            self.start = datetime.strptime(session_json['times'][0]['utcStartTime'], '%Y/%m/%d %H:%M:%S') + timedelta(hours=1)
            self.end = datetime.strptime(session_json['times'][0]['utcEndTime'], '%Y/%m/%d %H:%M:%S') + timedelta(hours=1)
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


def make_folder(folder_path) -> None:
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
    learning_map_name = learning_map.name
    learning_map_id = learning_map.id

    sessions_json = get_sessions(learning_map_id)

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
        title=learning_map_name,
        dates='2023-02-06 - 2023-02-10',
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
                    
            events.append(Event(day=session.start.strftime('%Y-%m-%d'), 
                                start=session.start.strftime('%H:%M'), 
                                end=session.end.strftime('%H:%M'), 
                                title=session.id,
                                notes=session.name,
                                style=color))

    calendar = Calendar.build(config)
    calendar.add_events(events)
    calendar.save(folder + '/' + learning_map_name + ".png")
    
    return learning_map_name


if __name__ == '__main__':
    
    LEARNING_MAPS_FOLDER = './learning_maps/'
    
    learning_maps = get_learning_maps()
    print('Done collecting all learning map sessions. Generating .png for each learning_map')

    folders = get_categories(learning_maps)

    # in case the folders to store learning_maps don't already exist
    for folder in folders:
        make_folder(LEARNING_MAPS_FOLDER + folder)
    
    with Pool(10) as pool:
        for done in pool.imap_unordered(make_calendar_view, learning_maps):
            print(f'-- DONE {done} --')