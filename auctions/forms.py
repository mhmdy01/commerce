from django import forms
from django.db.models import fields

from .models import Listing, Bid

class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'img_url', 'price', 'category']

class NewBidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['price']
