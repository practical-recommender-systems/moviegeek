import datetime
import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

import django

django.setup()

from collector.models import Log

SEED = 0


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
    # todo: Verify that movies are present in new dataset.
    # todo: content_ids should be strings. to avoid problems with zeros ex 0061350 becomes 61350 if not string.
    films = {
        'action': ['1211837', '2250912', '0803096', '2652118', '2381991', '1289401', '1340138', '2488496', '4172430', '2267968', '3300542', '1392190', '2304933', '2404233', '2911666', '3110958', '1877832', '0478970', '2975590', '1291150'],
        'drama': ['2381991', '0816692', '4172430', '1663202', '1179933', '2241351', '3460252', '3659388', '3349772', '1895587', '2025690', '1083452', '3707106', '2649554', '2057392', '2674430', '3322364', '2381111', '2267998', '1661199'],
        'comedy': ['1679335', '2709768', '4624424', '4769836', '2267968', '3110958', '0475290', '1291150', '3381008', '2120120', '1608290', '2293640', '1489889', '1083452', '2245084', '2096673', '2802144', '3949660', '1860213', '1985949']}
    genre = user.select_genre()
    interested_films = films[genre]

    film_id = interested_films[random.randint(0, len(interested_films) - 1)]
    return film_id


def select_action(user):
    actions = {'details': 70, 'moredetails': 20, 'buy': 10}

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
    number_of_events = 10000

    print("Generating Data")
    users = [
        User(1, 20, 30, 50),
        User(2, 50, 20, 40),
        User(3, 20, 30, 50),
        User(4, 100, 0, 0),
        User(5, 0, 100, 0),
        User(6, 0, 0, 100),
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
                visit_count=0)
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


