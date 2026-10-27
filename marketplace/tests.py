from django.contrib.auth.models import User, Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Listing, Offer, Review
from . import services

@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class MarketplaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user('seller', password='CorrectHorse!532')
        cls.buyer = User.objects.create_user('buyer', password='CorrectHorse!532')
        cls.other = User.objects.create_user('other', password='CorrectHorse!532')
        cls.stranger = User.objects.create_user('stranger', password='CorrectHorse!532')
        for user, role in [(cls.seller,'Seller'),(cls.other,'Seller'),(cls.buyer,'Buyer'),(cls.stranger,'Buyer')]:
            user.groups.add(Group.objects.get_or_create(name=role)[0])
        cls.data = dict(title='Build a thoughtful Django website', description='A carefully crafted website for your independent business.', category='Web Development', starting_price='150.00', status='ACTIVE')
        cls.listing = services.save_listing(cls.seller, cls.data)
    def setUp(self):
        self.api = APIClient()
    def auth(self, user):
        self.api.force_authenticate(user)
    def offer(self):
        return services.submit_offer(self.buyer, self.listing, {'offered_price':'100.00','message':'Please build a portfolio website.'})
    def completed(self):
        offer = self.offer()
        services.transition(self.seller, offer, 'accept')
        return services.transition(self.seller, offer, 'complete')
    def review_data(self, offer, rating=5):
        return {'offer':offer.pk,'rating':rating,'comment':'Excellent communication and thoughtful work.'}
    def test_01_seller_create(self):
        self.auth(self.seller)
        r = self.api.post('/api/listings/', self.data)
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.data['seller'],self.seller.pk)
    def test_02_buyer_cannot_create(self):
        self.auth(self.buyer)
        self.assertEqual(self.api.post('/api/listings/',self.data).status_code,403)
    def test_03_other_seller_cannot_edit(self):
        self.auth(self.other)
        self.assertEqual(self.api.patch(f'/api/listings/{self.listing.pk}/',{'title':'Hijacked listing'}).status_code,403)
    def test_04_owner_edit(self):
        self.auth(self.seller)
        self.assertEqual(self.api.patch(f'/api/listings/{self.listing.pk}/',{'title':'An updated service title'}).status_code,200)
    def test_05_delete_unused(self):
        self.auth(self.seller)
        self.assertEqual(self.api.delete(f'/api/listings/{self.listing.pk}/').status_code,204)
    def test_06_protect_history(self):
        self.offer(); self.auth(self.seller)
        self.assertEqual(self.api.delete(f'/api/listings/{self.listing.pk}/').status_code,400)
        self.assertTrue(Offer.objects.exists())
    def test_07_submit_offer(self):
        self.auth(self.buyer)
        r=self.api.post('/api/offers/',{'listing':self.listing.pk,'offered_price':'0.01','message':'Please help with my website.','status':'COMPLETED','buyer':self.stranger.pk})
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.data['status'],'PENDING')
        self.assertEqual(r.data['buyer'],self.buyer.pk)
    def test_08_invalid_prices(self):
        self.auth(self.buyer)
        for price in ['0','-1','100000000','abc','NaN','0.001']:
            with self.subTest(price=price):
                self.assertEqual(self.api.post('/api/offers/',{'listing':self.listing.pk,'offered_price':price,'message':'Please help with my website.'}).status_code,400)
    def test_09_seller_cannot_offer(self):
        self.auth(self.other)
        self.assertEqual(self.api.post('/api/offers/',{'listing':self.listing.pk,'offered_price':'100','message':'Please help with my website.'}).status_code,403)
    def test_10_inactive_listing(self):
        self.listing.status='INACTIVE'; self.listing.save(); self.auth(self.buyer)
        self.assertEqual(self.api.get(f'/api/listings/{self.listing.pk}/').status_code,404)
        self.assertEqual(self.api.post('/api/offers/',{'listing':self.listing.pk,'offered_price':'100','message':'Please help with my website.'}).status_code,400)
    def test_11_accept_complete_review(self):
        offer=self.offer(); self.auth(self.seller)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/accept/').data['status'],'ACCEPTED')
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/complete/').data['status'],'COMPLETED')
        self.auth(self.buyer)
        self.assertEqual(self.api.post('/api/reviews/',self.review_data(offer)).status_code,201)
    def test_12_reject_blocks_complete(self):
        offer=self.offer(); self.auth(self.seller)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/reject/').status_code,200)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/complete/').status_code,400)
    def test_13_pending_cannot_complete(self):
        offer=self.offer(); self.auth(self.seller)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/complete/').status_code,400)
    def test_14_accept_retry(self):
        offer=self.offer(); self.auth(self.seller)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/accept/').status_code,200)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/accept/').status_code,400)
    def test_15_buyer_cannot_accept(self):
        offer=self.offer(); self.auth(self.buyer)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/accept/').status_code,403)
    def test_16_other_seller_cannot_accept(self):
        offer=self.offer(); self.auth(self.other)
        self.assertEqual(self.api.post(f'/api/offers/{offer.pk}/accept/').status_code,404)
    def test_17_private_offers(self):
        self.offer(); self.auth(self.stranger)
        self.assertEqual(self.api.get('/api/offers/').data['count'],0)
    def test_18_review_before_completion(self):
        offer=self.offer(); self.auth(self.buyer)
        self.assertEqual(self.api.post('/api/reviews/',self.review_data(offer)).status_code,400)
    def test_19_unrelated_review(self):
        offer=self.completed(); self.auth(self.stranger)
        self.assertEqual(self.api.post('/api/reviews/',self.review_data(offer)).status_code,403)
    def test_20_duplicate_review(self):
        offer=self.completed(); self.auth(self.buyer)
        self.assertEqual(self.api.post('/api/reviews/',self.review_data(offer)).status_code,201)
        self.assertEqual(self.api.post('/api/reviews/',self.review_data(offer)).status_code,400)
        self.assertEqual(Review.objects.count(),1)
    def test_21_rating_boundaries_valid(self):
        self.auth(self.buyer)
        for rating in [1,5]:
            self.assertEqual(self.api.post('/api/reviews/',self.review_data(self.completed(),rating)).status_code,201)
    def test_22_rating_boundaries_invalid(self):
        offer=self.completed(); self.auth(self.buyer)
        for rating in [0,6,-1,1.5]:
            self.assertEqual(self.api.post('/api/reviews/',self.review_data(offer,rating)).status_code,400)
    def test_23_search_regression(self):
        self.completed()
        self.assertEqual(self.api.get('/api/listings/?q=django&category=Web%20Development').data['count'],1)
        self.assertEqual(self.api.get('/api/listings/?q=unknown').data['count'],0)
        self.assertEqual(self.api.get('/api/listings/?category=SEO').data['count'],0)
    def test_24_anonymous_write_denied(self):
        self.assertEqual(self.api.post('/api/listings/',self.data).status_code,403)
        self.assertEqual(self.api.get('/api/offers/').status_code,403)
    def test_25_csrf_enforced(self):
        client=APIClient(enforce_csrf_checks=True); client.force_login(self.seller)
        self.assertEqual(client.post('/api/listings/',self.data).status_code,403)
    def test_26_registration_roles_and_privilege(self):
        for role in ['Buyer','Seller']:
            r=self.client.post('/register/',{'username':role+'new','role':role,'password1':'StrongNewPass!234','password2':'StrongNewPass!234','is_staff':True,'is_superuser':True})
            self.assertEqual(r.status_code,302)
            user=User.objects.get(username=role+'new')
            self.assertTrue(user.groups.filter(name=role).exists())
            self.assertFalse(user.is_staff or user.is_superuser)
            self.client.logout()
    def test_27_html_pages(self):
        for url in ['/','/login/','/register/',f'/listings/{self.listing.pk}/']:
            self.assertEqual(self.client.get(url).status_code,200)
        self.client.force_login(self.seller)
        for url in ['/seller/dashboard/','/seller/listings/create/',f'/seller/listings/{self.listing.pk}/edit/']:
            self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.get('/buyer/dashboard/').status_code,403)
    def test_28_html_end_to_end(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.post(f'/listings/{self.listing.pk}/',{'offered_price':'90','message':'Please build my portfolio.'}).status_code,302)
        offer=Offer.objects.get()
        self.client.force_login(self.seller)
        for action in ['accept','complete']:
            self.assertEqual(self.client.post(f'/offers/{offer.pk}/{action}/').status_code,302)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.post(f'/reviews/{offer.pk}/create/',{'rating':5,'comment':'Wonderful project delivery.'}).status_code,302)
        self.assertContains(self.client.get('/buyer/dashboard/'),'You reviewed')
    def test_29_invalid_content_and_missing(self):
        self.auth(self.buyer)
        self.assertEqual(self.api.get('/api/listings/9999/').status_code,404)
        self.assertEqual(self.api.post('/api/offers/',{'listing':self.listing.pk,'offered_price':'100','message':'   '}).status_code,400)
        offer=self.completed()
        self.assertEqual(self.api.post('/api/reviews/',{'offer':offer.pk,'rating':5,'comment':'short'}).status_code,400)
    def test_30_html_ownership_and_safe_methods(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f'/seller/listings/{self.listing.pk}/delete/').status_code,403)
        self.assertEqual(self.client.get(f'/seller/listings/{self.listing.pk}/edit/').status_code,403)
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(f'/seller/listings/{self.listing.pk}/delete/').status_code,405)
