from django.db import models

class Record(models.Model):
    number = models.IntegerField()
    date = models.DateField()

    class Meta:
        db_table = 'records'
