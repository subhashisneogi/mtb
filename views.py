from django import template
from datetime import datetime
from django.utils import timezone

register = template.Library()

@register.filter
def pending_days(financial_bid_open_date):
    if not financial_bid_open_date:
        return ""

    # convert string to date if needed
    if isinstance(financial_bid_open_date, str):
        try:
            financial_bid_open_date = datetime.strptime(financial_bid_open_date, "%Y-%m-%d").date()
        except:
            return ""

    today = timezone.now().date()
    return (today - financial_bid_open_date).days
