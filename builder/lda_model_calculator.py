import os
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
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

from recommender.models import MovieDescriptions


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
    similarity_matrix = np.zeros((size,size))

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

    def train(self, data, docs):

        NUM_TOPICS = 50
        n_products = len(data)
        self.lda_path = './../lda/'
        if not os.path.exists(self.lda_path):
            os.makedirs(self.lda_path)

        dictionary, texts, lda_model = self.build_lda_model(data, docs, NUM_TOPICS)

    def tokenize(data):
        tokenizer = RegexpTokenizer(r'\w+')

        return [tokenizer.tokenize(d) for d in data]


    def build_lda_model(self, data, docs, n_topics=5):

        texts = []
        tokenizer = RegexpTokenizer(r'\w+')
        for data in data:
            raw = data.lower()

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
        for i in range(len(texts)):
            docs[i].lda_vector = i
            docs[i].save()

        self.save_lda_model(lda_model, corpus, dictionary)

        return dictionary, texts, lda_model

    def save_lda_model(self, lda_model, corpus, dictionary):
        pyLDAvis.save_json(pyLDAvis.gensim.prepare(lda_model, corpus, dictionary), './../static/js/lda.json')
        print(lda_model.print_topics())
        lda_model.save(self.lda_path + 'model.lda')

        dictionary.save(self.lda_path + 'dict.lda')
        corpora.MmCorpus.serialize(self.lda_path + 'corpus.mm', corpus)

    def remove_stopwords(self, tokenized_data):
        en_stop = get_stop_words('en')

        stopped_tokens = [token for token in tokenized_data if token not in en_stop]
        return stopped_tokens

if __name__ == '__main__':
    print("Calculating lda model...")


    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    data, docs = load_data()

    lda = LdaModel()
    lda.train(data, docs)
