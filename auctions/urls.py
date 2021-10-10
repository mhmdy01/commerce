from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listings/new", views.create_listing, name="create_listing"),
    path("listings/<int:listing_id>", views.display_listing, name="display_listing"),
    path("users/<str:username>", views.user_profile, name="user_profile"),
    path("categories/<int:category_id>", views.display_category, name="display_category"),
    path("categories", views.all_categories, name="all_categories"),
]
