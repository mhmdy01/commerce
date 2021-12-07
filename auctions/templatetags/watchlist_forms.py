from django import template


register = template.Library()

@register.inclusion_tag('auctions/watchlist_forms.html', takes_context=True)
def watchlist_forms(context):
    # watchlist details
    # when to show add-to-watchlist btn/form?
    #  - current user is logged in
    #  - listing is active
    #  - listing isn't created by current user
    #  - listing isn't currently on current user's watchlist
    # when to show rm-from-watchlist btn/form?
    #  - current user is logged in
    #  - listing is currently on current user's watchlist
    request = context['request']
    listing = context['listing']
    can_watch = (
        request.user.is_authenticated
        and listing.is_active
        and not request.user == listing.owner
        and not request.user.watchlist.listings.filter(pk=listing.id).exists()
    )
    can_unwatch = (
        request.user.is_authenticated
        and request.user.watchlist.listings.filter(pk=listing.id).exists()
    )
    return {
        'listing': listing,
        'can_watch': can_watch,
        'can_unwatch': can_unwatch
    }
