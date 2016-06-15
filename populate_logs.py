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
        'action': [145, 2373, 8241, 23, 459, 1240, 7787, 63113, 6534, 57528, 57640, 63181, 57951, 61024, 64508, 58293,
                   61350, 61132, 62999, 64231],
        'drama': [25940, 864, 1805, 5340, 7456, 48567, 3621, 297, 5907, 459, 1508, 5527, 8397, 4260, 5471, 5178, 2227,
                  8016, 60758, 60943],
        'comedy': [8241, 32013, 3884, 864, 61255, 62718, 62788, 59258, 60161, 60126, 60939, 61250, 62113, 62586, 58047,
                   58490, 57532, 58315, 58972, 59118, ]}
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


