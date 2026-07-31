from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    """Look up a dict field by a dynamic key, e.g. {{ item|get_item:col.key }}."""
    if isinstance(d, dict):
        return d.get(key, '')
    return getattr(d, key, '')
