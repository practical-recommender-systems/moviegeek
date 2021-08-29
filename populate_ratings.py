import os
import requests
import django
import datetime
import decimal
from tqdm import tqdm
from django import db


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

django.setup()
db.reset_queries()

from analytics.models import Rating

def download_ratings()-> list:
    '''
    Gets latest ratings in format userid::movieid::rating::timestamp\n
    :return: response object with data formatted as a list of strings
    '''
    URL = 'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest/ratings.dat'

    response = requests.get(URL)
    data = response.text
    ratings = data.split('\n')

    return ratings

def delete_db()-> None:
    Rating.objects.all().delete()

def populate(response:str)-> None:

    ratings = []

    for val in tqdm(response, mininterval=1, maxinterval=10):
        r = val.split(sep="::")
        if len(r) == 4:
            rating = Rating(user_id=r[0], movie_id=r[1], rating=decimal.Decimal(r[2]),
                                rating_timestamp=datetime.datetime.fromtimestamp(float(r[3])))
            ratings.append(rating)

    print("Bulk creating ratings table...")
    Rating.objects.bulk_create(ratings, batch_size=10000) # set batch size to avoid OOM leaks from Postgres
    print("Bulk created ratings table...")

if __name__ == '__main__':
    print("Starting populating ratings data...")
    print("Truncating movie ratings data")
    delete_db()

    print("Downloading ratings data...")
    data = download_ratings()
    print("Downloading movie ratings finished...")

    print("Populating movie ratings tables...")
    populate(data)
    print("Movie ratings tables populated...")
