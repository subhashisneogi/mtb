from django import template

register = template.Library()

@register.filter
def unique(value):
    seen = set()
    unique_list = []
    for item in value:
        if item not in seen:
            seen.add(item)
            unique_list.append(item)
    return unique_list