from django import template

register = template.Library()

@register.filter
def dict_key(dictionary, key):
    """Returns the value of a dictionary using the given key."""
    return dictionary.get(key, 0)
