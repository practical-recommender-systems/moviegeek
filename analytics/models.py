from django.db import models


class Rating(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    movie_id = models.CharField(max_length=8)
    rating = models.DecimalField(decimal_places=2, max_digits=3)
    rating_timestamp = models.DateTimeField()

    def __str__(self):
        return "user_id: {}, content_id: {}, rating: {}".format(self.user_id, self.movie_id, self.rating) #B

