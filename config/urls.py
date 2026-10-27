from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from marketplace import views, api
router = DefaultRouter()
router.register('listings', api.ListingViewSet, basename='listing')
router.register('offers', api.OfferViewSet, basename='offer')
router.register('reviews', api.ReviewViewSet, basename='review')
urlpatterns = [
    path('', views.home, name='home'), path('register/', views.register, name='register'),
    path('login/', auth.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth.LogoutView.as_view(), name='logout'), path('dashboard/', views.dashboard, name='dashboard'),
    path('listings/<int:pk>/', views.detail, name='detail'),
    path('seller/dashboard/', views.seller_dashboard, name='seller-dashboard'),
    path('buyer/dashboard/', views.buyer_dashboard, name='buyer-dashboard'),
    path('seller/listings/create/', views.listing_form, name='listing-create'),
    path('seller/listings/<int:pk>/edit/', views.listing_form, name='listing-edit'),
    path('seller/listings/<int:pk>/delete/', views.listing_delete, name='listing-delete'),
    path('offers/<int:pk>/<str:action>/', views.offer_action, name='offer-action'),
    path('reviews/<int:pk>/create/', views.review, name='review-create'),
    path('api/', include(router.urls)), path('admin/', admin.site.urls),
]
