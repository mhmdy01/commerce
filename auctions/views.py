from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST

from . import utils
from .models import User, Listing, Category, Watchlist
from .forms import NewBidForm, NewCommentForm


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


class CreateListingView(LoginRequiredMixin, CreateView):
    """Create a new listing."""
    model = Listing
    fields = ['title', 'description', 'img_url', 'price', 'category']
    template_name = 'auctions/create_listing.html'
    login_url = 'login'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


def display_listing(request, listing_id):
    """Display details of specific listing (`listing_id`)"""
    listing = Listing.objects.get(pk=listing_id)

    # bidding details
    bids_count = listing.bids.count()
    max_bid_price = utils.get_max_bid_price(listing)
    # what bid-related parts can user see?
    # for active listings:
    #   - #bids: all users (loggedin or not)
    #   - accept_bid form: loggedin, owner
    #   - place_bid form: loggedin, not owner
    # for closed listings:
    #   - inform, congrats (eg. you bought...): user won
    #   - only inform (eg. sold for...): user didn't win

    # when to show bids count?
    #   - listing is active
    can_see_bids_count = listing.is_active

    # when to show bidding form?
    #   - user is logged in
    #   - user isn't listing owner
    #   - listing is active
    can_place_bid = (
        request.user.is_authenticated
        and listing.owner != request.user
        and listing.is_active
    )

    # when to show accept_bid/close_listing form?
    #  - user is logged in
    #  - user is listing owner
    #  - listing is active
    #  - THERE MUST BE at least one bid on listing
    can_accept_bid = (
        request.user.is_authenticated
        and listing.owner == request.user
        and listing.is_active
        and bids_count > 0
    )

    # when to congrats user?
    #   - listing is closed
    #   - they placed (owner of) winning bid
    # NOTE:
    # - if listing is closed there must be a winning bid
    # - and that winning bid is always the last bid
    latest_bid = listing.bids.last()
    inform_and_congrats_user = (
        not listing.is_active
        and latest_bid.user == request.user
    )
    # when to show winning bid?
    #   - listing is closed
    #   - user isn't owner of winning bid
    inform_but_not_congrats = (
        not listing.is_active
        and latest_bid.user != request.user
    )

    # commenting details
    comments = listing.comments.all()
    # what comment-related parts can user see?
    # for active listings:
    #   - commenting form: loggedin users (owner, others)
    #   - comments: all users (loggedin, not)
    # for closed listings:
    #   - comments: all users (loggedin, not)

    # when to show commenting form?
    #  - user is logged in
    #  - listing is active
    can_write_comment = (
        request.user.is_authenticated
        and listing.is_active
    )

    return render(request, 'auctions/listing.html', {
        'listing': listing,
        'bids_count': bids_count,
        'max_bid': max_bid_price,
        'can_see_bids_count': can_see_bids_count,
        'can_place_bid': can_place_bid,
        'can_accept_bid': can_accept_bid,
        'bid_form': NewBidForm(max_bid_price=None),
        'inform_and_congrats_user': inform_and_congrats_user,
        'inform_but_not_congrats': inform_but_not_congrats,
        'comments': comments,
        'can_write_comment': can_write_comment,
        'comment_form': NewCommentForm(),
    })


@login_required(login_url='login')
@require_POST
def place_bid(request, listing_id):
    """Place a new bid on specific listing (`listing_id`)."""
    # get listing and handle if not found
    listing = get_object_or_404(Listing, pk=listing_id)

    # reject bidding if:
    #  - user is listing owner
    #  - listing is closed
    is_owner = listing.owner == request.user
    is_closed = not listing.is_active
    if is_closed or is_owner:
        return HttpResponseBadRequest()

    # validate bidding form
    max_bid_price = utils.get_max_bid_price(listing)
    form = NewBidForm(request.POST, max_bid_price=max_bid_price)
    if form.is_valid():
        # if valid price
        # create a new bid
        form.instance.user = request.user
        form.instance.listing = listing
        form.save()
        # and send new bids count to client
        # do we really need to query db each time?
        # cant increment whatever user sees instead?
        # anyway, whenver user refresh page
        # all correct data will be there
        return HttpResponse()
    else:
        # access form errors and send to client
        errors = form.errors.as_json(escape_html=True)
        return JsonResponse(errors, safe=False, status=400)


@login_required(login_url='login')
@require_POST
def accept_max_bid(request, listing_id):
    """
    Accept current max bid on specific listing (`listing_id`) as a winner.
    And mark listing as closed.
    """
    # get listing and handle if not found
    listing = get_object_or_404(Listing, pk=listing_id)

    # can't accept a bid if:
    #  - user isn't listing owner
    #  - listing is closed
    #  - listing has no bids yet
    not_owner = listing.owner != request.user
    is_closed = not listing.is_active
    has_no_bids = listing.bids.count() == 0
    if not_owner:
        return HttpResponse(status=401)
    if is_closed or has_no_bids:
        return HttpResponseBadRequest()

    # find max bid and mark it as winner
    # why last bid?
    # because bids have increasing prices
    # we ensure that when inserting a new bid
    # (new bid must be greater than all previous bids)
    max_bid = listing.bids.last()
    max_bid.is_winner = True
    max_bid.save()

    # close listing
    listing.is_active = False
    listing.save()

    # redirect to listing_details page
    return redirect(reverse('display_listing', args=(listing_id,)))


@login_required(login_url='login')
@require_POST
def add_comment(request, listing_id):
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
@require_POST
def add_to_watchlist(request, listing_id):
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
@require_POST
def remove_from_watchlist(request, listing_id):
    # get listing and handle if not found
    listing = get_object_or_404(Listing, pk=listing_id)

    # reject unwatching listings that NOT currenlty on user's watchlist
    if not request.user.watchlist.listings.filter(pk=listing_id).exists():
        return HttpResponseBadRequest()

    # remove listing from user's watchlist
    request.user.watchlist.listings.remove(listing)

    # redirect to listing details page
    return redirect(reverse('display_listing', args=(listing_id,)))


def user_profile(request, username):
    user = User.objects.get(username=username)
    return render(request, 'auctions/user.html', {
        'user_obj': user,
        'listings': user.listings.all(),
    })


class AllCategoriesView(ListView):
    """List all categories on website.
    Each category is displayed as link that leads to category page.
    """
    model = Category
    context_object_name = 'categories'
    template_name = 'auctions/categories.html'


class OneCategoryView(DetailView):
    """Display category page.
    A category page lists all active listing in that category.
    """
    model = Category
    template_name = 'auctions/category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['listings'] = context['category'].listings.filter(is_active=True)
        return context


class WatchlistView(LoginRequiredMixin, ListView):
    login_url = 'login'
    template_name = 'auctions/watchlist.html'
    context_object_name = 'listings'

    def get_queryset(self):
        return self.request.user.watchlist.listings.all()
