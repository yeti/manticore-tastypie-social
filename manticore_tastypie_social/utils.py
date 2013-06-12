import urllib
import urllib2
from celery.task import task
from django.conf import settings
import foursquare
import oauth2
from social_auth.db.django_models import UserSocialAuth
from tastypie.exceptions import BadRequest
from manticore_tastypie_social.manticore_tastypie_social.resources import TagResource, FollowResource, AirshipTokenResource, NotificationSettingResource, SocialProviderResource


# Registers this library's resources
def register_api(api):
    api.register(TagResource())
    api.register(FollowResource())
    api.register(AirshipTokenResource())
    api.register(NotificationSettingResource())
    api.register(SocialProviderResource())
    return api


@task
def post_social_media(user, message, provider, link, location, raise_error=True):
    try:
        user_social_auth = UserSocialAuth.objects.get(user=user, provider=provider)

        if user_social_auth.provider == 'facebook':
            url = "https://graph.facebook.com/%s/feed" % user_social_auth.uid

            params = {
                'access_token': settings.FACEBOOK_APP_ACCESS_TOKEN,
                'message': message,
                'link': link
            }

            req = urllib2.Request(url, urllib.urlencode(params))
            urllib2.urlopen(req)
        elif user_social_auth.provider == 'twitter':
            data = {
                'status': message,
                'wrap_links': True,
            }

            url = "https://api.twitter.com/1.1/statuses/update.json"
            consumer = oauth2.Consumer(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
            token = oauth2.Token(user_social_auth.tokens['oauth_token'], user_social_auth.tokens['oauth_token_secret'])
            client = oauth2.Client(consumer, token)
            client.request(url, 'POST', urllib.urlencode(data))
        elif user_social_auth.provider == 'foursquare':
            if location:
                client = foursquare.Foursquare(client_id=settings.FOURSQUARE_CONSUMER_KEY, client_secret=settings.FOURSQUARE_CONSUMER_SECRET, access_token=user_social_auth.extra_data['access_token'])
                coords = "%s,%s" % (location.latitude, location.longitude)
                query = client.venues.search(params={"intent": "match", "ll": coords, "query": location.name, "limit": 1})
                if len(query['venues']) > 0:
                    venue = query['venues'][0]
                    client.checkins.add(params={"venueId": venue['id'], "ll": coords, "shout": message})
                else:
                    raise BadRequest("Matching foursquare location not found")
            else:
                raise BadRequest("No location provided for foursquare")
        elif raise_error:
            raise BadRequest("Does not support this provider: %s" % provider)
    except (UserSocialAuth.DoesNotExist, urllib2.HTTPError, ValueError, IOError), e:
        if raise_error:
            raise e