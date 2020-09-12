import requests
import re
import os
import requests.auth
import logging

from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta


class PyArticles:
    posts_file = ""
    last_parse_time = ""

    def __init__(self, posts_file):
        # ======================================== LOGGING ========================================
        logging.info("Инициализируем PyArticles")
        
        self.posts_file = posts_file
        if os.path.exists(posts_file):
            self.last_parse_time = open(posts_file, 'r').read()
        else:
            f = open(posts_file, 'w')
            self.last_parse_time = str(datetime.timestamp(datetime.utcnow()))
            f.write(self.last_parse_time)
            f.close()

    def parse_new(self):
        # ======================================== LOGGING ========================================
        logging.info("Начинаем искать новые статьи о Python")
        
        last_timestamp = float(self.last_parse_time)

        # здесь мы будем собирать все новые посты
        all_posts = list()

        # Парсим HABR.COM
        # ======================================== LOGGING ========================================
        logging.info("Парсим HABR.COM")
        
        habr_urls = ['https://habr.com/ru/search/?target_type=posts&order_by=date&q=python', 'https://habr.com/ru/search/?target_type=posts&order_by=date&q=python3']

        for url in habr_urls:
            response = requests.get(url)
            html = BeautifulSoup(response.content, 'html.parser')

            posts = html.find_all('li', id=re.compile("^post_"))

            for pp in posts:
                post_info = dict()

                post_link = pp.h2.a['href']
                post_title = pp.h2.a.contents[0]
                post_id = int(str(pp['id']).split('_')[1])
                [date1, time1] = pp.find('span', 'post__time').contents[0].replace('вчера', str(date.today()-timedelta(days=1))).replace('сегодня', str(date.today())).split(' в ')
                post_time = datetime.strptime(time1, '%H:%M')
                date2 = str(date1).split()
                if len(date2) == 3:
                    [dd, mmm, yyyy] = date2
                    if str(mmm).lower().startswith('янв'):
                        mm = 1
                    elif str(mmm).lower().startswith('фев'):
                        mm = 2
                    elif str(mmm).lower().startswith('мар'):
                        mm = 3
                    elif str(mmm).lower().startswith('апр'):
                        mm = 4
                    elif str(mmm).lower().startswith('мая'):
                        mm = 5
                    elif str(mmm).lower().startswith('май'):
                        mm = 5
                    elif str(mmm).lower().startswith('июн'):
                        mm = 6
                    elif str(mmm).lower().startswith('июл'):
                        mm = 7
                    elif str(mmm).lower().startswith('авг'):
                        mm = 8
                    elif str(mmm).lower().startswith('сен'):
                        mm = 9
                    elif str(mmm).lower().startswith('окт'):
                        mm = 10
                    elif str(mmm).lower().startswith('ноя'):
                        mm = 11
                    elif str(mmm).lower().startswith('дек'):
                        mm = 12
                    post_date = date(year=int(yyyy), month=mm, day=int(dd))
                else:
                    post_date = date.fromisoformat(date2[0])
                date_time = datetime(year=post_date.year, month=post_date.month, day=post_date.day, hour=post_time.hour,
                                     minute=post_time.minute)
                post_utctime = date_time - timedelta(hours=3)
                post_timestamp = datetime.timestamp(post_utctime)

                post_info['post_id'] = post_id
                post_info['post_timestamp'] = post_timestamp
                post_info['post_title'] = post_title
                post_info['post_link'] = post_link

                if post_timestamp > last_timestamp:
                    all_posts.append(post_info)

#######################################################################################################################################################################################################
#######################################################################################################################################################################################################
#######################################################################################################################################################################################################

        # Парсим REDDIT.COM - пока тормознем, а то очень много спама с этого сайта
        # ======================================== LOGGING ========================================
        # logging.info("Парсим REDDIT.COM")
        
        # client_auth = requests.auth.HTTPBasicAuth('gDoZ3CYKjpzj2A', 'cI-BnDffdNKH1N-0apYsmoq3X5o')
        # post_data = {"grant_type": "password", "username": "pavlks", "password": "wossupbro"}
        # headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0"}
        # response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
        # cr = response.json()

        # reddit_urls = ['https://oauth.reddit.com/r/python/new', 'https://oauth.reddit.com/r/learnpython/new', 'https://oauth.reddit.com/r/learnprogramming/new']
        # for url in reddit_urls:
            # headers = {"Authorization": f"{cr['token_type']} {cr['access_token']}", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0"}
            # response = requests.get(url, headers=headers, params={'limit': 100})
            # posts = response.json()
            # for pp in posts['data']['children']:
                # post_info = dict()
                # post_info['post_id'] = pp['data']['id']
                # post_info['post_timestamp'] = pp['data']['created_utc']
                # post_info['post_title'] = pp['data']['title']
                # post_info['post_link'] = pp['data']['url']
                # post_timestamp = float(pp['data']['created_utc'])

                # if post_timestamp > last_timestamp:
                    # all_posts.append(post_info)

#######################################################################################################################################################################################################
#######################################################################################################################################################################################################
#######################################################################################################################################################################################################

        # Парсим MEDIUM.COM и TOWARDSDATASCIENCE.COM
        # ======================================== LOGGING ========================================
        logging.info("Парсим MEDIUM.COM и TOWARDSDATASCIENCE.COM")
        
        medium_urls = ['https://medium.com/tag/python3', 'https://medium.com/tag/python', 'https://towardsdatascience.com/tagged/python3', 'https://towardsdatascience.com/tagged/python']
        for url in medium_urls:
            response = requests.get(url)
            html = BeautifulSoup(response.content, 'html.parser')

            posts = [pp for pp in html.find_all('div', 'postArticle') if pp.has_attr('data-post-id')]

            for pp in posts:
                post_info = dict()
                post_id = pp['data-post-id']
                time1 = str(pp.find('time')['datetime'])
                post_utctime = datetime.strptime(time1, '%Y-%m-%dT%H:%M:%S.%fZ')
                post_timestamp = datetime.timestamp(post_utctime)
                post_title = pp.h3.contents[0]
                link1 = pp.find('a', href=re.compile(post_id))['href']
                post_link = link1.split('?', maxsplit=1)[0]

                post_info['post_id'] = post_id
                post_info['post_timestamp'] = post_timestamp
                post_info['post_title'] = post_title
                post_info['post_link'] = post_link

                if post_timestamp > last_timestamp:
                    all_posts.append(post_info)

        self.update_last_parse_time(str(datetime.timestamp(datetime.utcnow())))
        return all_posts

    def update_last_parse_time(self, timestamp: str):
        self.last_parse_time = timestamp

        with open(self.posts_file, "r+") as f:
            infodata = f.read()
            f.seek(0)
            f.write(str(timestamp))
            f.truncate()

        return timestamp