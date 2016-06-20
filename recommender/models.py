from django.db import models

class MovieDescriptions(models.Model):
    movie_id = models.CharField(max_length=8)
    imdb_id = models.CharField(max_length=8)
    title = models.CharField(max_length=56)
    description = models.CharField(max_length=512)

    def __str__(self):
        return self.imdb_id


class SeededRecs(models.Model):
    created = models.DateTimeField()
    source = models.CharField(max_length=8)
    target = models.CharField(max_length=8)
    support = models.DecimalField(max_digits=8, decimal_places=8)
    confidence = models.DecimalField(max_digits=8, decimal_places=8)
    type = models.CharField(max_length=8)

    class Meta:
        db_table = 'seeded_recs'

    def __str__(self):
        return "[({} => {}) s = {}, c= {}]".format(self.source,
                                                    self.target,
                                                    self.support,
                                                    self.confidence)