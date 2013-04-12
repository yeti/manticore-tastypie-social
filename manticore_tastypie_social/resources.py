from tastypie.authorization import Authorization
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from manticore_tastypie_social.manticore_tastypie_social.models import Tag, Comment
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication


class TagResource(ManticoreModelResource):

    class Meta:
        queryset = Tag.objects.all()
        fields = ['id','name',]
        resource_name = "tag"
        object_name = "tag"
        include_resource_uri = False


class CommentResource(ManticoreModelResource):

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