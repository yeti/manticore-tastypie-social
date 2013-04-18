import urllib
import urllib2
from django.conf import settings
import oauth2
from social_auth.db.django_models import UserSocialAuth
from tastypie.exceptions import BadRequest
from manticore_tastypie_social.manticore_tastypie_social.resources import TagResource, FollowResource


# Registers this library's resources
def register_api(api):
    api.register(TagResource())
    api.register(FollowResource())
    return api


def post_social_media(user, message, provider, raise_error=False):
    try:
        user_social_auth = UserSocialAuth.objects.get(user=user, provider=provider)

        if user_social_auth.provider == 'facebook':
            url = "https://graph.facebook.com/%s/feed" % user_social_auth.uid

            params = {
                'access_token': settings.FACEBOOK_APP_ACCESS_TOKEN,
                'message': message
                # 'link': bundle.obj.url
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
        elif raise_error:
            raise BadRequest("Does not support this provider: %s" % provider)
    except (UserSocialAuth.DoesNotExist, urllib2.HTTPError, ValueError, IOError), e:
        if raise_error:
            raise e