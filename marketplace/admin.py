from django.contrib import admin
from .models import Listing, Offer, Review

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'status', 'starting_price']
    list_filter = ['status', 'category']
    search_fields = ['title', 'seller__username']

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'buyer', 'status', 'offered_price']
    list_filter = ['status']
    readonly_fields = ['listing', 'buyer', 'offered_price', 'message', 'status', 'created_at', 'updated_at']
    actions = ['accept_offers', 'reject_offers', 'complete_offers']
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def change_status(self, request, queryset, action):
        from .services import transition
        from django.core.exceptions import ValidationError
        for offer in queryset.select_related('listing__seller'):
            try:
                transition(offer.listing.seller, offer, action)
            except ValidationError as exc:
                self.message_user(request, f'Offer {offer.pk}: {exc.messages[0]}', level='ERROR')
    @admin.action(description='Accept pending offers')
    def accept_offers(self, request, queryset):
        self.change_status(request, queryset, 'accept')
    @admin.action(description='Reject pending offers')
    def reject_offers(self, request, queryset):
        self.change_status(request, queryset, 'reject')
    @admin.action(description='Complete accepted offers')
    def complete_offers(self, request, queryset):
        self.change_status(request, queryset, 'complete')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'reviewer', 'seller', 'rating', 'created_at']
    readonly_fields = ['offer', 'reviewer', 'seller', 'rating', 'created_at']
    def has_add_permission(self, request):
        return False
