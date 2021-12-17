from django.test import TestCase
from django.urls import reverse

from .models import Bid, User, Listing


# init some data
# users
foo_credentials = {'username': 'foo',  'password': 'foo'}
bar_credentials = {'username': 'bar',  'password': 'bar'}
# listings
listing_fields = {
    'title': 'listing#1 title',
    'description': 'listing#1 description',
    'img_url': '',
    'price': 10.0,
}
# bids
bid_fields = {
    'price': 100.0
}


class CreateListingTests(TestCase):
    """tests for views.create_listing"""
    def setUp(self):
        """populate db and config http client"""
        # populate db
        foo = User.objects.create_user(**foo_credentials)

        Listing.objects.create(owner=foo, **listing_fields)

        # config client
        self.user = foo
        self.user_login_credentials = foo_credentials

    def test_get_fails_notloggedin(self):
        """check that page isn't available for unauthenticated users"""
        response = self.client.get(f"/listings/new")

        # pov/response: should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_fails_notloggedin(self):
        """check that creating a listing fails if user isn't loggedin"""
        response = self.client.post(f"/listings/new")

        # pov/response: should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_fails_invalid_price(self):
        """check that creating a listing fails if price isn't valid (eg. <= 0)"""
        # must login first
        self.client.login(**self.user_login_credentials)

        listing_to_add = listing_fields
        listing_to_add['price'] = 0
        response = self.client.post(f"/listings/new", listing_to_add)

        # pov/response: should have failing status code
        self.assertEqual(response.status_code, 400)
        # pov/response: should have error msg
        self.assertTrue(hasattr(response.context['form'], 'errors'))
        self.assertIn('Ensure this value is', str(response.context['form'].errors))

    def test_works(self):
        """check that loggedin users can create new listings"""
        # must login first
        self.client.login(**self.user_login_credentials)

        listing_to_add = listing_fields
        listing_to_add['price'] = 10
        response = self.client.post(f"/listings/new", listing_to_add)

        # pov/response: should redirect to details page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(f'listings/2'))

        # pov/db: objects count should increase by one
        # and new object should exist
        self.assertEqual(Listing.objects.count(), 2)
        self.assertEqual(Listing.objects.last().title, listing_to_add['title'])


class PlaceBidTests(TestCase):
    """tests for views.place_bid"""
    def setUp(self):
        """populate db and config http client"""
        # populate db
        foo = User.objects.create_user(**foo_credentials)
        bar = User.objects.create_user(**bar_credentials)

        listing1 = Listing.objects.create(owner=foo, **listing_fields)
        listing2 = Listing.objects.create(owner=foo, is_active=False, **listing_fields)

        # config client
        self.listing_owner = foo
        self.listing_owner_login_credentials = foo_credentials

        self.not_listing_owner = bar
        self.not_listing_owner_login_credentials = bar_credentials

        self.active_listing_to_bid_on = listing1
        self.closed_listing_to_bid_on = listing2

    def test_place_bid_fails_notloggedin(self):
        """check that bidding fails if current user isn't loggedin"""
        # response = self.client.post(reverse('place_bid', args=(self.listing_to_bid_on.id,)), bid_fields)
        response = self.client.post(f"/listings/{self.active_listing_to_bid_on.id}/bid", bid_fields)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_place_bid_fails_notexist(self):
        """check that bidding fails if listing to bid on doesn't exist in db"""
        # login first
        self.client.login(**self.not_listing_owner_login_credentials)

        response = self.client.post(f"/listings/{self.active_listing_to_bid_on.id + 1}/bid", bid_fields)
        # TODO: is 400 the valid the status code?
        self.assertEqual(response.status_code, 400)

    def test_place_bid_fails_notactive(self):
        """check that bidding fails if listing to bid on isn't active"""
        # login first
        self.client.login(**self.not_listing_owner_login_credentials)

        response = self.client.post(f"/listings/{self.closed_listing_to_bid_on.id}/bid", bid_fields)
        self.assertEqual(response.status_code, 400)

    def test_place_bid_fails_isowner(self):
        """check that bidding fails if current user is listing owner"""
        # login first
        self.client.login(**self.listing_owner_login_credentials)

        response = self.client.post(f"/listings/{self.active_listing_to_bid_on.id}/bid", bid_fields)
        self.assertEqual(response.status_code, 400)

    def test_place_bid_fails_lowprice(self):
        """check that bidding fails if bid price isn't higher than all previous bids"""
        # login first
        self.client.login(**self.not_listing_owner_login_credentials)

        # set bid price
        price = listing_fields['price'] - 1

        response = self.client.post(f"/listings/{self.active_listing_to_bid_on.id}/bid", {'price': price})
        self.assertEqual(response.status_code, 400)
        # TODO: howto test response content when status != 200?
        # cuz by default django assertcontains assumes status = 200
        # self.assertContains(response, 'must be greater than')

    def test_place_bid_works(self):
        """check that a loggedin user (who isn't listing owner)
        can place a bid on an active listing
        """
        # login first
        self.client.login(**self.not_listing_owner_login_credentials)

        response = self.client.post(f"/listings/{self.active_listing_to_bid_on.id}/bid", bid_fields)
        # pov: client
        self.assertEqual(response.status_code, 200)
        # pov: db
        # self.assertEqual(Bid.objects.count(), 1)
        # self.assertEqual(Bid.objects.last().price, bid_fields['price'])
        self.assertEqual(self.active_listing_to_bid_on.bids.count(), 1)
        self.assertEqual(self.active_listing_to_bid_on.bids.last().price, bid_fields['price'])


