from tastypie import fields
from tastypie.authorization import Authorization
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from manticore_tastypie_social.manticore_tastypie_social.models import Tag, Comment, Follow, Like, Flag
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication
from manticore_tastypie_user.manticore_tastypie_user.authorization import UserProfileObjectsOnlyAuthorization
from manticore_tastypie_user.manticore_tastypie_user.resources import UserProfileResource, MinimalUserProfileResource


class TagResource(ManticoreModelResource):

    class Meta:
        allowed_methods = ['get']
        queryset = Tag.objects.all()
        authorization = Authorization()
        authentication = ExpireApiKeyAuthentication()
        fields = ['id', 'name']
        resource_name = "tag"
        object_name = "tag"
        include_resource_uri = False
        filtering = {'name': ['exact'],}


class CommentResource(ManticoreModelResource):
    user_profile = fields.ToOneField(MinimalUserProfileResource, 'user_profile', full=True)

    class Meta:
        queryset = Comment.objects.all()
        allowed_methods = ['post']
        authorization = Authorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "comment"
        always_return_data = True
        object_name = "comment"

    #TODO: notify user who owns the object being commented on and other commenters
    # def obj_create(self, bundle, request=None, **kwargs):
    #     bundle = super(CommentResource, self).obj_create(bundle, request, user=request.user.get_profile())
    #
    #     users = [bundle.obj.blurt.user]
    #     for comment in bundle.obj.blurt.comment_set.all():
    #         if comment.user not in users:
    #             users.append(comment.user)
    #
    #     for user in users:
    #         create_notification(user, bundle.obj.user, bundle.obj.blurt.pk, Notification.TYPE_COMMENT)
    #
    #     return bundle


class CreateFollowResource(ManticoreModelResource):
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile')

    class Meta:
        queryset = Follow.objects.all()
        allowed_methods = ['post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "create_follow"
        always_return_data = True
        object_name = "follow"


class FollowResource(ManticoreModelResource):
    name = fields.CharField(attribute="name")
    object_type = fields.CharField(attribute="object_type")

    class Meta:
        queryset = Follow.objects.all()
        allowed_methods = ['get', 'delete']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "follow"
        object_name = "follow"
        filtering = {
            'object_id': ['exact'],
        }


class LikeResource(ManticoreModelResource):
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile')

    class Meta:
        queryset = Like.objects.all()
        allowed_methods = ['post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "like"
        always_return_data = True
        object_name = "like"


class FlagResource(ManticoreModelResource):
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile')

    class Meta:
        queryset = Flag.objects.all()
        allowed_methods = ['post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "flag"
        always_return_data = True
        object_name = "flag"