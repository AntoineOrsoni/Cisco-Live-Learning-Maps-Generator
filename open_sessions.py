import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import re

def get_sessions(session_type, req_from = 0):
    '''
    Returns all sessions based on sessiontype.
    '''

    url = "https://events.rainfocus.com/api/search"

    payload =   {
                    'search.sessiontype': session_type,
                    'type': 'session',
                    'catalogDisplay': 'list',
                    'browserTimezone': 'Europe%2FParis',
                    'from': req_from
                }

    headers = {
        'authority': 'events.rainfocus.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.ciscolive.com',
        'referer': 'https://www.ciscolive.com/',
        'rfapiprofileid': credentials['rfapiprofileid'],
        'rfauthtoken': credentials['rfauthtoken'],
        'rfwidgetid': credentials['rfwidgetid'],
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


class Session():

    def __init__(self, session_json):
        self.type = session_json['type']
        self.name = re.sub(r"", "", session_json['title'])
        self.id = session_json['code']
        match int(self.id.split('-')[1][0]):
            case 1: self.level = 'Introductory'
            case 2: self.level = 'Intermediate'
            case 3: self.level = 'Advanced'
            case 4: self.level = 'General'
        if 'times' in session_json:
            start = session_json['times'][0].get('utcStartTime', 'Unknown')
            if start != 'Unknown':
                self.start = datetime.strptime(start, '%Y/%m/%d %H:%M:%S') + timedelta(hours=1)
            else:
                self.start = 'Unknown'
            end = session_json['times'][0].get('utcEndTime', 'Unknown')
            if end != 'Unknown':
                self.end = datetime.strptime(end, '%Y/%m/%d %H:%M:%S') + timedelta(hours=1)
            else:
                self.end = 'Unknown'
            self.day_name = session_json['times'][0]['dayName']
            self.capacity = int(session_json['times'][0]['capacity'])
            seats_remaining = session_json['times'][0].get('seatsRemaining', 'Unknown')
            if seats_remaining != 'Unknown':
                seats_remaining = int(seats_remaining)
            else:
                self.seats_remaining = 'Unknown'
            waitlist_remaining = session_json['times'][0].get('waitlistRemaining', 'Unknown')
            if waitlist_remaining != 'Unknown':
                waitlist_remaining = int(waitlist_remaining)
            else:
                self.waitlist_remaining = 'Unknown'
            self.room_id = session_json['times'][0]['roomId']
            self.room = session_json['times'][0]['room']
            self.incomplete = False
        else:
            print(self.name, 'has no attributes')
            self.incomplete = True
        
    def __str__(self) -> str:
        return f"{self.id} - {self.name}"


if __name__ == '__main__':
    
    with open('credentials.json') as file:
        credentials = json.load(file)

    session_types = ['Technical_seminar', 'BRK']

    for session_type in session_types:

        full_sessions = 0
        
        sessions_json = get_sessions(session_type)

        req_from = int(sessions_json['sectionList'][0]['from'])
        num_items = int(sessions_json['sectionList'][0]['numItems'])
        total = int(sessions_json['sectionList'][0]['total'])
        size = int(sessions_json['sectionList'][0]['size'])

        while req_from + num_items < total:
            req_from += size
            sessions_json_temp = get_sessions(session_type, req_from=req_from)

            for session in sessions_json_temp['items']:
                sessions_json['sectionList'][0]['items'].append(session)

        sessions = []

        for session in sessions_json['sectionList'][0]['items']:
            sessions.append(Session(session))

        list_df = []

        for session in sessions:

            if session.incomplete:
                to_append = {
                    'Session Name': [session.id + ' - ' + session.name],
                    'Day': 'Unknown',
                    'Timeslot': 'Unknwon',
                    'Total Capacity': 'Unknwon',
                    'Empty Seats': 'Unknwon', 
                    '% Available': 'Unknwon',
                    'Room': 'Unknwon',
                    'Status': 'Unknwon',
                }
            else:
                if session.seats_remaining != 'Unknown' and session.capacity != 'Unknown':
                    percent_available = int((session.seats_remaining / session.capacity) * 100)
                    if percent_available == 0: status = 'Full',
                    elif percent_available > 20 : status = 'Overcapacity',
                    else: status = 'Ok'
                else:
                    percent_available = 'Unknown'
                    status = 'Unknown'

                to_append = {
                    'Session Name': [session.id + ' - ' + session.name],
                    'Day': session.day_name,
                    'Timeslot': [session.start.strftime("%H:%M") + ' - ' + session.end.strftime("%H:%M")],
                    'Total Capacity': session.capacity,
                    'Empty Seats': session.seats_remaining, 
                    '% Available': [percent_available],
                    'Room': session.room,
                    'Status': status,
                }
            
            list_df.append(pd.DataFrame(data=to_append))

            if hasattr(session, 'seats_remaining') and session.seats_remaining != 'Unknown':
                if session.seats_remaining < 1:
                    full_sessions += 1

        try:
            df = pd.concat(list_df, names=['Session Name', 'Day', 'Timeslot', 'Total Capacity', 'Empty Seats', '% Available', 'Room', 'Status'])
        except ValueError:
            print('the below session has an ISSUE\n', session)

        df.to_excel('./open_sessions/open_' + session_type + '.xlsx', index=False)

        percentage_sessions_full = int((full_sessions / len(sessions)) * 100)
        print(percentage_sessions_full, 'percent of', session_type, 'are full!')