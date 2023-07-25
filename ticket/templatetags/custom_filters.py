# templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def continue_if_false(value):
    return value if value else None
