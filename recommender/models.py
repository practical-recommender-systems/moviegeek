from django.db import models

class MovieDescriptions(models.Model):
    movie_id = models.CharField(max_length=16)
    imdb_id = models.CharField(max_length=16)
    title = models.CharField(max_length=512)
    description = models.CharField(max_length=1024)
    genres = models.CharField(max_length=512, default='')
    lda_vector = models.CharField(max_length=56, null=True)
    sim_list = models.CharField(max_length=512, default='')

    class Meta:
        db_table = 'movie_description'

    def __str__(self):
        return "{}: {}".format(self.imdb_id, self.title)


class LdaSimilarity(models.Model):
    created = models.DateField()
    source = models.CharField(max_length=16, db_index=True)
    target = models.CharField(max_length=16)
    similarity = models.DecimalField(max_digits=8, decimal_places=7)

    class Meta:
        db_table = 'lda_similarity'

    def __str__(self):
        return "[({} => {}) sim = {}]".format(self.source,
                                              self.target,
                                              self.similarity)


class Similarity(models.Model):
    created = models.DateField()
    source = models.CharField(max_length=16, db_index=True)
    target = models.CharField(max_length=16)
    similarity = models.DecimalField(max_digits=8, decimal_places=7)

    class Meta:
        db_table = 'similarity'

    def __str__(self):
        return "[({} => {}) sim = {}]".format(self.source,
                                              self.target,
                                              self.similarity)


class SeededRecs(models.Model):
    created = models.DateTimeField()
    source = models.CharField(max_length=16)
    target = models.CharField(max_length=16)
    support = models.DecimalField(max_digits=10, decimal_places=8)
    confidence = models.DecimalField(max_digits=10, decimal_places=8)
    type = models.CharField(max_length=8)

    class Meta:
        db_table = 'seeded_recs'

    def __str__(self):
        return "[({} => {}) s = {}, c= {}]".format(self.source,
                                                    self.target,
                                                    self.support,
                                                    self.confidence)

class Recs(models.Model):

    user = models.CharField(max_length=16)
    item = models.CharField(max_length=16)
    rating = models.FloatField()
    type = models.CharField(max_length=16)

    class Meta:
        db_table = 'recs'

    def __str__(self):
        return "(u,i, t)({}, {}, {})= {}".format(self.user,
                                                 self.item,
                                                 self.type,
                                                 self.rating)
