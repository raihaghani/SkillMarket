from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from . import services
from .models import Listing, Offer, Review

def call_service(fn, *args):
    try:
        return fn(*args)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(getattr(exc, 'message_dict', None) or exc.messages)
    except ProtectedError:
        raise serializers.ValidationError('Engagement history prevents deletion. Archive this listing instead.')

class ListingSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    class Meta:
        model = Listing
        fields = ['id', 'seller', 'seller_name', 'title', 'description', 'category', 'starting_price', 'status', 'created_at', 'updated_at']
        read_only_fields = ['seller', 'created_at', 'updated_at']

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['id', 'listing', 'buyer', 'offered_price', 'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['buyer', 'status', 'created_at', 'updated_at']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'offer', 'reviewer', 'seller', 'rating', 'comment', 'created_at']
        read_only_fields = ['reviewer', 'seller', 'created_at']
        extra_kwargs = {'offer': {'validators': []}}

class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ['list', 'retrieve', 'reviews'] else [permissions.IsAuthenticated()]
    def get_queryset(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return Listing.objects.all()
        return services.browse(self.request.query_params.get('q', ''), self.request.query_params.get('category', ''))
    def perform_create(self, serializer):
        serializer.instance = call_service(services.save_listing, self.request.user, serializer.validated_data)
    def perform_update(self, serializer):
        serializer.instance = call_service(services.save_listing, self.request.user, serializer.validated_data, serializer.instance)
    def perform_destroy(self, instance):
        call_service(services.delete_listing, self.request.user, instance)
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        qs = Review.objects.filter(offer__listing=self.get_object())
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(ReviewSerializer(page, many=True).data)

class OfferViewSet(viewsets.GenericViewSet):
    serializer_class = OfferSerializer
    def get_queryset(self):
        user = self.request.user
        if services.has_role(user, 'Seller'):
            return Offer.objects.filter(listing__seller=user)
        return Offer.objects.filter(buyer=user)
    def list(self, request):
        return self.get_paginated_response(self.get_serializer(self.paginate_queryset(self.get_queryset()), many=True).data)
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = call_service(services.submit_offer, request.user, serializer.validated_data['listing'], serializer.validated_data)
        return Response(self.get_serializer(offer).data, status=status.HTTP_201_CREATED)
    def change(self, request, action):
        offer = call_service(services.transition, request.user, self.get_object(), action)
        return Response(self.get_serializer(offer).data)
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        return self.change(request, 'accept')
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self.change(request, 'reject')
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        return self.change(request, 'complete')

class ReviewViewSet(viewsets.GenericViewSet):
    serializer_class = ReviewSerializer
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = call_service(services.submit_review, request.user, serializer.validated_data['offer'], serializer.validated_data)
        return Response(self.get_serializer(review).data, status=status.HTTP_201_CREATED)
