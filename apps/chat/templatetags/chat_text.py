from django import template

register = template.Library()


@register.filter
def strip_text(value):
    return "" if value is None else str(value).strip()
