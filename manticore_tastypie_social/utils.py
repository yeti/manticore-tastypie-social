import urllib
import urllib2
from celery.task import task
from django.conf import settings
# import foursquare
from social.apps.django_app.default.models import UserSocialAuth
from tastypie.exceptions import BadRequest
from twython import Twython
from manticore_tastypie_social.manticore_tastypie_social.resources import TagResource, FollowResource, AirshipTokenResource, NotificationSettingResource, SocialProviderResource, \
    FollowUserResource, FollowingUsersResource, UserFollowersResource


# Registers this library's resources
def register_api(api):
    api.register(TagResource())
    api.register(FollowResource())
    api.register(FollowUserResource())
    api.register(FollowingUsersResource())
    api.register(UserFollowersResource())
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


def post_to_facebook_og(app_access_token, user_social_auth, obj):
    og_info = obj.facebook_og_info()

    url = "https://graph.facebook.com/{0}/{1}:{2}".format(
        user_social_auth.uid,
        settings.FACEBOOK_OG_NAMESPACE,
        og_info['action'],
    )

    params = {
        '{0}'.format(og_info['object']): '{0}'.format(og_info['url']),
        'access_token': app_access_token,
    }

    req = urllib2.Request(url, urllib.urlencode(params))
    urllib2.urlopen(req)


@task
def post_social_media(user, message, provider, link, location, object_class, pk, raise_error=True):
    try:
        user_social_auth = UserSocialAuth.objects.get(user=user, provider=provider)

        if user_social_auth.provider == 'facebook':
            if settings.USE_FACEBOOK_OG:
                social_object = object_class.objects.get(pk=pk)

                try:
                    post_to_facebook_og(settings.FACEBOOK_APP_ACCESS_TOKEN, user_social_auth, social_object)
                except urllib2.HTTPError:
                    # Error in launching app with dev facebook credentials, if we get a HTTPError retry with dev credentials
                    post_to_facebook_og(settings.FACEBOOK_APP_ACCESS_TOKEN_DEV, user_social_auth, social_object)
            else:
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

            full_message_url = "{0} {1}".format(message, link)

            # 140 characters minus the length of the link minus the space minus 3 characters for the ellipsis
            message_trunc = 140 - len(link) - 1 - 3

            # Truncate the message if the message + url is over 140
            safe_message = ("{0}... {1}".format(message[:message_trunc], link)) if len(full_message_url) > 140 else full_message_url
            twitter.update_status(status=safe_message, wrap_links=True)
        # elif user_social_auth.provider == 'foursquare':
        #     if location:
        #         client = foursquare.Foursquare(client_id=settings.FOURSQUARE_CONSUMER_KEY, client_secret=settings.FOURSQUARE_CONSUMER_SECRET, access_token=user_social_auth.extra_data['access_token'])
        #         coords = "%s,%s" % (location.latitude, location.longitude)
        #         query = client.venues.search(params={"intent": "match", "ll": coords, "query": location.name, "limit": 1})
        #         if len(query['venues']) > 0:
        #             venue = query['venues'][0]
        #             client.checkins.add(params={"venueId": venue['id'], "ll": coords, "shout": message})
        #         else:
        #             raise BadRequest("Matching foursquare location not found")
        #     else:
        #         raise BadRequest("No location provided for foursquare")
        elif raise_error:
            raise BadRequest("Does not support this provider: %s" % provider)
    except (UserSocialAuth.DoesNotExist, urllib2.HTTPError, ValueError, IOError), e:
        if raise_error:
            raise e