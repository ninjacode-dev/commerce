from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime


class User(AbstractUser):
    pass

class Listings(models.Model):
    listing = models.CharField(max_length=64)
    photo = models.ImageField()
    description = models.CharField()
    starting_bid = models.FloatField()
    creation = models.DateTimeField(default=datetime.now())
    category = models.CharField(max_length=64, default="Other")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    closed = models.BooleanField(default=False)


class Bids(models.Model):
    bid = models.FloatField()
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE)
    bid_number = models.IntegerField(default= 1)


class Comments(models.Model):
    comment = models.CharField()
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE)

class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE)
