from django.contrib import admin

from .models import Listing, Category

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'img_url', 'price', 'owner', 'category')

admin.site.register(Listing, ListingAdmin)
admin.site.register(Category)
