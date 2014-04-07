from tastypie.authorization import ReadOnlyAuthorization, Authorization


class FollowerAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        return object_list.filter(object_id=bundle.request.user.pk)

    def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        return bundle.obj.content_object == bundle.request.user


class SocialAuthorization(Authorization):
    def share_detail(self, object_list, bundle):
        raise NotImplementedError("Social sharing authorization has not been specified")