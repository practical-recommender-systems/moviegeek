import datetime
import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

import django

django.setup()

from collector.models import Log

SEED = 0

films = {'comedy':
                 [
                  '0475290'
                ,'1289401'
                ,'1292566'
                ,'1473832'
                ,'1489889'
                ,'1608290'
                ,'1679335'
                ,'1700841'
                ,'1711525'
                ,'1860213'
                ,'1878870'
                ,'1985949'
                ,'2005151'
                ,'2277860'
                ,'2387499'
                ,'2709768'
                ,'2823054'
                ,'2869728'
                ,'2937696'
                ,'3110958'
                ,'3381008'
                ,'3470600'
                ,'3521164'
                ,'3553442'
                ,'3783958'
                ,'3874544'
                ,'4034354'
                ,'4048272'
                ,'4136084'
                ,'4139124'
                ,'4438848'
                ,'4501244'
                ,'4513674'
                ,'4624424'
                ,'4651520'
                ,'4698684'
                ,'4901306'
                ,'5247022'
                ,'5512872'],
             'drama': ['2119532'
                ,'2543164'
                ,'3783958'
                ,'3315342'
                ,'3263904'
                ,'4034228'
                ,'3040964'
                ,'3741834'
                ,'2140479'
                ,'1179933'
                ,'1355644'
                ,'4550098'
                ,'2582782'
                ,'4975722'
                ,'2674426'
                ,'2005151'
                ,'4846340'
                ,'1860357'
                ,'3640424'
                ,'3553976'
                ,'2241351'
                ,'4052882'
                ,'2671706'
                ,'3774114'
                ,'5512872'
                ,'4172430'
                ,'3544112'
                ,'4513674'
                ,'0490215'
                ,'1619029'
                ,'4572514'
                ,'1878870'
                ,'1083452'
                ,'2025690'
                ,'1219827'
                ,'1972591'
                ,'4276820'
                ,'2381991'
                ,'3416532'
                ,'2547584'
             ], 'action': [
            '1431045', '2975590'
            , '1386697'
            , '3498820'
            , '3315342'
            , '1211837'
            , '2948356'
            , '3748528'
            , '3385516'
            , '3110958'
            , '4196776'
            , '4425200'
            , '3896198'
            , '2404435'
            , '3731562'
            , '1860357'
            , '4630562'
            , '0803096'
            , '2660888'
            , '3640424'
            , '3300542'
            , '0918940'
            , '2094766'
            , '5700672'
            , '1289401'
            , '1628841'
            , '3393786'
            , '4172430'
            , '4094724'
            , '2025690'
            , '4116284'
            , '3381008'
            , '1219827'
            , '1972591'
            , '2381991'
            , '2034800'
            , '2267968'
            , '2869728'
            , '3949660'
            , '3410834'
        ,'2250912']}

class User:
    sessionId = 0
    userId = 0
    likes = {}
    events = {}

    def __init__(self, user_id, action, drama, comedy):
        self.sessionId = random.randint(0, 1000000)
        self.userId = user_id
        self.likes = {'action': action, 'drama': drama, 'comedy': comedy}
        self.events = {self.sessionId: []}

    def get_session_id(self):
        if random.randint(0, 100) > 90:
            self.sessionId += 1
            self.events[self.sessionId] = []

        return self.sessionId

    def select_genre(self):
        return sample(self.likes)


def select_film(user):

    genre = user.select_genre()
    interested_films = films[genre]
    film_id = ''
    while film_id == '':
        film_candidate = interested_films[random.randint(0, len(interested_films) - 1)]
        if film_candidate not in user.events[user.sessionId]:
            film_id = film_candidate

    return film_id


def select_action(user):
    actions = {'genreView': 15, 'details': 50, 'moreDetails': 24, 'addToList': 10, 'buy': 1}

    return sample(actions)


def sample(dictionary):
    random_number = random.randint(0, 100)
    index = 0
    for key, value in dictionary.items():
        index += value

        if random_number <= index:
            return key


def main():
    Log.objects.all().delete()
    random.seed(SEED)

    number_of_events = 100000

    print("Generating Data")
    users = [
        User(400001, 20, 30, 50),
        User(400002, 50, 20, 40),
        User(400003, 20, 30, 50),
        User(400004, 100, 0, 0),
        User(400005, 0, 100, 0),
        User(400006, 0, 0, 100),
    ]
    print("Simulating " + str(len(users)) + " visitors")

    for x in range(0, number_of_events):
        randomuser_id = random.randint(0, len(users) - 1)
        user = users[randomuser_id]
        selected_film = select_film(user)
        action = select_action(user)
        if action == 'buy':
            user.events[user.sessionId].append(selected_film)
        print("user id " + str(user.userId) + " selects film " + str(selected_film) + " and " + action)

        l = Log(user_id=str(user.userId),
                content_id=selected_film,
                event=action,
                session_id=str(user.get_session_id()),
                created=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
        l.save()

    print("users\n")
    for u in users:
        print("user with id {} \n".format(u.userId))
        for key, value in u.events.items():
            if len(value) > 0:
                print(" {}: {}".format(key, value))


if __name__ == '__main__':
    print("Starting MovieGeeks Log Population script...")
    main()
