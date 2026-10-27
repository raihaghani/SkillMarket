from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.db import models

class Listing(models.Model):
    CATEGORIES = [(v, v) for v in ['Web Development', 'Graphic Design', 'Content Writing', 'Video Editing', 'SEO', 'Digital Marketing']]
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='listings')
    title = models.CharField(max_length=200, validators=[MinLengthValidator(5)])
    description = models.TextField(max_length=10000, validators=[MinLengthValidator(20)])
    category = models.CharField(max_length=100, choices=CATEGORIES)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=8, choices=[('ACTIVE', 'Published'), ('INACTIVE', 'Draft')], default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'category']), models.Index(fields=['seller', 'status']), models.Index(fields=['title'])]
        constraints = [models.CheckConstraint(condition=models.Q(starting_price__gt=0), name='listing_positive_price'),
                       models.CheckConstraint(condition=models.Q(status__in=['ACTIVE', 'INACTIVE']), name='listing_valid_status')]
    def __str__(self):
        return self.title

class Offer(models.Model):
    STATUSES = [(s, s.title()) for s in ['PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED']]
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name='offers')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='offers')
    offered_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    message = models.TextField(max_length=5000, validators=[MinLengthValidator(10)])
    status = models.CharField(max_length=10, choices=STATUSES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['buyer', 'status']), models.Index(fields=['listing', 'status'])]
        constraints = [models.CheckConstraint(condition=models.Q(offered_price__gt=0), name='offer_positive_price'),
                       models.CheckConstraint(condition=models.Q(status__in=['PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED']), name='offer_valid_status')]

class Review(models.Model):
    offer = models.OneToOneField(Offer, on_delete=models.PROTECT, related_name='review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reviews_written')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reviews_received')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=2000, validators=[MinLengthValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name='review_rating_range')]
