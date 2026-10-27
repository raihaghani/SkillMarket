from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.db import transaction
from .models import Listing, Offer, Review

class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=[('Buyer', 'I want to hire'), ('Seller', 'I want to offer services')])
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=True)
        user.groups.add(Group.objects.get(name=self.cleaned_data['role']))
        return user

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'starting_price', 'status']

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['offered_price', 'message']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
