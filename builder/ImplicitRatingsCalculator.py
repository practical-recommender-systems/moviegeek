import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
from django.db.models import Count
django.setup()

import datetime
from datetime import date, timedelta
import sqlite3

from collector.models import Log
from analytics.models import Rating
from builder import DataHelper

db = './../db.sqlite3'
w1 = 100
w2 = 50
w3 = 15


def connect_to_db():
    return sqlite3.connect(db)


def calculate_decay(age_in_days):
    return 1/age_in_days


def query_log_for_users(conn):
    sql = """
    select distinct(user_id)
    from collector_log log
    """

    #c = conn.cursor()
    #return c.execute(sql)
    return Log.objects.values('user_id').distinct()


def query_log_data_for_user(userid, conn):
    sql = """
    SELECT *
    FROM collector_log log
    WHERE user_id = {}
    """.format(userid)

    c = conn.cursor()
    #return c.execute(sql)
    return Log.objects.filter(user_id=userid)


def query_aggregated_log_data_for_user(userid, conn):
    sql = """
    SELECT
        user_id,
        content_id,
        mov.title,
        count(case when event = 'buy' then 1 end) as buys,
        count(case when event = 'details' then 1 end) as details,
        count(case when event = 'moredetails' then 1 end) as moredetails
    FROM   collector_log log
    JOIN    moviegeeks_movie mov
    ON      log.content_id = mov.movie_id
    WHERE
        user_id like {}
    group by user_id, content_id, mov.title
    order by buys desc, details desc, moredetails desc
    """.format(userid)

    c = conn.cursor()
    print(c.description)
    return c.execute(sql)


def calculate_implicit_ratings_w_timedecay(userid, conn):

    data = query_log_data_for_user(userid, conn)

    weights = {{'buy': w1}, {'moredetails': w2}, {'details': w3} }
    ratings = dict()

    for entry in data:
        movie_id = entry.movie_id
        event_type = entry.event

        if movie_id in ratings:

            age = (date.today() - entry.created) // timedelta(days=365.2425)

            decay = calculate_decay(age)

            ratings[movie_id] += weights[event_type]*decay

    return ratings


def calculate_implicit_ratings_for_user(userid, conn=connect_to_db()):
    data = query_aggregated_log_data_for_user(userid, conn=connect_to_db())

    ratings = dict()
    maxrating = 0

    for row in data:
        print(row)
        content_id = str(row[1])
        buys = row[3]
        details = row[4]
        moredetails = row[5]

        rating = w1 * buys + w2 * details + w3 * moredetails
        if rating > maxrating:
            maxrating = rating
        ratings[content_id] = rating

    for content_id in ratings.keys():
        ratings[content_id] = 10 * ratings[content_id] / maxrating

    return ratings


def save_ratings(ratings, userid, type, conn=DataHelper.connect_to_db()):

    print("saving ratings for {}".format(userid))
    i = 0

    for content_id, rating in ratings.items():

        Rating(
            user_id=userid,
            movie_id=str(content_id),
            rating=rating,
            rating_timestamp=datetime.datetime.now(),
            type=type
        ).save()
        print ('{} {}'.format(userid, str(content_id)))
        #conn.cursor().execute(sql)

        i += 1

        if i == 100:
            print('.', end="")
            i = 0


def calculate_ratings_with_timedecay(conn):

    for user in query_log_for_users(conn):
        userid = user['user_id']
        ratings = calculate_implicit_ratings_w_timedecay(userid, conn)
        save_ratings(ratings, userid, 'implicit_w', conn)


def calculate_ratings(conn):

    rows = query_log_for_users(conn)
    for user in rows:
        userid = user['user_id']
        ratings = calculate_implicit_ratings_for_user(userid, conn=connect_to_db())
        save_ratings(ratings, userid, 'implicit', conn)


if __name__ == '__main__':
    print("Calculating implicit ratings...")

    Rating.objects.filter(type='implicit').delete()

    #conn = connect_to_db()
    conn = []
    # c = conn.cursor()
    #
    # for tables in c.execute("select name from sqlite_master where type = 'table';"):
    #     print(tables[0])

    # Save (commit) the changes
    calculate_ratings(conn)
    #conn.commit()
    #conn.close()
