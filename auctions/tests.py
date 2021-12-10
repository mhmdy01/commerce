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
        self.assertEqual(response.status_code, 302)
        # pov: db
        # self.assertEqual(Bid.objects.count(), 1)
        # self.assertEqual(Bid.objects.last().price, bid_fields['price'])
        self.assertEqual(self.active_listing_to_bid_on.bids.count(), 1)
        self.assertEqual(self.active_listing_to_bid_on.bids.last().price, bid_fields['price'])
