import re
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from mezzanine.accounts import get_profile_model
from manticore_django.manticore_django.models import CoreModel

# UserProfile = get_profile_model()


class Tag(CoreModel):
    name = models.CharField(max_length=75, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


# Expects tags is stored in a field called 'related_tags' on implementing model and it has a parameter called TAG_FIELD to be parsed
def relate_tags(sender, **kwargs):
    if kwargs['update_fields'] and 'related_tags' not in kwargs['update_fields']:
        return

    changed = False
    message = getattr(kwargs['instance'], sender.TAG_FIELD, '')
    for word in message.split():
        if word.startswith("#"):
            tag, created = Tag.objects.get_or_create(name=word[1:])
            if tag not in kwargs['instance'].related_tags.all():
                kwargs['instance'].related_tags.add(tag)
                changed = True
        elif word.startswith("@"):
            #TODO: notifications
            pass
            # try:
            #     user_profile = UserProfile.objects.get(user__username=word.replace("@", ""))
            #     create_notification(user_profile, self.user, self.pk, Notification.TYPE_MENTION)
            # except UserProfile.DoesNotExist:
            #     pass

    if changed:
        kwargs['instance'].save()


class Comment(CoreModel):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    description = models.CharField(max_length=120)
    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)

    class Meta:
        ordering = ['-created']

#TODO: Add @ mention notifications
# def comment_post_save(sender, **kwargs):
#     if kwargs['created']:
#         comment = kwargs['instance']
#         for word in comment.description.split():
#             if word.startswith("@"):
#                 try:
#                     user_profile = UserProfile.objects.get(user__username=word.replace("@", ""))
#                     create_notification(user_profile, comment.user, comment.blurt.pk, Notification.TYPE_MENTION)
#                 except UserProfile.DoesNotExist:
#                     pass
#
# post_save.connect(comment_post_save, sender=Comment)