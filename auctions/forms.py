from django import forms
from django.core.exceptions import ValidationError

from .models import Bid, Comment


class NewBidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['price']

    def __init__(self, *args, **kwargs):
        self.max_bid_price = kwargs.pop('max_bid_price')
        super(NewBidForm, self).__init__(*args, **kwargs)
        # self.fields['price'].validators = [MinValueValidator(max_bid_price)]

    def clean_price(self):
        """validate bid price.
        MUST BE GREATER THAN max bid so far.
        """
        data = self.cleaned_data['price']
        if data <= self.max_bid_price:
            error_msg = f"Your bid (${data}) must be greater than the current max bid of (${self.max_bid_price})"
            raise ValidationError(error_msg)
        return data


class NewCommentForm(forms.ModelForm):
    # trick used to hide field label @form
    # cuz its repetiting (keep saying comment, add comment, leave a comment...)
    # why pain? just trying something new
    content = forms.CharField(widget=forms.Textarea, label='')
    class Meta:
        model = Comment
        fields = ['content']
