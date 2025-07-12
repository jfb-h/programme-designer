from django import template
register = template.Library()

@register.filter
def get_item(container, key):
    """Get item from dict or return empty dict if key not found"""
    if hasattr(container, 'get'):
        return container.get(key, {})
    elif hasattr(container, '__getitem__'):
        try:
            return container[key]
        except (KeyError, IndexError, TypeError):
            return {}
    return {}

@register.filter
def course_type_short(course_type):
    """Convert course type to short display format"""
    course_type_map = {
        'vorlesung': 'VL',
        'uebung': 'Ü',
        'seminar': 'S',
        'gelände': 'G',
        'thesis': 'T',
    }
    return course_type_map.get(course_type, course_type)

@register.filter
def discipline_short(discipline):
    """Convert discipline to short display format"""
    discipline_map = {
        'physische_geographie': 'Phys. Geo',
        'humangeographie': 'Human Geo',
        'methoden': 'Methoden',
        'übergreifend': 'Übergreifend',
    }
    return discipline_map.get(discipline, discipline)