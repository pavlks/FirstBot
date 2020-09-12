import requests
import os.path
import math
import ast

from datetime import timedelta
from bs4 import BeautifulSoup


# page with information https://www.nhc.noaa.gov/cyclones/


class NHC:
    alert_file = ""
    alert_text = ""

    def __init__(self, alert_file):
        """ Парсим состояние циклонов в регионе """
        self.alert_file = alert_file
        if os.path.exists(alert_file):
            self.alert_text = open(alert_file, 'r').read()
        else:
            a = open(alert_file, 'w')
            self.alert_text = self.status_check()
            a.write(self.alert_text)
            a.close()

    def distance(self, lat: float, long: float):
        """ Cчитаем расстояние до центра циклона """
        r = 6371.0  # radius of the Earth
        lat1 = math.radians(20.86)  # Puerto Morelos coordinates
        lon1 = math.radians(-86.9)
        lat2 = math.radians(float(lat))
        lon2 = math.radians(float(long))
        dlon = lon2 - lon1  # change in coordinates
        dlat = lat2 - lat1
        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = round(r * c)
        return distance

    def get_cyclones(self, url: str):
        """ Собираем информацию по циклонам """
        response = requests.get(url)
        xml = BeautifulSoup(response.content, 'lxml-xml')
        cyclones_results = xml.find_all("nhc:Cyclone")

        if cyclones_results:
            cyclones_info = list()
            for i in cyclones_results:
                cyclone = dict()

                # Cyclone type and name
                ctype = i.find('nhc:type').contents[0]
                name = str(i.find('nhc:name').contents[0]).upper()

                # Calculate distance in km
                ccenter = i.find('nhc:center').contents[0]
                clat, clong = map(float, str(ccenter).split(','))
                dist_km = self.distance(clat, clong)

                # Calculate time and speed in kmh
                movement = i.find('nhc:movement').contents[0]
                direction, speed_mph = str(movement).replace(' mph', '').split(' at ')
                speed_kmh = 1.60934 * float(speed_mph)
                time = round(dist_km / speed_kmh)

                # Calculate wind speed
                wind_mph = i.find('nhc:wind').contents[0]
                wind_kmh = round(float(str(wind_mph).replace(' mph', '')) * 1.60934)

                cyclone['distance'] = dist_km
                cyclone['time'] = time
                cyclone['speed'] = speed_kmh
                cyclone['wind'] = wind_kmh
                cyclone['type'] = ctype
                cyclone['name'] = name
                cyclone['headline'] = i.find('nhc:headline').contents[0]
                cyclone['time_formatted'] = str(timedelta(hours=time).days) + ' д. ' + str(time % 24) + ' ч.'
                cyclone['wind_formatted'] = str(round(float(str(wind_mph).replace(' mph', '')) * 1.60934)) + ' км/ч'

                cyclones_info.append(cyclone)

            return cyclones_info

    def alert_message(self):
        """ Составляем окончательное сообщение из 2х частей """
        # так будем вставлять перенос строки в текст оповещения
        nl = '\n'

        # Atlantic GIS
        cyclones_list = self.get_cyclones('https://www.nhc.noaa.gov/gis-at.xml')
        if cyclones_list:
            at_message = str()
            for cyclone in cyclones_list:
                message_line = f"📢 {cyclone['type']} <b>{cyclone['name']}</b>{nl}" \
                               f"⏳ До него {cyclone['time_formatted']}, 🌪️скорость ветра достигает {cyclone['wind_formatted']}{nl}{nl}"
                at_message += message_line

                atlantic_info = "‼‼В <b>нашем Атлантическом регионе</b> бушуют циклоны:\n\n" + at_message
                at_active = True
        else:
            atlantic_info = F"☀ В нашем регионе бояться нечего - всё чисто 😎"
            at_active = False

        # Eastern Pacific GIS
        cyclones_list = self.get_cyclones('https://www.nhc.noaa.gov/gis-ep.xml')
        if cyclones_list:
            ep_message = str()
            for cyclone in cyclones_list:
                message_line = f"📢 {cyclone['type']} <b>{cyclone['name']}</b>{nl}" \
                               f"⏳ До него {cyclone['time_formatted']}, 🌪️скорость ветра достигает {cyclone['wind_formatted']}{nl}{nl}"
                ep_message += message_line

                eastern_pacific_info = "🚩🚩В <b>Тихом океане</b> не так уж и спокойно:\n\n" + ep_message
                ep_active = True
        else:
            eastern_pacific_info = F"☀ Тихоокеанский регион циклонами не затронут 😎"
            ep_active = False

        alert = atlantic_info + '\n' + eastern_pacific_info
        return alert, at_active, ep_active

    def status_check(self):
        urls = ['https://www.nhc.noaa.gov/gis-at.xml', 'https://www.nhc.noaa.gov/gis-ep.xml']
        status_line = list()
        for u in urls:
            info = self.get_cyclones(u)
            if info:
                for c in info:
                    status_line.append({
                        'type': c['type'],
                        'name': c['name'],
                        'distance': c['distance'],
                    })
        status = str(status_line)
        if status_line != self.alert_text:
            return status

    def update_hurricanes_info(self, status):
        self.alert_text = status

        with open(self.alert_file, "r+") as f:
            if status:
                f.read()
                f.seek(0)
                f.write(status)
                f.truncate()
                f.close()
            else:
                f.truncate(0)
                f.close()


        return status
