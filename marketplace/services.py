"""Shared authorization and transactional writes for HTML and API callers."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from .models import Listing, Offer, Review

def has_role(user, role):
    return user.is_authenticated and user.groups.filter(name=role).exists()

def require_role(user, role):
    if not has_role(user, role):
        raise PermissionDenied(f'A {role.lower()} account is required.')

def own_listing(user, listing):
    require_role(user, 'Seller')
    if listing.seller_id != user.pk:
        raise PermissionDenied('You do not own this listing.')

def browse(query='', category=''):
    qs = Listing.objects.filter(status='ACTIVE').select_related('seller')
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category:
        qs = qs.filter(category=category)
    return qs

def save_listing(user, data, listing=None):
    require_role(user, 'Seller')
    if listing:
        own_listing(user, listing)
    else:
        listing = Listing(seller=user)
    for key in ['title', 'description', 'category', 'starting_price', 'status']:
        if key in data:
            setattr(listing, key, data[key])
    listing.full_clean()
    listing.save()
    return listing

def delete_listing(user, listing):
    own_listing(user, listing)
    if listing.offers.exists():
        raise ValidationError('This listing has offers. Set it to Draft to preserve engagement history.')
    listing.delete()

@transaction.atomic
def submit_offer(user, listing, data):
    require_role(user, 'Buyer')
    listing = Listing.objects.select_for_update().get(pk=listing.pk)
    if listing.status != 'ACTIVE' or listing.seller_id == user.pk:
        raise ValidationError('Offers require an active listing from another seller.')
    offer = Offer(listing=listing, buyer=user, offered_price=data['offered_price'], message=data['message'])
    offer.full_clean()
    offer.save()
    return offer

@transaction.atomic
def transition(user, offer, action):
    offer = Offer.objects.select_for_update().select_related('listing').get(pk=offer.pk)
    own_listing(user, offer.listing)
    transitions = {'accept': ('PENDING', 'ACCEPTED'), 'reject': ('PENDING', 'REJECTED'), 'complete': ('ACCEPTED', 'COMPLETED')}
    if action not in transitions or offer.status != transitions[action][0]:
        raise ValidationError('This action is not valid for the current offer status.')
    offer.status = transitions[action][1]
    offer.save(update_fields=['status', 'updated_at'])
    return offer

@transaction.atomic
def submit_review(user, offer, data):
    require_role(user, 'Buyer')
    offer = Offer.objects.select_for_update().select_related('listing').get(pk=offer.pk)
    if offer.buyer_id != user.pk:
        raise PermissionDenied('You can only review your own engagement.')
    if offer.status != 'COMPLETED':
        raise ValidationError('Complete the engagement before reviewing it.')
    if Review.objects.filter(offer=offer).exists():
        raise ValidationError('This engagement already has a review.')
    review = Review(offer=offer, reviewer=user, seller=offer.listing.seller, rating=data['rating'], comment=data['comment'])
    review.full_clean()
    review.save()
    return review
