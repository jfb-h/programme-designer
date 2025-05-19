from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key, [])

@register.filter
def sum_attr(items, attr):
    total = 0
    for item in items:
        value = getattr(item, attr, None)
        if value is not None:
            try:
                total += float(value)
            except Exception:
                pass
    return total
