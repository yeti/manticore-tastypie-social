

# Registers this library's resources
from manticore_tastypie_social.manticore_tastypie_social.resources import TagResource, FollowResource


def register_api(api):
    api.register(TagResource())
    api.register(FollowResource())
    return api