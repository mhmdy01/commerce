from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator

class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    img_url = models.URLField(max_length=128, blank=True, default='')
    price = models.DecimalField(max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal(1.0))])

    def __str__(self):
        return f'{self.title} ({self.price})'
