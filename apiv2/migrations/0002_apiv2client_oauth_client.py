# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-15 11:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
        ('apiv2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiv2client',
            name='oauth_client',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='apiv2_client', to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
        ),
    ]