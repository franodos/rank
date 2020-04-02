from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Client(models.Model):
    number = models.IntegerField()
    grade = models.IntegerField()

    class Meta:
        ordering = ["grade"]




