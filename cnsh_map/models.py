from django.conf import settings
from django.db import models
from django.utils import timezone

class Location(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class Person(models.Model):
    location = models.ForeignKey("Location", on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    note = models.CharField(max_length=100, blank=True)
    Registered_time = models.DateTimeField(default=timezone.now)
   
    def __str__(self):
        return self.name