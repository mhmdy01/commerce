from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator

class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

class Listing(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    img_url = models.URLField(max_length=128, blank=True, default='')
    price = models.DecimalField(max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal(1.0))])
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    # listing could have one category or none
    # choosen by user form a provided list (created by admin)
    # TODO: to set optional fk> both blank & null are required for some reason
    # which i need to RSA later...
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name='listings')

    def __str__(self):
        return f'{self.title} ({self.price})'