class AcceptBidTests(TestCase):
    """tests for views.accept_max_bid"""
    def setUp(self):
        """populate db and config http client"""
        # populate db
        foo = User.objects.create_user(**foo_credentials)
        bar = User.objects.create_user(**bar_credentials)

        listing1 = Listing.objects.create(owner=foo, **listing_fields)
        listing2 = Listing.objects.create(owner=foo, is_active=False, **listing_fields)
        listing3 = Listing.objects.create(owner=foo, **listing_fields)

        Bid.objects.create(listing=listing1, user=bar, price=bid_fields['price'])

        # config client
        self.owner = foo
        self.owner_login_credentials = foo_credentials

        self.not_owner = bar
        self.not_owner_login_credentials = bar_credentials

        self.listing = listing1
        self.closed_listing = listing2
        self.nobids_listing = listing3

    def test_accept_bid_fails_notloggedin(self):
        """check that accepting a bid fails if user isn't loggedin"""
        response = self.client.post(f"/listings/{self.listing.id}/close")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_accept_bid_fails_notexist(self):
        """check that accepting a bid fails if listing doesn't exist in db"""
        # login first
        self.client.login(**self.owner_login_credentials)

        response = self.client.post(f"/listings/{self.listing.id + 100}/close")
        self.assertEqual(response.status_code, 404)

    def test_accept_bid_fails_notowner(self):
        """check that accepting a bid fails if user isn't listing owner"""
        # login first
        self.client.login(**self.not_owner_login_credentials)

        response = self.client.post(f"/listings/{self.listing.id}/close")
        self.assertEqual(response.status_code, 401)

    def test_accept_bid_fails_notactive(self):
        """check that accepting a bid fails if listing isn't active"""
        # login first
        self.client.login(**self.owner_login_credentials)

        response = self.client.post(f"/listings/{self.closed_listing.id}/close")
        self.assertEqual(response.status_code, 400)

    def test_accept_bid_fails_nobids(self):
        """check that accepting a bid fails if listing has no bids yet"""
        # login first
        self.client.login(**self.owner_login_credentials)

        response = self.client.post(f"/listings/{self.nobids_listing.id}/close")
        self.assertEqual(response.status_code, 400)

    def test_accept_bid_works(self):
        """check that listing owner can accept a winning bid"""
        # login first
        self.client.login(**self.owner_login_credentials)

        response = self.client.post(f"/listings/{self.listing.id}/close")
        # pov: client/view/template
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/listings'))
        self.assertIn(str(self.listing.id), response.url)
        # pov: db
        self.assertFalse(Listing.objects.first().is_active)
        self.assertTrue(Bid.objects.first().is_winner)
