from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class AffinityGroupView(models.Model):
    IP = models.CharField(max_length=40)
    port = models.CharField(max_length=5)
    rtt = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(1000)])
    heartbeatCount = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(1000)])
class Contact(models.Model):
    groupID = models.CharField(max_length=40)
    IP = models.CharField(max_length=40)
    port = models.CharField(max_length=5)
    rtt = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(1000)])
    heartbeatCount = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(1000)])

class Filetuple(models.Model):
    fileName = models.CharField(max_length=100)
    IP = models.CharField(max_length=40)
    port = models.CharField(max_length=5)

class File(models.Model):
    file_obj = models.FileField()
    file_name = models.CharField(max_length=100)
 