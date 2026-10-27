from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from . import services
from .forms import RegistrationForm, ListingForm, OfferForm, ReviewForm
from .models import Listing, Offer, Review

def home(request):
    query = request.GET.get('q', '').strip()[:200]
    category = request.GET.get('category', '')
    listings = services.browse(query, category).annotate(rating=Avg('offers__review__rating')).order_by('-created_at', '-pk')
    return render(request, 'home.html', {'page': Paginator(listings, 12).get_page(request.GET.get('page')),
                  'categories': Listing.CATEGORIES, 'query': query, 'category': category})

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            user = form.save()
        except IntegrityError:
            # save() is atomic: its failed insert has rolled back before we query.
            # A concurrent registration can take the username after is_valid().
            form.validate_unique()
            if 'username' not in form.errors:
                raise  # Do not disguise unrelated database failures as duplicates.
        else:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'form.html', {'form': form, 'title': 'Your next chapter starts here', 'button': 'Create account'})

def detail(request, pk):
    listing = get_object_or_404(Listing.objects.select_related('seller'), pk=pk)
    if listing.status != 'ACTIVE' and listing.seller_id != request.user.pk:
        from django.http import Http404
        raise Http404
    form = OfferForm(request.POST or None)
    if request.method == 'POST':
        services.require_role(request.user, 'Buyer')
        if form.is_valid():
            try:
                services.submit_offer(request.user, listing, form.cleaned_data)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, 'Offer sent. Track the response in your dashboard.')
                return redirect('buyer-dashboard')
    return render(request, 'detail.html', {'listing': listing, 'form': form,
                  'reviews': Review.objects.filter(offer__listing=listing).select_related('reviewer')})

@login_required
def dashboard(request):
    if services.has_role(request.user, 'Seller'):
        return redirect('seller-dashboard')
    if request.user.is_staff:
        return redirect('/admin/')
    return redirect('buyer-dashboard')

@login_required
def seller_dashboard(request):
    services.require_role(request.user, 'Seller')
    return render(request, 'seller.html', {'listings': request.user.listings.all(),
        'offers': Offer.objects.filter(listing__seller=request.user).select_related('listing', 'buyer')})

@login_required
def buyer_dashboard(request):
    services.require_role(request.user, 'Buyer')
    return render(request, 'buyer.html', {'offers': request.user.offers.select_related('listing', 'listing__seller', 'review')})

@login_required
def listing_form(request, pk=None):
    services.require_role(request.user, 'Seller')
    listing = get_object_or_404(Listing, pk=pk) if pk else None
    if listing:
        services.own_listing(request.user, listing)
    form = ListingForm(request.POST or None, instance=listing)
    if request.method == 'POST' and form.is_valid():
        try:
            services.save_listing(request.user, form.cleaned_data, listing)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Your listing has been saved.')
            return redirect('seller-dashboard')
    return render(request, 'form.html', {'form': form, 'title': 'Edit your service' if pk else 'Share what you do best', 'button': 'Save listing'})

@require_POST
@login_required
def listing_delete(request, pk):
    try:
        services.delete_listing(request.user, get_object_or_404(Listing, pk=pk))
        messages.success(request, 'Listing deleted.')
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
    return redirect('seller-dashboard')

@require_POST
@login_required
def offer_action(request, pk, action):
    try:
        services.transition(request.user, get_object_or_404(Offer, pk=pk), action)
        messages.success(request, 'Offer updated.')
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
    return redirect('seller-dashboard')

@login_required
def review(request, pk):
    services.require_role(request.user, 'Buyer')
    offer = get_object_or_404(Offer, pk=pk, buyer=request.user)
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.submit_review(request.user, offer, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Thank you. Your review is published.')
            return redirect('buyer-dashboard')
    return render(request, 'form.html', {'form': form, 'title': 'How did it go?', 'button': 'Publish review'})
