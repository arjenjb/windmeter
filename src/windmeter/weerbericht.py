import os
from collections import namedtuple
from datetime import datetime

import requests

Meting = namedtuple('Meting', ('timestamp', 'richting_graden', 'snelheid_ms'))

DENHOORN = object()
LUTTORPET = object()


def get_weer_meting_luttorpet():
    molkom = '2691510'
    api_key = os.environ.get('OWM_API_KEY')

    response = requests.get('https://api.openweathermap.org/data/2.5/weather', {'id': molkom, 'APPID': api_key})
    result = response.json()

    wind = result['wind']
    return Meting(datetime.fromtimestamp(result['dt']), wind['deg'], wind['speed'])

def get_weer_meting_denhoorn():
    response = requests.get('https://api.buienradar.nl/data/public/1.1/jsonfeed')
    result = response.json()

    data = next(x for x in result['buienradarnl']['weergegevens']['actueel_weer']['weerstations']['weerstation'] if
                x['@id'] == '6229')

    return Meting(data['datum'], int(data['windrichtingGR']), float(data['windsnelheidMS']))

def get_weer_meting(locatie):
    if locatie is DENHOORN:
        return get_weer_meting_denhoorn()
    else:
        return get_weer_meting_luttorpet()


if __name__ == '__main__':
    from dotenv import load_dotenv


    load_dotenv()

    print(get_weer_meting_luttorpet())