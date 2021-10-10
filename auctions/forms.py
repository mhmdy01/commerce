from django import forms

from .models import Listing

class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'img_url', 'price']
