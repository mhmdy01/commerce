from django.contrib import admin

from .models import Listing, Category, Bid, Comment

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'img_url', 'price', 'owner', 'category', 'is_active')

class BidAdmin(admin.ModelAdmin):
    list_display = ('price', 'listing', 'user')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'listing', 'user')

admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Category)
