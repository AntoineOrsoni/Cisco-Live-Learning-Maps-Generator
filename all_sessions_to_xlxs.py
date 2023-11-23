from datetime import datetime, timedelta
import requests
import json
import pandas as pd
import warnings
import re
from openpyxl.utils.exceptions import IllegalCharacterError


class Session():

    def __clean_string__(self, input_string: str):
        '''
        Takes a string and removes illegal characters. Returns the cleaned string.
        '''

        # Create a list of illegal characters.
        illegal_chars = [chr(i) for i in range(0,32) if i not in (9,10,13)]
        # Remove illegal characters from the string.
        cleaned_string = ''.join(char for char in input_string if char not in illegal_chars)
        # Remove html tags
        cleaned_string = re.sub('<.*?>|\n', '', cleaned_string)

        return cleaned_string

    def __init__(self, session_json):
        self.type = session_json['type']
        if 'times' in session_json:
            start = session_json['times'][0].get('utcStartTime', 'Null')
            if start != 'Null':
                self.start = datetime.strptime(start, '%Y/%m/%d %H:%M:%S') + timedelta(hours=2)
            else:
                self.start = 'Null'
            end = session_json['times'][0].get('utcEndTime', 'Null')
            if end != 'Null':
                self.end = datetime.strptime(end, '%Y/%m/%d %H:%M:%S') + timedelta(hours=2)
            else:
                self.end = 'Null'
            self.incomplete = False
        else: 
            self.incomplete = True
        self.name = session_json['title']
        self.id = session_json['code']
        match int(self.id.split('-')[1][0]):
            case 1: self.level = 'Introductory'
            case 2: self.level = 'Intermediate'
            case 3: self.level = 'Advanced'
            case 4: self.level = 'General'
        
        self.abstract = self.__clean_string__(session_json['abstract'])

        participants = session_json.get('participants', 'Null')
        if participants != 'Null':
            self.participants = [participant['globalFullName'] for participant in participants]

            for participant in participants:
                attributes = participant.get('attributevalues', 'Null')
                
                if attributes != 'Null':
                    for attribute in attributes:
                        if attribute['attribute_id'] == "distinguished_speaker":
                            self.distinguished_speaker = True
                        else:
                            self.distinguished_speaker = False
                else: 
                    self.distinguished_speaker = False
        else:
            self.participants = 'None'
            self.distinguished_speaker = False

        self.technologies = []
        attributes = session_json.get('attributevalues', 'Null')
        if attributes != "Null":
            for attribute in attributes:
                if attribute['attribute_id'] == "Technology":
                    self.technologies.append(self.__clean_string__(attribute['value']))
        else:
            self.technologies = ['None']
        
    def __str__(self) -> str:
        return f"{self.id} - {self.name}"
    
    
def get_sessions_from(start):
    '''
    Returns a subset of cisco live sessions in a json object, starting at index `start`.

    When start = 0, output looks like this:
    {'responseCode': '0', 'responseMessage': 'Success', 'totalSearchItems': 1524, 'sections': True, 'sectionList': []}

    Otherwise, output looks like this:
    {'responseCode': '0', 'responseMessage': 'Success', 'total': 1524, 'numItems': 50, 'from': 50, 'size': 50, 'items': []}
    '''



    all_sessions = []

    url = "https://events.rainfocus.com/api/search"

    payload =   {'type': 'session',
                 'from': start
                }

    headers = {
    'rfapiprofileid': credentials['rfapiprofileid'],
    'referer': 'https://www.ciscolive.com/'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


def get_all_sessions():
    '''
    Returns all cisco live sessions in a json object.

    When start = 0, output looks like this:
    {'responseCode': '0', 'responseMessage': 'Success', 'totalSearchItems': 1524, 'sections': True, 'sectionList': []}

    Otherwise, output looks like this:
    {'responseCode': '0', 'responseMessage': 'Success', 'total': 1524, 'numItems': 50, 'from': 50, 'size': 50, 'items': []}
    '''

    counter = 0
    all_sessions = []

    initial_response = get_sessions_from(start=0)
    sessions_total = initial_response['totalSearchItems']
    all_sessions.extend(initial_response['sectionList'][0]['items'])
    counter += initial_response['sectionList'][0]['size']

    while counter < sessions_total:
        sessions = get_sessions_from(start=counter)
        all_sessions.extend(sessions['items'])
        counter += sessions['size']
        print(f'{counter = }, {sessions_total = }')

    return all_sessions


if __name__ == '__main__':

    warnings.simplefilter(action='ignore', category=FutureWarning)
    with open('credentials.json') as file:
        credentials = json.load(file)

    all_sessions_raw = []
    all_sessions_raw = get_all_sessions()

    sessions = []

    for session in all_sessions_raw:
        sessions.append(Session(session))

    df = pd.DataFrame(columns=['ID', 'Name', 'Technical Level', 'Speakers', 'Distinguished Speaker?', 'Technologies', 'Abstract'])

    for session in sessions:
        df = df.append({'ID': session.id, 
                        'Name': session.name, 
                        'Technical Level': session.level,
                        'Speakers': ', '.join(session.participants),
                        'Distinguished Speaker?': str(session.distinguished_speaker),
                        'Technologies': ', '.join(session.technologies),
                        'Abstract': session.abstract}, 
                        ignore_index=True)

    try:
        df.to_excel("sessions_amsterdam_2024.xlsx", index=False)
    except IllegalCharacterError as e:
        print('ERROR', session.id, session.name)
        print(session.abstract)
        print(e)