import os
import urllib.request
import django
import datetime
import decimal
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

django.setup()

from analytics.models import Rating


def create_rating(user_id, content_id, rating, timestamp):

    rating = Rating(user_id=user_id, movie_id=content_id, rating=decimal.Decimal(rating),
                    rating_timestamp=datetime.datetime.fromtimestamp(float(timestamp)))
    rating.save()

    return rating


def download_ratings():
    URL = 'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest/ratings.dat'
    response = urllib.request.urlopen(URL)
    data = response.read()

    print('download finished')
    return data.decode('utf-8')


def delete_db():
    print('truncate db')
    Rating.objects.all().delete()
    print('finished truncate db')


def populate():

    delete_db()

    ratings = download_ratings()

    for rating in tqdm(ratings.split(sep="\n")):
        r = rating.split(sep="::")
        if len(r) == 4:
            create_rating(r[0], r[1], r[2], r[3])


if __name__ == '__main__':
    print("Starting MovieGeeks Population script...")
    populate()
