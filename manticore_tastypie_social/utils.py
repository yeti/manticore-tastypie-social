from manticore_tastypie_social.manticore_tastypie_social.resources import TagResource, FollowResource


# Registers this library's resources
def register_api(api):
    api.register(TagResource())
    api.register(FollowResource())
    return api