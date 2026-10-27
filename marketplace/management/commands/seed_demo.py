import os
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from marketplace.models import Listing

class Command(BaseCommand):
    help = 'Create repeatable fictional demo listings. Requires DEBUG and DEMO_PASSWORD.'
    def handle(self, *args, **options):
        password = os.getenv('DEMO_PASSWORD')
        if not settings.DEBUG or not password or len(password) < 12:
            raise CommandError('Use local DEBUG and set DEMO_PASSWORD to at least 12 characters.')
        services = [
            ('maya.studio','Graphic Design','A thoughtful visual identity for your brand','240.00'),
            ('alex.builds','Web Development','A beautiful, fast website for your business','350.00'),
            ('sarah.writes','Content Writing','Website copy that sounds like you','120.00'),
            ('omar.motion','Video Editing','Turn your footage into a story worth watching','180.00'),
            ('nina.search','SEO','An actionable SEO audit for your next chapter','95.00'),
            ('leo.digital','Digital Marketing','A social strategy with a clear sense of direction','160.00')]
        for username, category, title, price in services:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password); user.save()
                user.groups.add(Group.objects.get(name='Seller'))
            Listing.objects.get_or_create(seller=user,title=title,defaults={'category':category,'starting_price':price,'description':f"Let's make your next project something special. I offer focused {category.lower()} services for independent businesses and small teams.\n\nWe will start with your goals, agree on a clear scope, and work towards a thoughtful result. Send an offer with your brief, timeline, and budget to get started.\n\nThis is a fictional demonstration listing."})
        buyer, created = User.objects.get_or_create(username='demo.buyer')
        if created:
            buyer.set_password(password); buyer.save(); buyer.groups.add(Group.objects.get(name='Buyer'))
        self.stdout.write(self.style.SUCCESS('Six fictional services and demo.buyer are ready. Existing passwords were not changed.'))
