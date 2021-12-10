from django.db.models import Max


def get_max_bid_price(listing):
    """
    max bid price is:
     - initial price (if listing has no bids yet)
     - max value (aggregate) of price field for all bids (if listing has bids)
    """
    bids_count = listing.bids.count()
    if bids_count == 0:
        max_bid_price = listing.price
    else:
        max_bid_price = listing.bids.all().aggregate(Max('price')).get('price__max')
    return max_bid_price
