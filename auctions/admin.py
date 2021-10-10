from django.contrib import admin

from .models import Listing

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'img_url')

admin.site.register(Listing, ListingAdmin)
