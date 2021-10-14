from django.contrib import admin

from .models import Listing, Category, Bid, Comment, Watchlist

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'img_url', 'price', 'owner', 'category', 'is_active')

class BidAdmin(admin.ModelAdmin):
    list_display = ('price', 'listing', 'user', 'is_winner')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'listing', 'user')

class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'listings_count')

    # why? cuz cant display many-to-many without querying the db
    def listings_count(self, obj):
        # return '\n'.join(listing.title for listing in obj.listings.all())
        return obj.listings.count()

admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Watchlist, WatchlistAdmin)
admin.site.register(Category)
