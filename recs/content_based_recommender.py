from recs.base_recommender import base_recommender
from analytics.models import Rating
from recommender.models import MovieDescriptions, Similarity

from gensim import models, corpora, similarities, matutils
from scipy import spatial


class ContentBasedRecs(base_recommender):
    def recommend_items(self, user_id, num=6):
        ratings = Rating.objects.filter(user_id=user_id)

        lda = models.ldamodel.LdaModel.load('./lda/model.lda')

        dictionary = corpora.Dictionary.load('./lda/dict.lda')

        corpus = corpora.MmCorpus('./lda/corpus.mm')

        content_sims = dict()
        for rating in ratings:

            md = MovieDescriptions.objects.filter(imdb_id=rating.movie_id).first()
            if md is not None:
                index = similarities.MatrixSimilarity.load('./lda/index.lda')

                lda_vector = lda[corpus[int(md.lda_vector)]]
                sims = index[lda_vector]
                sorted_sims = sorted(enumerate(sims), key=lambda item: -item[1])[:num]
                movies = get_movie_ids(sorted_sims, corpus, dictionary)

                for movie in movies:
                    target = movie['target']
                    if target in content_sims.keys():
                        if movie['sim'] > content_sims[target]['sim']:
                            content_sims[target] = movie
                    else:
                        content_sims[target] = movie

    def predict_score(self, user_id, item_id):

        ratings = Rating.objects.filter(user_id=user_id)
        rated_movies = {r['movie_id']: r['rating'] for r in ratings.values()}

        lda = models.ldamodel.LdaModel.load('./lda/model.lda')
        corpus = corpora.MmCorpus('./lda/corpus.mm')

        md = MovieDescriptions.objects.filter(imdb_id=item_id).first()
        rated_movies_desc = MovieDescriptions.objects.filter(imdb_id__in=rated_movies.keys())

        if md is None:
            return 0

        if rated_movies_desc.count() == 0:
            return 0

        top = 0.0
        bottom = 0.0
        sim_items = 0
        for rm in rated_movies_desc:
            lda_vector = lda[corpus[int(md.lda_vector)]]
            lda_vector_sim = lda[corpus[int(rm.lda_vector)]]
            sim = matutils.cossim(lda_vector, lda_vector_sim)
            rating = rated_movies[rm.imdb_id]

            top += sim * float(rating)
            bottom += sim

        return top / bottom


def get_movie_ids(sorted_sims, corpus, dictionary):
    ids = [s[0] for s in sorted_sims]
    movies = MovieDescriptions.objects.filter(lda_vector__in=ids)

    return [{"target": movies[i].imdb_id,
             "title": movies[i].title,
             "sim": str(sorted_sims[i][1])} for i in range(len(movies))]