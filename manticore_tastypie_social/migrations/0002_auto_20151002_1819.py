# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manticore_tastypie_social', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='legacy_comment_id',
        ),
        migrations.AlterField(
            model_name='comment',
            name='content_type',
            field=models.ForeignKey(related_name='wm_comment', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='flag',
            name='content_type',
            field=models.ForeignKey(related_name='wm_flag', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='follow',
            name='content_type',
            field=models.ForeignKey(related_name='wm_follow', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='like',
            name='content_type',
            field=models.ForeignKey(related_name='wm_like', to='contenttypes.ContentType'),
        ),
    ]
