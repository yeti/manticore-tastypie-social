from StringIO import StringIO
import urllib
import urllib2
from celery.task import task
from django.conf import settings
import foursquare
from social_auth.db.django_models import UserSocialAuth
from tastypie.exceptions import BadRequest
from twython import Twython
from manticore_tastypie_social.manticore_tastypie_social.resources import TagResource, FollowResource, AirshipTokenResource, NotificationSettingResource, SocialProviderResource


# Registers this library's resources
def register_api(api):
    api.register(TagResource())
    api.register(FollowResource())
    api.register(AirshipTokenResource())
    api.register(NotificationSettingResource())
    api.register(SocialProviderResource())
    return api


def post_to_facebook(app_access_token, user_social_auth, message, link):
    url = "https://graph.facebook.com/%s/feed" % user_social_auth.uid

    params = {
        'access_token': app_access_token,
        'message': message,
        'link': link
    }

    req = urllib2.Request(url, urllib.urlencode(params))
    urllib2.urlopen(req)

@task
def post_social_media(user, message, provider, link, location, object_class, pk, raise_error=True):
    try:
        user_social_auth = UserSocialAuth.objects.get(user=user, provider=provider)

        if user_social_auth.provider == 'facebook':
            try:
                post_to_facebook(settings.FACEBOOK_APP_ACCESS_TOKEN, user_social_auth, message, link)
            except urllib2.HTTPError:
                # Error in launching app with dev facebook credentials, if we get a HTTPError retry with dev credentials
                post_to_facebook(settings.FACEBOOK_APP_ACCESS_TOKEN_DEV, user_social_auth, message, link)
        elif user_social_auth.provider == 'twitter':
            twitter = Twython(
                app_key=settings.TWITTER_CONSUMER_KEY,
                app_secret=settings.TWITTER_CONSUMER_SECRET,
                oauth_token=user_social_auth.tokens['oauth_token'],
                oauth_token_secret=user_social_auth.tokens['oauth_token_secret']
            )

            social_object = object_class.objects.get(pk=pk)

            if social_object.small_photo:
                photo = StringIO(urllib.urlopen(social_object.small_photo.url).read())
                twitter.update_status_with_media(media=photo, status=message, wrap_links=True)
            else:
                twitter.update_status(status=message, wrap_links=True)
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