import json

import django
from application_masters.models import *
from django import template
from django.conf import settings
from django.contrib.auth.models import User

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
