import os
import urllib.request



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

import django
import csv, decimal, datetime

django.setup()

from analytics.models import Rating

def create_rating(user_id, content_id, rating, timestamp):

    rating = Rating(user_id=user_id, movie_id=content_id, rating=decimal.Decimal(rating),
                    rating_timestamp=datetime.datetime.fromtimestamp(float(timestamp)))

    return rating


def delete_db():
    print('truncate db')
    Rating.objects.all().delete()
    print('finished truncate db')

def populate(path):

    with open(path, newline='') as csvfile:
        rating_reader = csv.DictReader(csvfile, skipinitialspace=True)
        ratings = []
        for rating in rating_reader:
            if len(rating) == 4:
                rating = create_rating(rating['userId'], rating['movieId'], rating['rating'], rating['timestamp'])
                ratings.append(rating)
            if len(ratings) == 1000:
                Rating.objects.bulk_create(ratings)
                ratings = []
                print(".")
        Rating.objects.bulk_create(ratings)
    print('database is populated with {} ratings'.format(Rating.objects.count()))


if __name__ == '__main__':
    print("This script will load the MovieLens latest dataset - only the ratings")
    print("Beware that this dataset doesnt work with the moviegeek website. run populate_ratings.py for that")

    print("Before starting this you need to download the latest from here: ")
    print("http://grouplens.org/datasets/movielens/latest/")
    print("when its downloaded you should unzip it and place it where its easy to get")

    print("Usage: python populate_ratings_from_MovieLens_data.py ")
    print("Starting MovieGeeks Population script...")
    delete_db()
    populate('/Users/u0157492/Downloads/ml-latest-small/ratings.csv')