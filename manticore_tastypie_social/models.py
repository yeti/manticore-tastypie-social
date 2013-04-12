import re
from django.db import models
from manticore_django.manticore_django.models import CoreModel


class Tag(CoreModel):
    name = models.CharField(max_length=75, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


# Expects tags is stored in a field called 'related_tags'
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