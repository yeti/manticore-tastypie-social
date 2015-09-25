from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from tastypie import fields
from tastypie.authentication import MultiAuthentication, Authentication
from tastypie.authorization import Authorization
from tastypie.exceptions import BadRequest
from tastypie.utils import now
import urbanairship
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from manticore_tastypie_social.manticore_tastypie_social.models import Tag, Comment, Follow, Like, Flag, AirshipToken, NotificationSetting, Notification, create_friend_action, FriendAction, SocialProvider
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication
from manticore_tastypie_user.manticore_tastypie_user.authorization import UserProfileObjectsOnlyAuthorization
from manticore_tastypie_user.manticore_tastypie_user.resources import UserProfileResource, MinimalUserProfileResource

UserProfile = get_user_model()


class TagResource(ManticoreModelResource):

    class Meta:
        allowed_methods = ['get']
        queryset = Tag.objects.all()
        authorization = Authorization()
        authentication = MultiAuthentication(ExpireApiKeyAuthentication(), Authentication())
        fields = ['id', 'name']
        resource_name = "tag"
        object_name = "tag"
        include_resource_uri = False
        filtering = {'name': ['exact'],}


class CommentResource(ManticoreModelResource):
    user_profile = fields.ToOneField(MinimalUserProfileResource, 'user_profile', full=True, readonly=True)

    class Meta:
        queryset = Comment.objects.all()
        allowed_methods = ['post']
        authorization = Authorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "comment"
        always_return_data = True
        object_name = "comment"

    def obj_create(self, bundle, **kwargs):
        bundle = super(CommentResource, self).obj_create(bundle, **kwargs)
        create_friend_action(bundle.obj.user_profile, bundle.obj.content_object, FriendAction.TYPES.comment)
        return bundle


class CreateFollowResource(ManticoreModelResource):
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile', readonly=True)

    class Meta:
        queryset = Follow.objects.all()
        allowed_methods = ['post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "create_follow"
        always_return_data = True
        object_name = "follow"

    def obj_create(self, bundle, **kwargs):
        bundle = super(CreateFollowResource, self).obj_create(bundle, **kwargs)
        create_friend_action(bundle.obj.user_profile, bundle.obj.content_object, FriendAction.TYPES.follow)
        return bundle


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
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile', readonly=True)

    class Meta:
        queryset = Like.objects.all()
        allowed_methods = ['post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "like"
        always_return_data = True
        object_name = "like"

    def obj_create(self, bundle, **kwargs):
        bundle = super(LikeResource, self).obj_create(bundle, **kwargs)
        create_friend_action(bundle.obj.user_profile, bundle.obj.content_object, FriendAction.TYPES.like)
        return bundle


class FlagResource(ManticoreModelResource):
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile', readonly=True)

    class Meta:
        queryset = Flag.objects.all()
        allowed_methods = ['post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "flag"
        always_return_data = True
        object_name = "flag"


class AirshipTokenResource(ManticoreModelResource):

    class Meta:
        queryset = AirshipToken.objects.all()
        allowed_methods = ['get', 'post']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "airship_token"
        always_return_data = True
        object_name = "airship_token"

    def obj_create(self, bundle, **kwargs):
        if 'token' in bundle.data:
            airship = urbanairship.Airship(settings.AIRSHIP_APP_KEY, settings.AIRSHIP_APP_MASTER_SECRET)
            try:
                airship.register(bundle.data['token'], alias="%s:%s" % (bundle.request.user.pk, bundle.request.user.username))

                # Delete other usages of this token (i.e. multiple accounts on one device)
                AirshipToken.objects.filter(token=bundle.data['token']).delete()

                bundle.obj = AirshipToken(user_profile=bundle.request.user.userprofile, token=bundle.data['token'])
                bundle.obj.save()
            except urbanairship.AirshipFailure:
                raise BadRequest("Failed Authentication")

            return bundle
        else:
            raise BadRequest("Missing token")


class NotificationSettingResource(ManticoreModelResource):
    name = fields.CharField(attribute='name')
    display_name = fields.CharField(attribute='display_name')

    class Meta:
        queryset = NotificationSetting.objects.all()
        allowed_methods = ['get', 'patch']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "notification_setting"
        always_return_data = True
        object_name = "notification_setting"
        fields = ['id', 'allow', 'name', 'display_name']


class NotificationResource(ManticoreModelResource):
    name = fields.CharField(attribute='name')
    display_name = fields.CharField(attribute='display_name')
    reporter = fields.ToOneField(UserProfileResource, 'reporter', null=True, full=True)

    class Meta:
        queryset = Notification.objects.all()
        allowed_methods = ['get']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "notification"
        object_name = "notification"
        fields = ['id', 'created', 'name', 'display_name', 'reporter']

    def get_object_list(self, request=None, **kwargs):
        date = now() - timedelta(days=settings.NOTIFICATION_WINDOW_HOURS)
        return super(NotificationResource, self).get_object_list(request).filter(created__gte=date)


class FriendActionResource(ManticoreModelResource):
    name = fields.CharField(attribute='name')
    display_name = fields.CharField(attribute='display_name')
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile', full=True)

    class Meta:
        queryset = FriendAction.objects.all()
        allowed_methods = ['get']
        authorization = UserProfileObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "friend_action"
        object_name = "friend_action"
        fields = ['id', 'created', 'name', 'display_name', 'user_profile']

    def get_object_list(self, request=None, **kwargs):
        date = now() - timedelta(days=settings.NOTIFICATION_WINDOW_HOURS)
        return super(FriendActionResource, self).get_object_list(request).filter(created__gte=date)


class SocialProviderResource(ManticoreModelResource):

    class Meta:
        queryset = SocialProvider.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "social_provider"
        object_name = "social_provider"
        detail_uri_name = 'name'
        fields = ['name']