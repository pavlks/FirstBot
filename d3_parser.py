import requests

class D3:

    def __init__(self, threshold_date='day', min_rating=100):
        """ Парсим лучшие статьи за сегодня """
        self.threshold_date = threshold_date
        self.min_rating = min_rating

    def new_articles_d3(self, quantity=None):
        bad_subdomains = [150, 170, 6545, 8271, 7369]  # id подсайтов politota: 170, politics: 150, polka: 6545, telega: 8271, shapito: 7369
        d3_verified_publications = list()
        my_verified_publications = list()

        # FIRST we will parse d3 best posts
        for page in range(1, 2):  # here we set how many page we will parse
            settings = {
                'page': page,
                'sorting': 'rating',
                'per_page': 42,
                'threshold_date': self.threshold_date,  # day, week, month, year
            }
            d3_response = requests.get('https://d3.ru/api/posts/', params=settings).json()
            for p in d3_response["posts"]:
                subdomain = p["domain"]["id"]
                url_slug = p["url_slug"]
                rating = p["rating"]

                # проверяем, чтобы подсайт был нормальный и пост был не удалён
                if subdomain not in bad_subdomains and url_slug and rating and rating >= self.min_rating:
                    publication = dict()
                    # заголовок поста
                    publication['title'] = p["title"]
                    # рейтинг
                    publication['rating'] = p["rating"]
                    # id
                    publication['id'] = p["id"]
                    # ссылка
                    publication['link'] = str(p["domain"]["url"]) + "/" + str(p["url_slug"]) + "-" + str(p["id"])
                    d3_verified_publications.append(publication)

        # SECOND we will parse my personal subscription list
        # login_pass = {'username': 'pavlk', 'password': 'wossupbro'}
        # auth_url = 'https://d3.ru/api/auth/login/'
        # authentication = requests.post(url=auth_url, data=login_pass).json()  #we obtain sid and uid for 'headers' later
        # sid = authentication['sid']
        # uid = authentication['uid']
        sid = '26b9e363ee82e29e9a5e887c6a4db39c'
        uid = '80997'

        for page in range(1, 3):
            url = 'https://d3.ru/api/posts/subscriptions/'
            payload = {
                "sorting": "rating",
                "threshold_rating": 100,
                "threshold_date": self.threshold_date,
                # "feed_type": "personal",
                "per_page": 42,
                "page": page,
            }
            headers = {
                'X-Futuware-UID': uid,
                'X-Futuware-SID': sid
            }

            my_response = requests.get(url, params=payload, headers=headers).json()
            for p in my_response["posts"]:
                subdomain = p["domain"]["id"]
                url_slug = p["url_slug"]
                rating = p["rating"]
                if subdomain not in bad_subdomains and url_slug and rating and rating >= self.min_rating:
                    publication = dict()
                    publication['title'] = p["title"]
                    publication['rating'] = p["rating"]
                    publication['id'] = p["id"]
                    publication['link'] = str(p["domain"]["url"]) + "/" + str(p["url_slug"]) + "-" + str(p["id"])
                    my_verified_publications.append(publication)

        # join both lists and remove duplicates
        for pub in my_verified_publications:
            if not bool(p for p in d3_verified_publications if p['id'] == pub['id']):
                d3_verified_publications.append(pub)

        best_publications = sorted(d3_verified_publications, key=lambda i: i['rating'], reverse=True)[:quantity]

        # save to file just for fun
        with open('d3_posts.txt', 'w', encoding="utf-8") as d:
            print(best_publications, file=d)

        return best_publications
