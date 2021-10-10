from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    img_url = models.URLField(max_length=128, blank=True, default='')

    def __str__(self):
        return self.title
