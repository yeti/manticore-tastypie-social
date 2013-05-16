import abc
import re
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from mezzanine.accounts import get_profile_model
from model_utils import Choices
import urbanairship
from manticore_django.manticore_django.models import CoreModel
from django.utils.translation import ugettext_lazy as _

class FollowableModel():
    """
    Abstract class that used as interface
    This class makes sure that child classes have
    my_method implemented
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def identifier(self):
        return

    @abc.abstractmethod
    def type(self):
        return


class Tag(CoreModel):
    name = models.CharField(max_length=75, unique=True)

    def identifier(self):
        return u"#%s" % self.name

    def type(self):
        return u"tag"

    def __unicode__(self):
        return u"%s" % self.name

FollowableModel.register(Tag)


# Expects tags is stored in a field called 'related_tags' on implementing model and it has a parameter called TAG_FIELD to be parsed
def relate_tags(sender, **kwargs):
    # If we're saving related_tags, don't save again so we avoid duplicating notifications
    if kwargs['update_fields'] and 'related_tags' not in kwargs['update_fields']:
        return

    changed = False
    message = getattr(kwargs['instance'], sender.TAG_FIELD, '')
    for tag in re.findall(ur"#[a-zA-Z0-9_-]+", message):
        tag_obj, created = Tag.objects.get_or_create(name=tag[1:])
        if tag_obj not in kwargs['instance'].related_tags.all():
            kwargs['instance'].related_tags.add(tag_obj)
            changed = True

    if changed:
        kwargs['instance'].save()


def mentions(sender, **kwargs):
    if kwargs['created']:
        message = getattr(kwargs['instance'], sender.TAG_FIELD, '')

        UserProfile = get_profile_model()
        for user_profile in re.findall(ur"@[a-zA-Z0-9_]+", message):
            try:
                receiver = UserProfile.objects.get(user__username=user_profile[1:])
                create_notification(receiver, kwargs['instance'].user_profile, kwargs['instance'], Notification.TYPES.mention)
            except UserProfile.DoesNotExist:
                pass


class Comment(CoreModel):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    description = models.CharField(max_length=120)
    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)

    class Meta:
        ordering = ['created']


def comment_post_save(sender, **kwargs):
    if kwargs['created']:
        comment = kwargs['instance']
        UserProfile = get_profile_model()
        for user_profile in re.findall(ur"@[a-zA-Z0-9_]+", comment.description):
            try:
                receiver = UserProfile.objects.get(user__username=user_profile[1:])
                create_notification(receiver, comment.user_profile, comment.content_object, Notification.TYPES.mention)
            except UserProfile.DoesNotExist:
                pass

post_save.connect(comment_post_save, sender=Comment)


# Allows a user to 'follow' objects
class Follow(CoreModel):
    content_type = models.ForeignKey(ContentType)
    object_id = models.CharField(max_length=250)
    content_object = generic.GenericForeignKey()

    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)

    @property
    def object_type(self):
        return self.content_type.name

    @property
    def name(self):
        #object must be registered with FollowableModel
        return self.content_object.identifier()

    class Meta:
        unique_together = (("user_profile", "content_type", "object_id"),)
        ordering = ['created']


class Like(CoreModel):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)

    class Meta:
        unique_together = (("user_profile", "content_type", "object_id"),)


# Flag an object for review
class Flag(CoreModel):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)

    class Meta:
        unique_together = (("user_profile", "content_type", "object_id"),)


# Stores user tokens from Urban Airship
class AirshipToken(CoreModel):
    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE, unique=True)
    token = models.CharField(max_length=100)
    expired = models.BooleanField(default=False)


#TODO: Need to abstract 'report' out
class Notification(CoreModel):
    TYPES = Choices(
        (0, 'follow', _('started following you')),
        (1, 'like', _('liked your report')),
        (2, 'comment', _('commented on your report')),
        (3, 'shared', _('shared your report')),
        (4, 'mention', _('mentioned you')),
        (5, 'trending', _('your report is trending')),
        (6, 'friend', _('your friend just signed up')),
    )
    notification_type = models.PositiveSmallIntegerField(choices=TYPES)
    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE, related_name="receiver")
    reporter = models.ForeignKey(settings.AUTH_PROFILE_MODULE, related_name="reporter", null=True, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    def message(self):
        return unicode(Notification.TYPES[self.notification_type][1])

    def push_message(self):
        # If this is a comment on an object the receiving user doesn't own, change the default message
        if self.notification_type == self.TYPES.comment and self.content_object.user_profile != self.user_profile:
            message = "@%s commented on @%s's report" % (self.reporter.user.username, self.content_object.user_profile.user.username)
        elif self.notification_type == self.TYPES.trending:
            message = "Your report is trending!"
        elif self.notification_type == self.TYPES.friend:
            message = "Your friend just signed up as @%s" % self.reporter.user.username
        else:
            message = "@%s %s" % (self.reporter.user.username, self.message())

        return message

    def name(self):
        return u"%s" % Notification.TYPES._full[self.notification_type][1]

    def display_name(self):
        return u"%s" % self.get_notification_type_display()

    class Meta:
        ordering = ['-created']

def create_notification(receiver, reporter, content_object, notification_type):
    # If the receiver of this notification is the same as the reporter or if the user has blocked this type, then don't create
    if receiver == reporter or not NotificationSetting.objects.get(notification_type=notification_type, user_profile=receiver).allow:
        return

    notification = Notification.objects.create(user_profile=receiver,
                                               reporter=reporter,
                                               content_object=content_object,
                                               notification_type=notification_type)
    notification.save()

    if AirshipToken.objects.filter(user_profile=receiver, expired=False).exists():
        try:
            device_tokens = list(AirshipToken.objects.filter(user_profile=receiver, expired=False).values_list('token', flat=True))
            airship = urbanairship.Airship(settings.AIRSHIP_APP_KEY, settings.AIRSHIP_APP_MASTER_SECRET)
            airship.push({'aps': {'alert': notification.push_message(), 'badge': '+1'}}, device_tokens=device_tokens)
        except urbanairship.AirshipFailure:
            pass


class NotificationSetting(CoreModel):
    notification_type = models.PositiveSmallIntegerField(choices=Notification.TYPES)
    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)
    allow = models.BooleanField(default=True)

    class Meta:
        unique_together = ('notification_type', 'user_profile')

    def name(self):
        return u"%s" % Notification.TYPES._full[self.notification_type][1]

    def display_name(self):
        return u"%s" % self.get_notification_type_display()


def create_notifications(sender, **kwargs):
    sender_name = "%s.%s" % (sender._meta.app_label, sender._meta.object_name)
    if sender_name.lower() != settings.AUTH_PROFILE_MODULE.lower():
        return

    if kwargs['created']:
        user_profile = kwargs['instance']
        NotificationSetting.objects.bulk_create([NotificationSetting(user_profile=user_profile, notification_type=pk) for pk, name in Notification.TYPES])

post_save.connect(create_notifications)


#TODO: Need to abstract out 'report'
class FriendAction(CoreModel):
    TYPES = Choices(
        (0, 'follow', _('is following')),
        (1, 'like', _('liked a report')),
        (2, 'comment', _('commented on a report')),
    )
    action_type = models.PositiveSmallIntegerField(choices=TYPES)
    user_profile = models.ForeignKey(settings.AUTH_PROFILE_MODULE)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    def message(self):
        return unicode(Notification.TYPES[self.action_type][1])

    def name(self):
        return u"%s" % Notification.TYPES._full[self.action_type][1]

    def display_name(self):
        return u"%s" % self.get_action_type_display()

    class Meta:
        ordering = ['-created']


def create_friend_action(user_profile, content_object, action_type):
    friend_action = FriendAction.objects.create(user_profile=user_profile,
                                                content_object=content_object,
                                                action_type=action_type)
    friend_action.save()


# Currently available social providers
class SocialProvider(CoreModel):
    name = models.CharField(max_length=20)