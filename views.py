from django import template
from datetime import datetime

register = template.Library()

@register.filter
def pending_days(financial_bid_open_date):
    if not financial_bid_open_date:
        return ""
    
    today = datetime.now().date()
    return (today - financial_bid_open_date).days

<td>{{ item.financial_bid_open_date|pending_days }}</td>
