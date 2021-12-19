from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listings/new", views.CreateListingView.as_view(), name="create_listing"),
    path("listings/<int:listing_id>", views.display_listing, name="display_listing"),
    path("users/<str:username>", views.ProfileView.as_view(), name="user_profile"),
    path("categories/<int:pk>", views.OneCategoryView.as_view(), name="display_category"),
    path("categories", views.AllCategoriesView.as_view(), name="all_categories"),

    path("listings/<int:listing_id>/bid", views.place_bid, name="place_bid"),

    path("listings/<int:listing_id>/close", views.accept_max_bid, name="accept_max_bid"),

    path("listings/<int:listing_id>/comment", views.add_comment, name="add_comment"),

    path("listings/<int:listing_id>/watch", views.add_to_watchlist, name="add_to_watchlist"),
    path("listings/<int:listing_id>/unwatch", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("watchlist", views.WatchlistView.as_view(), name="display_watchlist"),
]
