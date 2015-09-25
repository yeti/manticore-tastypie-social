# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AirshipToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('token', models.CharField(max_length=100)),
                ('expired', models.BooleanField(default=False)),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('description', models.CharField(max_length=140)),
                ('legacy_comment_id', models.CharField(db_index=True, max_length=50, unique=True, null=True, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('object_id', models.CharField(max_length=250, db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FriendAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('action_type', models.PositiveSmallIntegerField(choices=[(0, 'is following'), (1, 'liked a report'), (2, 'commented on a report')])),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('notification_type', models.PositiveSmallIntegerField(choices=[(0, 'started following you'), (1, 'liked your report'), (2, 'commented on your report'), (3, 'shared your report'), (4, 'mentioned you'), (5, 'your report is trending'), (6, 'your friend just signed up')])),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('reporter', models.ForeignKey(related_name='reporter', blank=True, to='forecast.UserProfile', null=True)),
                ('user_profile', models.ForeignKey(related_name='receiver', to='forecast.UserProfile')),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NotificationSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('notification_type', models.PositiveSmallIntegerField(choices=[(0, 'started following you'), (1, 'liked your report'), (2, 'commented on your report'), (3, 'shared your report'), (4, 'mentioned you'), (5, 'your report is trending'), (6, 'your friend just signed up')])),
                ('allow', models.BooleanField(default=True)),
                ('user_profile', models.ForeignKey(to='forecast.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SocialProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('name', models.CharField(unique=True, max_length=75)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='notificationsetting',
            unique_together=set([('notification_type', 'user_profile')]),
        ),
        migrations.AlterUniqueTogether(
            name='like',
            unique_together=set([('user_profile', 'content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together=set([('user_profile', 'content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='flag',
            unique_together=set([('user_profile', 'content_type', 'object_id')]),
        ),
    ]
