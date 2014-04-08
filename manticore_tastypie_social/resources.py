from datetime import timedelta
from django.conf import settings
from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from social.apps.django_app.default.models import UserSocialAuth
from tastypie import fields, http
from tastypie.authentication import MultiAuthentication, Authentication
from tastypie.authorization import Authorization, ReadOnlyAuthorization
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.exceptions import BadRequest, Unauthorized
from tastypie.utils import now, dict_strip_unicode_keys
import urbanairship
from manticore_tastypie_core.manticore_tastypie_core.fields import BareGenericForeignKeyField
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from manticore_tastypie_social.manticore_tastypie_social.authorization import SocialAuthorization
from manticore_tastypie_social.manticore_tastypie_social.models import Tag, Comment, Follow, Like, Flag, AirshipToken, NotificationSetting, Notification, create_friend_action, FriendAction, SocialProvider, \
    create_notification
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication
from manticore_tastypie_user.manticore_tastypie_user.authorization import UserObjectsOnlyAuthorization, \
    RelateUserAuthorization
from manticore_tastypie_user.manticore_tastypie_user.resources import UserResource, MinimalUserResource, \
    SearchUserResource

User = get_user_model()


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
    user = fields.ToOneField(MinimalUserResource, 'user', full=True)

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
        create_friend_action(bundle.obj.user, bundle.obj.content_object, FriendAction.TYPES.comment)
        return bundle


class CreateFollowResource(ManticoreModelResource):
    user = fields.ToOneField(UserResource, 'user', blank=True)

    class Meta:
        queryset = Follow.objects.all()
        allowed_methods = ['post', 'delete']
        authorization = RelateUserAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "create_follow"
        always_return_data = True
        object_name = "follow"

    def obj_create(self, bundle, **kwargs):
        bundle = super(CreateFollowResource, self).obj_create(bundle, **kwargs)
        create_friend_action(bundle.obj.user, bundle.obj.content_object, FriendAction.TYPES.follow)
        return bundle


class FollowResource(ManticoreModelResource):
    name = fields.CharField(attribute="name")
    object_type = fields.CharField(attribute="object_type")

    class Meta:
        queryset = Follow.objects.all()
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = MultiAuthentication(ExpireApiKeyAuthentication(), Authentication())
        resource_name = "follow"
        object_name = "follow"
        filtering = {
            'object_id': ['exact'],
        }


# Create or destroy a user follow relationship for an authenticated user
class FollowUserResource(CreateFollowResource):
    user_to_follow = BareGenericForeignKeyField({User: SearchUserResource}, 'content_object')

    class Meta(CreateFollowResource.Meta):
        resource_name = "follow_user"
        object_name = "follow_user"

    def obj_create(self, bundle, **kwargs):
        bundle = super(FollowUserResource, self).obj_create(bundle, **kwargs)
        create_notification(bundle.obj.content_object, bundle.obj.user, bundle.obj.user, Notification.TYPES.follow)
        return bundle

    def obj_delete(self, bundle, **kwargs):
        # Allow client to hit "/api/v1/follow_user/:id/" with DELETE to delete follow relationship on user
        # with :id, rather than delete the Follow object with that id
        bundle.obj = Follow.objects.get(user=bundle.request.user, object_id=kwargs['pk'])
        super(CreateFollowResource, self).obj_delete(bundle, **kwargs)


# List of users a specified user is following
class FollowingUsersResource(FollowResource):
    # There will be a list of user_being_followed objects. user_being_followed is the generic relationship
    # in the Follow model
    user_being_followed = BareGenericForeignKeyField({User: SearchUserResource}, 'content_object', full=True)

    # user is the owner of the Follow object, and is the user whose profile we are viewing
    user = fields.ToOneField(SearchUserResource, 'user', full=False)

    class Meta(FollowResource.Meta):
        queryset = Follow.objects.filter(content_type=ContentType.objects.get_for_model(User))
        allowed_methods = ['get']
        resource_name = "following_users"
        # Since we want a list of objects being followed (user_being_followed), we are filtering on Follow object owner,
        # which is user
        # An example api call to get all the users that user 1 is following would be:
        # /api/v1/following_users/?user=1&format=json
        filtering = {
            'user': ALL_WITH_RELATIONS
        }


# List of users that are following the specified user
class UserFollowersResource(FollowResource):
    # user is the owner of the Follow object
    user = fields.ToOneField(SearchUserResource, 'user', full=True)

    # user_being_followed is the user whose profile we are viewing
    user_being_followed = BareGenericForeignKeyField({User: SearchUserResource}, 'content_object', full=False)

    # filtering attribute is not required because filtering is defined on FollowResource.Meta
    # FollowResource.Meta allows filtering on object_id, which is the id of the object being followed (the
    # generic relationship).
    # In this case, the object being followed is a user, so to get the list of people following user 1,
    # the api call would look like: /api/v1/user_followers/?object_id=1&format=json
    class Meta(FollowResource.Meta):
        queryset = Follow.objects.filter(content_type=ContentType.objects.get_for_model(User))
        allowed_methods = ['get']
        resource_name = "user_followers"


