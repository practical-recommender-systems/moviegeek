import os

from datetime import datetime

from recs.base_recommender import base_recommender
from analytics.models import Rating
from recommender.models import MovieDescriptions

from gensim import models, corpora, similarities, matutils

lda_path = './lda/'


class ContentBasedRecs(base_recommender):

    def __init__(self,
                 corpus=corpora.MmCorpus(lda_path + 'corpus.mm'),
                 index=similarities.MatrixSimilarity.load(lda_path + 'index.lda')):
        self.corpus = corpus
        self.index = index

    def recommend_items(self,
                        user_id,
                        num=6):

        movie_ids = Rating.objects.filter(user_id=user_id).order_by('-rating').values_list('movie_id', flat=True)[:100]

        return self.recommend_items_from_items(movie_ids, num)

    def recommend_items_by_ratings(self, user_id, active_user_items, num=6):
        movie_ids = [movie['movie_id'] for movie in active_user_items]
        return self.recommend_items_from_items(movie_ids, num)

    def recommend_items_from_items(self,
                                   movie_ids,
                                   num=6):
        content_sims = dict()

        start_time = datetime.now()
        for movie_id in movie_ids:

            md = MovieDescriptions.objects.filter(imdb_id=movie_id).first()
            if md is not None:

                lda_vector = self.corpus[int(md.lda_vector)]
                sims = self.index[lda_vector]
                sorted_sims = sorted(enumerate(sims), key=lambda item: -item[1])[1:num+5]
                movies = get_movie_ids(sorted_sims)

                for movie in movies:
                    target = movie['target']
                    if target in content_sims.keys():
                        if movie['sim'] > content_sims[target]['sim']:
                            content_sims[target] = movie
                    else:
                        content_sims[target] = movie
        print(f"old way {datetime.now()-start_time}")

        return sorted(content_sims.items(), key=lambda item: -float(item[1]['sim']))[:num]

    def predict_score(self, user_id, item_id):

        ratings = Rating.objects.filter(user_id=user_id)
        rated_movies = {r['movie_id']: r['rating'] for r in ratings.values()}

        md = MovieDescriptions.objects.filter(imdb_id=item_id).first()
        rated_movies_desc = MovieDescriptions.objects.filter(imdb_id__in=rated_movies.keys())

        if md is None:
            return 0

        if rated_movies_desc is None:
            return 0
        if rated_movies_desc.count() == 0:
            return 0

        top = 0.0
        bottom = 0.0

        for rm in rated_movies_desc:
            lda_vector = self.corpus[int(md.lda_vector)]
            lda_vector_sim = self.corpus[int(rm.lda_vector)]
            sim = matutils.cossim(lda_vector, lda_vector_sim)
            rating = rated_movies[rm.imdb_id]

            top += sim * float(rating)
            bottom += sim

        return top / bottom


def get_movie_ids(sorted_sims):
    ids = [s[0] for s in sorted_sims]
    movies = list(MovieDescriptions.objects.filter(lda_vector__in=ids))
    m_info = {str(movie.lda_vector): (movie.imdb_id, movie.title, sorted_sims) for movie in movies}

    return [{"target": m_info[str(id[0])][0],
             "title": m_info[str(id[0])][1],
             "sim": str(id[1])} for id in sorted_sims]