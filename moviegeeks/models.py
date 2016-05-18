from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=64)

class Movie(models.Model):
    movie_id = models.CharField(max_length=8, unique=True, primary_key=True)
    title = models.CharField(max_length=128)
    year = models.IntegerField(null=True)
    genres = models.ManyToManyField(Genre, related_name='is_in', db_table='movie_genre')

    def __str__(self):
        return self.title