class LikeResource(ManticoreModelResource):
    user = fields.ToOneField(UserResource, 'user')

    class Meta:
        queryset = Like.objects.all()
        allowed_methods = ['post']
        authorization = RelateUserAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "like"
        always_return_data = True
        object_name = "like"

    def obj_create(self, bundle, **kwargs):
        bundle = super(LikeResource, self).obj_create(bundle, **kwargs)
        create_friend_action(bundle.obj.user, bundle.obj.content_object, FriendAction.TYPES.like)
        return bundle


class FlagResource(ManticoreModelResource):
    user = fields.ToOneField(UserResource, 'user')

    class Meta:
        queryset = Flag.objects.all()
        allowed_methods = ['post']
        authorization = RelateUserAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "flag"
        always_return_data = True
        object_name = "flag"


class AirshipTokenResource(ManticoreModelResource):

    class Meta:
        queryset = AirshipToken.objects.all()
        allowed_methods = ['get', 'post']
        authorization = UserObjectsOnlyAuthorization()
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

                bundle.obj = AirshipToken(user=bundle.request.user, token=bundle.data['token'])
                bundle.obj.save()
            except urbanairship.AirshipFailure:
                raise BadRequest("Failed Authentication")

            return bundle
        else:
            raise BadRequest("Missing token")


class NotificationSettingResource(ManticoreModelResource):
    name = fields.CharField(attribute='name', blank=True)
    display_name = fields.CharField(attribute='display_name', blank=True)

    class Meta:
        queryset = NotificationSetting.objects.all()
        allowed_methods = ['get', 'patch']
        authorization = UserObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "notification_setting"
        always_return_data = True
        object_name = "notification_setting"
        fields = ['id', 'allow', 'name', 'display_name']


class NotificationResource(ManticoreModelResource):
    name = fields.CharField(attribute='name')
    display_name = fields.CharField(attribute='display_name')
    reporter = fields.ToOneField(UserResource, 'reporter', null=True, full=True)

    class Meta:
        queryset = Notification.objects.all()
        allowed_methods = ['get']
        authorization = UserObjectsOnlyAuthorization()
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
    user = fields.ToOneField(UserResource, 'user', full=True)

    class Meta:
        queryset = FriendAction.objects.all()
        allowed_methods = ['get']
        authorization = UserObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "friend_action"
        object_name = "friend_action"
        fields = ['id', 'created', 'name', 'display_name', 'user']

    def get_object_list(self, request=None, **kwargs):
        date = now() - timedelta(days=settings.NOTIFICATION_WINDOW_HOURS)
        return super(FriendActionResource, self).get_object_list(request).filter(created__gte=date)


class SocialProviderResource(ManticoreModelResource):

    class Meta:
        queryset = SocialProvider.objects.all()
        allowed_methods = ['get']
        authorization = SocialAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "social_provider"
        object_name = "social_provider"
        detail_uri_name = 'name'
        fields = ['name']


class SocialShareResource(ManticoreModelResource):
    providers = fields.ListField(null=True)

    def obj_create(self, bundle, **kwargs):
        bundle = super(SocialShareResource, self).obj_create(bundle, **kwargs)

        if 'providers' in bundle.data:
            for provider in bundle.data['providers']:
                try:
                    user_social_auth = UserSocialAuth.objects.get(user=bundle.request.user, provider=provider)

                    # Inline import to remove recursive importing
                    from manticore_tastypie_social.manticore_tastypie_social.utils import post_social_media
                    post_social_media.apply_async((user_social_auth, bundle.obj), countdown=settings.SOCIAL_SHARE_DELAY)
                except UserSocialAuth.DoesNotExist:
                    pass
        return bundle

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/social_share/(?P<pk>\w[\w/-]*)/$" % self._meta.resource_name, self.wrap_view('social_share'), name="api_social_share"),
        ]

    def social_share(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        try:
            social_obj = self._meta.queryset._clone().get(pk=kwargs['pk'])
        except self._meta.object_class.DoesNotExist:
            return http.HttpNotFound()

        deserialized = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        bundle = self.build_bundle(obj=social_obj, request=request, data=dict_strip_unicode_keys(deserialized))

        try:
            auth_result = self._meta.authorization.share_detail(None, bundle)
            if not auth_result is True:
                raise Unauthorized()
        except Unauthorized as e:
            self.unauthorized_result(e)
        except AttributeError as e:
            raise NotImplementedError("You must create a share_detail authorization method")

        if 'provider' not in bundle.data:
            return self.error_response(request, {"error": "No provider parameter given"}, response_class=http.HttpBadRequest)

        try:
            user_social_auth = UserSocialAuth.objects.get(user=bundle.request.user, provider=bundle.data['provider'])

            # Inline import to remove recursive importing
            from manticore_tastypie_social.manticore_tastypie_social.utils import post_social_media
            post_social_media.delay(user_social_auth, bundle.obj)
        except UserSocialAuth.DoesNotExist:
            return self.error_response(request, {"error": "User is not authenticated with %s" % bundle.data['provider']}, response_class=http.HttpBadRequest)
        except BadRequest, e:
            return self.error_response(request, {"error": e}, response_class=http.HttpBadRequest)

        bundle = self.full_dehydrate(bundle)

        # create_notification(bundle.obj.user, bundle.request.user, bundle.obj, Notification.TYPES.shared)

        return self.create_response(request, bundle, response_class=http.HttpAccepted)