from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get an item from a dictionary by key."""
    if dictionary and key:
        return dictionary.get(key)
    return None

@register.filter  
def dict_get(dictionary, key):
    """Template filter to get an item from a dictionary by key - alias for get_item."""
    if dictionary and key:
        return dictionary.get(key)
    return None

@register.filter
def course_type_short(course_type):
    """Convert course type to short code."""
    short_codes = {
        'vorlesung': 'VL',
        'uebung': 'Ü',
        'seminar': 'S',
        'gelände': 'G',
        'thesis': 'T',
    }
    return short_codes.get(course_type, course_type.upper()[:2])

@register.filter
def discipline_short(discipline):
    """Convert discipline to short code."""
    short_codes = {
        'physische_geographie': 'PhysGeo',
        'humangeographie': 'HumGeo',
        'methoden': 'Methoden',
        'übergreifend': 'HG / PG',
    }
    return short_codes.get(discipline, discipline[:7] if discipline else '')

@register.filter
def has_regional_excursion_lpo(course):
    """Check if course has regional or excursion LPO relevance."""
    if not course or not hasattr(course, 'lpo_relevance'):
        return False
    
    lpo_names = [lpo.name for lpo in course.lpo_relevance.all()]
    return 'regional' in lpo_names or 'exkursion' in lpo_names

@register.filter
def has_regional_lpo(course):
    """Check if course has regional LPO relevance."""
    if not course or not hasattr(course, 'lpo_relevance'):
        return False
    
    lpo_names = [lpo.name for lpo in course.lpo_relevance.all()]
    return 'regional' in lpo_names

@register.filter
def has_excursion_lpo(course):
    """Check if course has excursion LPO relevance."""
    if not course or not hasattr(course, 'lpo_relevance'):
        return False
    
    lpo_names = [lpo.name for lpo in course.lpo_relevance.all()]
    return 'exkursion' in lpo_names
