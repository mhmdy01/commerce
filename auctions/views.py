from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Bid, User, Listing, Category
from .forms import NewListingForm, NewBidForm

def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required(login_url='login')
def create_listing(request):
    if request.method == 'POST':
        form = NewListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return redirect(reverse('display_listing', kwargs={'listing_id': listing.id}))
        else:
            return render(request, 'auctions/create_listing.html', {
                'form': form
            })
    else:
        return render(request, 'auctions/create_listing.html', {
            'form': NewListingForm()
        })

def display_listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    
    # must filter bids for current listing only> listing.bids
    bids_count = listing.bids.all().count()
    # print('all_bids:', bids_count)
    if not bids_count:
        max_bid = listing.price
    else:
        # must filter bids for current listing only> listing.bids
        # not max bid (in general)> Bid.objects.all
        max_bid = listing.bids.all().aggregate(Max('price')).get('price__max')
    # print('max_bid:', max_bid)
    
    show_bid_form = request.user.is_authenticated and listing.owner != request.user
    show_bids = request.user.is_authenticated and listing.owner == request.user
    # print('show_bid_form:', show_bid_form)
    # print('show_bids:', show_bids)
    
    # if placing a bid
    if request.method == 'POST':
        form = NewBidForm(request.POST)
        # automatic validation #
        if form.is_valid():
            bid = form.save(commit=False)
            
            # manual validation #
            # bid value must be > max_bid.. which is:
            # price      (if no bids)
            # max(price) (if there bids)

            # invalid bid
            if bid.price <= max_bid:
                error = f"Your bid (${bid.price}) must be greater than the current max bid of (${max_bid})"
                return render(request, 'auctions/listing.html', {
                    'listing': listing,
                    'bids_count': bids_count,
                    'show_bid_form': show_bid_form,
                    'show_bids': show_bids,
                    'bid_form': form,
                    'bid_form_error': error,
                })
            # valid bid
            else:
                bid.user = request.user
                bid.listing = listing
                bid.save()
                return redirect(reverse('display_listing', kwargs={'listing_id': listing_id}))
        else:
            return render(request, 'auctions/listing.html', {
                'listing': listing,
                'bids_count': bids_count,
                'show_bid_form': show_bid_form,
                'show_bids': show_bids,
                'bid_form': form,
            })

    return render(request, 'auctions/listing.html', {
        'listing': listing,
        'bids_count': bids_count,
        'max_bid': max_bid,
        'show_bid_form': show_bid_form,
        'show_bids': show_bids,
        'bid_form': NewBidForm()
    })

def user_profile(request, username):
    user = User.objects.get(username=username)
    return render(request, 'auctions/user.html', {
        'user_obj': user,
        'listings': user.listings.all(),
    })

def display_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    return render(request, 'auctions/category.html', {
        'category': category,
        'listings': category.listings.all(),
    })

def all_categories(request):
    return render(request, 'auctions/categories.html', {
        'categories': Category.objects.all(),
    })

