# main/templatetags/dict_filters.py

from django import template
register = template.Library()

@register.filter
def dict_key(d, key):
    return d.get(key, '')