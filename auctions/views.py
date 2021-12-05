from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Bid, User, Listing, Category, Watchlist
from .forms import NewListingForm, NewBidForm, NewCommentForm

def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(is_active=True)
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
        
        # create watchlist once user signed up successfully
        user_watchlist = Watchlist(user=request.user)
        user_watchlist.save()

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
    comments = listing.comments.all()
    
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
    
    show_bid_form = (
        request.user.is_authenticated
        and listing.owner != request.user
        and listing.is_active
    )
    show_bids = (
        request.user.is_authenticated
        and listing.owner == request.user
        and listing.is_active
    )
    # print('show_bid_form:', show_bid_form)
    # print('show_bids:', show_bids)
    
    # only available if at least one bid? and not already close
    can_close_listing = (
        show_bids
        and bids_count > 0
    )
    # TODO/tradeoffs: short-circuting using and vs. implicit conditions @filters
    ##### THIS BAD #####
    # no need to check authentication (ie. req.user.is_auth)
    # cuz we filter by current user and if not authenticated, filtering would fail
    # no need to check for listing status (ie. listing.is_active)
    # cuz we filter by winning bid and if there's any,
    # that means the listing is already closed
    # did_current_user_win = listing.bids.filter(user=request.user, is_winner=True).count() == 1
    ##### ------ #####
    ##### THIS GOOD #####
    did_current_user_win = (
        request.user.is_authenticated
        and not listing.is_active
        and listing.bids.filter(user=request.user, is_winner=True).count() == 1
    )

    show_comments_form = (
        request.user.is_authenticated
        and listing.is_active
    )

    # watchlist details
    # does the user's watchlist include the current listing?
    user_watchlist = request.user.watchlist
    is_watchlisted = user_watchlist.listings.filter(pk=listing_id).exists()
    
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
        'comments': comments,
        'bids_count': bids_count,
        'max_bid': max_bid,
        'show_bid_form': show_bid_form,
        'show_bids': show_bids,
        'show_comments_form': show_comments_form,
        'can_close_listing': can_close_listing,
        'did_current_user_win': did_current_user_win,
        'is_watchlisted': is_watchlisted,
        'bid_form': NewBidForm(),
        'comment_form': NewCommentForm()
    })

def close_listing(request, listing_id):
    if not request.method == 'POST':
        return HttpResponseForbidden()
    listing = Listing.objects.get(pk=listing_id)
    listing.is_active = False
    listing.save()
    # find winner bid for this listing (the one with max price)
    price_of_max_bid = listing.bids.all().aggregate(Max('price')).get('price__max')
    max_bid = listing.bids.get(price=price_of_max_bid)
    max_bid.is_winner = True
    max_bid.save()
    return redirect(reverse('display_listing', kwargs={'listing_id': listing_id}))

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
        'listings': category.listings.filter(is_active=True),
    })

def all_categories(request):
    return render(request, 'auctions/categories.html', {
        'categories': Category.objects.all(),
    })


@login_required(login_url='login')
def add_comment(request, listing_id):
    # reject non-POST requests
    if not request.method == 'POST':
        return HttpResponseNotAllowed(['POST'])

    # get listing and handle if not found
    listing = get_object_or_404(Listing, pk=listing_id)

    # reject comments on closed listings
    if not listing.is_active:
        return HttpResponseBadRequest()

    # process form
    form = NewCommentForm(request.POST)
    if form.is_valid():
        form.instance.listing = listing
        form.instance.user = request.user
        form.save()
        return redirect(reverse('display_listing', args=(listing_id,)))
    return HttpResponseBadRequest()


@login_required(login_url='login')
def add_to_watchlist(request, listing_id):
    # reject non-POST requests
    if not request.method == 'POST':
        return HttpResponseNotAllowed(['POST'])

    # get listing and handle if not found
    listing = get_object_or_404(Listing, pk=listing_id)

    # reject watching:
    # - closed listings
    # - one's own listings
    # - listings that are already/currently on user's watchlist
    is_closed = not listing.is_active
    is_owner = request.user == listing.owner
    is_on_wachlist = request.user.watchlist.listings.filter(pk=listing_id).exists()
    if is_closed or is_owner or is_on_wachlist:
        return HttpResponseBadRequest()

    # add listing to user's watchlist
    request.user.watchlist.listings.add(listing)

    # redirect to listing details page
    return redirect(reverse('display_listing', args=(listing_id,)))


@login_required(login_url='login')
def remove_from_watchlist(request, listing_id):
    # reject non-POST requests
    if not request.method == 'POST':
        return HttpResponseNotAllowed(['POST'])

    # get listing and handle if not found
    listing = get_object_or_404(Listing, pk=listing_id)

    # reject unwatching listings that NOT currenlty on user's watchlist
    if not request.user.watchlist.listings.filter(pk=listing_id).exists():
        return HttpResponseBadRequest()

    # remove listing from user's watchlist
    request.user.watchlist.listings.remove(listing)

    # redirect to listing details page
    return redirect(reverse('display_listing', args=(listing_id,)))

login_required(login_url='login')
def display_watchlist(request):
    return render(request, 'auctions/watchlist.html', {
        'listings': Watchlist.objects.get(user=request.user).listings.all()
    })
