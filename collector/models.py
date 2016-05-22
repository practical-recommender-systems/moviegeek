from django.db import models


class Log(models.Model):
    created = models.DateTimeField('date happened') #A
    user_id = models.IntegerField()
    content_id = models.IntegerField()
    event = models.CharField(max_length=200)
    session_id = models.CharField(max_length=128)
    visit_count = models.IntegerField()

    def __str__(self):
        return "user_id: {}, content_id: {}, event: {}".format(self.user_id, self.content_id, self.event) #B
