from django import forms
from django.db.models import fields

from .models import Listing, Bid, Comment

class NewListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'img_url', 'price', 'category']

class NewBidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['price']

class NewCommentForm(forms.ModelForm):
    # trick used to hide field label @form
    # cuz its repetiting (keep saying comment, add comment, leave a comment...)
    # why pain? just trying something new
    content = forms.CharField(widget=forms.Textarea, label='')
    class Meta:
        model = Comment
        fields = ['content']
