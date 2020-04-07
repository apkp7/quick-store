from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class AffinityGroupView(models.Model):
    IP = models.CharField(max_length=40)
    port = models.CharField(max_length=5)
    rtt = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    heartbeatCount = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    timestamp = models.IntegerField(default=0, validators=[MinValueValidator(0)])

class Contact(models.Model):
    groupID = models.CharField(max_length=40)
    IP = models.CharField(max_length=40)
    port = models.CharField(max_length=5)
    rtt = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    heartbeatCount = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    timestamp = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    actual = models.BooleanField(default=False) 

class Filetuple(models.Model):
    fileName = models.CharField(max_length=100)
    IP = models.CharField(max_length=40)
    port = models.CharField(max_length=5)
    heartbeatCount = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    timestamp = models.IntegerField(default=0, validators=[MinValueValidator(0)])

class Misc(models.Model):
    name = models.CharField(max_length=40)
    count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    groupID = models.CharField(default='-1', max_length=40)

class File(models.Model):
    file_obj = models.FileField()
    file_name = models.CharField(max_length=100)
