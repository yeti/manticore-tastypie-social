from django.core.management import BaseCommand
from forecast.models import UserProfile
from manticore_tastypie_social.manticore_tastypie_social.models import Notification, NotificationSetting

__author__ = 'rudolphmutter'


class Command(BaseCommand):
    args = ''
    help = 'Creates missing notification settings for existing users'

    def handle(self, *args, **options):
        for user_profile in UserProfile.objects.all():
            for pk, name in Notification.TYPES:
                try:
                    NotificationSetting.objects.get_or_create(notification_type=pk, user_profile=user_profile)
                except:
                    pass