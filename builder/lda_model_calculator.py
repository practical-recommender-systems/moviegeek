import os
import sqlite3
import tqdm
import psycopg2
from scipy.sparse import coo_matrix

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django
from datetime import datetime

from prs_project import settings

import logging
import numpy as np

import pyLDAvis
import pyLDAvis.gensim

import operator
import math

from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from gensim import corpora, models, similarities

django.setup()

from recommender.models import MovieDescriptions, LdaSimilarity


def dot_product(v1, v2):
    dp = sum(map(operator.mul, v1, v2))
    return dp


def vector_cos(v1, v2):
    prod = dot_product(v1, v2)
    sqrt1 = math.sqrt(dot_product(v1, v1))
    sqrt2 = math.sqrt(dot_product(v2, v2))
    return prod / (sqrt1 * sqrt2)


def cosine_similarity(ldas):
    size = ldas.shape[0]
    similarity_matrix = np.zeros((size, size))

    for i in range(ldas.shape[0]):

        for j in range(ldas.shape[0]):
            similarity_matrix[i, j] = vector_cos(ldas[i,], ldas[j, ])

    return similarity_matrix


def load_data():
    docs = list(MovieDescriptions.objects.all())
    data = ["{}, {}, {}".format(d.title, d.genres, d.description) for d in docs]

    if len(data) == 0:
        print("No descriptions were found, run populate_sample_of_descriptions")
    return data, docs


class LdaModel(object):

    def __init__(self, min_sim=0.1):
        self.dirname, self.filename = os.path.split(os.path.abspath(__file__))
        self.min_sim = min_sim
        self.db = settings.DATABASES['default']['ENGINE']

    def train(self, data = None, docs = None):

        if data is None:
            data, docs = load_data()

        NUM_TOPICS = 10

        self.lda_path = self.dirname + '/../lda/'
        if not os.path.exists(self.lda_path):
            os.makedirs(self.lda_path)

        self.build_lda_model(data, docs, NUM_TOPICS)

    @staticmethod
    def tokenize(self, data):
        tokenizer = RegexpTokenizer(r'\w+')

        return [tokenizer.tokenize(d) for d in data]

    def build_lda_model(self, data, docs, n_topics=5):

        texts = []
        tokenizer = RegexpTokenizer(r'\w+')
        for d in tqdm(data):
            raw = d.lower()

            tokens = tokenizer.tokenize(raw)

            stopped_tokens = self.remove_stopwords(tokens)

            stemmed_tokens = stopped_tokens
            #stemmer = PorterStemmer()
            #stemmed_tokens = [stemmer.stem(token) for token in stopped_tokens]

            texts.append(stemmed_tokens)

        dictionary = corpora.Dictionary(texts)

        corpus = [dictionary.doc2bow(text) for text in texts]

        lda_model = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary,
                                                 num_topics=n_topics)

        index = similarities.MatrixSimilarity(corpus)

        self.save_lda_model(lda_model, corpus, dictionary, index)
        self.save_similarities(index, docs)

        return dictionary, texts, lda_model

    def save_lda_model(self, lda_model, corpus, dictionary, index):

        index.save(self.lda_path + 'index.lda')
        pyLDAvis.save_json(pyLDAvis.gensim.prepare(lda_model, corpus, dictionary), self.lda_path + '/../static/js/lda.json')
        print(lda_model.print_topics())
        lda_model.save(self.lda_path + 'model.lda')

        dictionary.save(self.lda_path + 'dict.lda')
        corpora.MmCorpus.serialize(self.lda_path + 'corpus.mm', corpus)

    @staticmethod
    def remove_stopwords(tokenized_data):

        en_stop = get_stop_words('en')

        stopped_tokens = [token for token in tokenized_data if token not in en_stop]
        return stopped_tokens

    def save_similarities(self, index, docs, created=datetime.now()):
        if self.db == 'django.db.backends.postgresql':
            self.save_similarities_with_postgre(index, docs, created)
        else:
            self.save_similarities_with_django(index, docs, created)

    def save_similarities_with_django(self, index, docs, created=datetime.now()):
        start_time = datetime.now()
        print(f'truncating table in {datetime.now() - start_time} seconds')

        no_saved = 0
        start_time = datetime.now()
        coo = coo_matrix(index)
        csr = coo.tocsr()

        print(f'instantiation of coo_matrix in {datetime.now() - start_time} seconds')

        conn= self.get_conn()
        cur = conn.cursor()

        cur.execute('truncate table lda_similarity')

        print(f'{coo.count_nonzero()} similarities to save')
        xs, ys = coo.nonzero()
        for x, y in zip(xs, ys):

            if x == y:
                continue

            sim = float(csr[x, y])
            x_id = str(docs[x].movie_id)
            y_id = str(docs[y].movie_id)
            if sim < self.min_sim:
                continue

            LdaSimilarity(created, x_id, y_id, sim).save()
            no_saved += 1

        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    def save_similarities_with_postgre(self, index, docs, created=datetime.now()):
        start_time = datetime.now()
        print(f'truncating table in {datetime.now() - start_time} seconds')
        sims = []
        no_saved = 0
        start_time = datetime.now()
        coo = coo_matrix(index)
        csr = coo.tocsr()

        print(f'instantiation of coo_matrix in {datetime.now() - start_time} seconds')

        query = "insert into lda_similarity (created, source, target, similarity) values %s;"

        conn= self.get_conn()
        cur = conn.cursor()

        cur.execute('truncate table lda_similarity')

        print(f'{coo.count_nonzero()} similarities to save')
        xs, ys = coo.nonzero()
        for x, y in zip(xs, ys):

            if x == y:
                continue

            sim = float(csr[x, y])
            x_id = str(docs[x].movie_id)
            y_id = str(docs[y].movie_id)
            if sim < self.min_sim:
                continue

            if len(sims) == 100000:
                psycopg2.extras.execute_values(cur, query, sims)
                sims = []
                print(f"{no_saved} saved in {datetime.now() - start_time}")

            new_similarity = (str(created), x_id, y_id, sim)
            no_saved += 1
            sims.append(new_similarity)

        psycopg2.extras.execute_values(cur, query, sims, template=None, page_size=1000)
        conn.commit()
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    @staticmethod
    def get_conn():
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            dbUsername = settings.DATABASES['default']['USER']
            dbPassword = settings.DATABASES['default']['PASSWORD']
            dbName = settings.DATABASES['default']['NAME']
            conn_str = "dbname={} user={} password={}".format(dbName,
                                                              dbUsername,
                                                              dbPassword)
            conn = psycopg2.connect(conn_str)
        elif settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            dbName = settings.DATABASES['default']['NAME']
            conn = sqlite3.connect(dbName)

        return conn
if __name__ == '__main__':
    print("Calculating lda model...")

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    data, docs = load_data()

    lda = LdaModel()
    lda.train(data, docs)
