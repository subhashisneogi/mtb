from django import template
import calendar
from django.db.models import Sum

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


# @register.filter
# def unique_names(profile_list):
#     if profile_list is None:
#         return [] 
    
#     seen = set()
#     unique_list = []
#     for item in profile_list:
#         if item.name:
#             if item.name and item.name not in seen:
#                 seen.add(item.name)
#                 unique_list.append(item.name)
#     return unique_list


@register.filter
def month_name(month_number):
    return calendar.month_name[month_number]


@register.filter
def format_number(num, round_to=2):
    num = float(num)
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{:.{}f}{}'.format(round(num, round_to), round_to, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

@register.filter 
def times(number):
    return range(number)


@register.filter
def sum_section_area(division):
    return division.section_set.aggregate(Sum('section_area'))['section_area__sum'] or 0


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)