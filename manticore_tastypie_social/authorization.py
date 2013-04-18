from tastypie.authorization import ReadOnlyAuthorization


class FollowerAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        return object_list.filter(object_id=bundle.request.user.get_profile().pk)

    def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        return bundle.obj.content_object == bundle.request.user.get_profile()