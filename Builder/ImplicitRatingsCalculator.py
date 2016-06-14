import datetime
import sqlite3

db = './../db.sqlite3'
w1 = 100
w2 = 50
w3 = 15


def query_log_data_for_user(userid, conn):
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
    return c.execute(sql)


def calculate_implicit_ratings_for_user(userid, conn=sqlite3.connect(db)):
    data = query_log_data_for_user(userid, conn)

    ratings = dict()
    maxrating = 0

    for row in data:
        content_id = row[1]
        buys = row[3]
        details = row[4]
        moredetails = row[5]

        rating = w1 * buys + w2 * details + w3 * moredetails
        if rating > maxrating:
            maxrating = rating
        ratings[content_id] = w1 * buys + w2 * details + w3 * moredetails

    for content_id in ratings.keys():
        ratings[content_id] = 10 * ratings[content_id] / maxrating

    return ratings


def save_ratings(ratings, userid, conn):
    for content_id, rating in ratings.items():
        print("saving rating")
        sql = """
        UPDATE analytics_rating
        SET rating = {},rating_timestamp = '{}'
        WHERE user_id = {} and movie_id = {}
        """.format(rating, datetime.datetime.now(), userid, content_id)
        # print (sql)
        conn.cursor().execute(sql)


if __name__ == '__main__':
    print("Calculating implicit ratings...")

    userid = 1
    conn = sqlite3.connect(db)
    # c = conn.cursor()
    #
    # for tables in c.execute("select name from sqlite_master where type = 'table';"):
    #     print(tables[0])
    ratings = calculate_implicit_ratings_for_user(userid, conn)
    save_ratings(ratings, userid, conn)

    # Save (commit) the changes
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()
