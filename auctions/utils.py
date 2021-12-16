from django.db.models import Max


def get_max_bid_price(listing):
    """Get price of max bid on specific `listing`.
    max price is:
    - if listing has no bids yet: listing initial price
    - if listing has bids: price of most recent one
    """
    max_bid = listing.bids.last()
    if max_bid is None:
        max_bid_price = listing.price
    else:
        max_bid_price = max_bid.price
    return max_bid_price
