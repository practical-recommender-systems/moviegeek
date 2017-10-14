import os
import sys

import psycopg2
from scipy.sparse import coo_matrix

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django
from datetime import datetime


import logging
import json
import numpy as np

import pyLDAvis
import pyLDAvis.gensim

import operator
import math

from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer
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

    def train(self, data, docs):

        NUM_TOPICS = 10
        n_products = len(data)
        self.lda_path = self.dirname + '/../lda/'
        if not os.path.exists(self.lda_path):
            os.makedirs(self.lda_path)

        dictionary, texts, lda_model = self.build_lda_model(data, docs, NUM_TOPICS)

    def tokenize(data):
        tokenizer = RegexpTokenizer(r'\w+')

        return [tokenizer.tokenize(d) for d in data]

    def build_lda_model(self, data, docs, n_topics=5):

        texts = []
        tokenizer = RegexpTokenizer(r'\w+')
        for d in data:
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

        index.save(self.lda_path + 'index.lda')
        cor = coo_matrix(index)
        cor = cor.multiply(cor > self.min_sim)
        print(cor.count_nonzero())
        for i in range(len(texts)):
            lda_vector = corpus[i]
            #docs[i].sim_list = index[lda_vector]
            docs[i].lda_vector = i
            docs[i].save()

        self.save_lda_model(lda_model, corpus, dictionary)
        self.save_similarities(corpus, index, docs)

        return dictionary, texts, lda_model

    def save_lda_model(self, lda_model, corpus, dictionary):
        pyLDAvis.save_json(pyLDAvis.gensim.prepare(lda_model, corpus, dictionary), self.lda_path + '/../static/js/lda.json')
        print(lda_model.print_topics())
        lda_model.save(self.lda_path + 'model.lda')

        dictionary.save(self.lda_path + 'dict.lda')
        corpora.MmCorpus.serialize(self.lda_path + 'corpus.mm', corpus)

    def remove_stopwords(self, tokenized_data):
        en_stop = get_stop_words('en')

        stopped_tokens = [token for token in tokenized_data if token not in en_stop]
        return stopped_tokens

    def save_similarities(self, corpus, index, docs, created=datetime.now()):

        start_time = datetime.now()
        print(f'truncating table in {datetime.now() - start_time} seconds')
        sims = []
        no_saved = 0
        start_time = datetime.now()
        coo = coo_matrix(index)
        csr = coo.tocsr()

        print(f'instantiation of coo_matrix in {datetime.now() - start_time} seconds')

        query = "insert into lda_similarity (created, source, target, similarity) values %s;"

        conn = psycopg2.connect("dbname=moviegeek user=postgres password=hullo1!")
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


if __name__ == '__main__':
    print("Calculating lda model...")

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    data, docs = load_data()

    lda = LdaModel()
    lda.train(data, docs)
