from datetime import timedelta
from django.conf import settings
from mezzanine.accounts import get_profile_model
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.exceptions import BadRequest
from tastypie.utils import now
import urbanairship
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from manticore_tastypie_social.manticore_tastypie_social.models import Tag, Comment, Follow, Like, Flag, AirshipToken, NotificationSetting, Notification
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication
from manticore_tastypie_user.manticore_tastypie_user.authorization import UserProfileObjectsOnlyAuthorization
from manticore_tastypie_user.manticore_tastypie_user.resources import UserProfileResource, MinimalUserProfileResource

UserProfile = get_profile_model()


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
                airship.register(bundle.data['token'], alias=bundle.request.user.email)

                # Delete other usages of this token (i.e. multiple accounts on one device)
                AirshipToken.objects.filter(token=bundle.data['token']).delete()

                bundle.obj = AirshipToken(user=bundle.request.user.get_profile(), token=bundle.data['token'])
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

    # Rename our target_object to either report or user_profile appropriately depending on its type
    def alter_list_data_to_serialize(self, request, data):
        for bundle in data['objects']:
            if isinstance(bundle.obj.content_object, UserProfile):
                bundle.data['user_profile'] = bundle.data['target_object']
                del bundle.data['target_object']
            else:
                bundle.data['report'] = bundle.data['target_object']
                del bundle.data['target_object']
        return super(NotificationResource, self).alter_list_data_to_serialize(request, data)