# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-08-04 02:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_default_address'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='receive',
            new_name='receiver',
        ),
    ]
