from django.contrib import admin

from .models import Listing, Category, Bid

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'img_url', 'price', 'owner', 'category')

class BidAdmin(admin.ModelAdmin):
    list_display = ('price', 'listing', 'user')

admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Category)
