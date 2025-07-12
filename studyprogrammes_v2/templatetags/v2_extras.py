from django import template
import math

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
def calculate_classes(student_count, max_participants):
    """Calculate number of classes needed given student count and max participants per class."""
    
    # Convert to int if they're strings or handle empty values
    try:
        student_count = int(student_count) if student_count else 0
        max_participants = int(max_participants) if max_participants else 0
    except (ValueError, TypeError):
        return 0
    
    if student_count <= 0 or max_participants <= 0:
        return 0
    
    result = math.ceil(student_count / max_participants)
    return result

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
        'physische_geographie': 'PG',
        'humangeographie': 'HG',
        'methoden': 'M/A',
        'übergreifend': 'HG/PG',
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

@register.filter
def module_has_regional_lpo(module):
    """Check if module has regional LPO relevance."""
    if not module or not hasattr(module, 'has_regional_lpo'):
        return False
    return module.has_regional_lpo()

@register.filter
def module_has_excursion_lpo(module):
    """Check if module has excursion LPO relevance."""
    if not module or not hasattr(module, 'has_excursion_lpo'):
        return False
    return module.has_excursion_lpo()

@register.filter
def semester_short(semester_type):
    """Convert semester type to short code."""
    short_codes = {
        'winter': 'WS',
        'summer': 'SS',
        'wintersemester': 'WS',
        'sommersemester': 'SS',
    }
    return short_codes.get(semester_type.lower() if semester_type else '', semester_type)

@register.filter
def programme_type_short(programme_type):
    """Convert programme type to short code."""
    short_codes = {
        'bachelor_100': 'BA100',
        'bachelor_60': 'BA60',
        'bachelor_30': 'BA30',
        'lehramt_vertieft': 'LA Vert',
        'lehramt_nicht_vertieft': 'LA nVert',
        'lehramt_mittelschule': 'LA MS',
        'lehramt_grundschule': 'LA GS',
        'master_hg': 'MA-HG',
        'master_pg': 'MA-PG',
    }
    return short_codes.get(programme_type, programme_type.upper()[:6])

@register.filter
def calculate_required_classes(course, context_data):
    """
    Calculate required classes for a course given programme and student counts.
    Usage: {{ course|calculate_required_classes:programme_and_student_counts }}
    """
    try:
        # Extract programme and student_counts from context
        if isinstance(context_data, dict):
            programme = context_data.get('programme')
            student_counts = context_data.get('student_counts', {})
        else:
            # Fallback if just student_counts passed
            programme = None
            student_counts = context_data if context_data else {}
        
        return course.calculate_required_classes(programme, student_counts)
    except Exception:
        return {'min_classes': 'Error', 'max_classes': 'Error', 'no_limit': True}

@register.filter
def calculate_sws_range(course, student_counts):
    """Calculate SWS range for a course based on number of classes needed."""
    if not course.max_participants or not course.sws:
        return course.sws
    
    min_students = student_counts.get('min', {}).get(course.semester, 0) if student_counts else 0
    max_students = student_counts.get('max', {}).get(course.semester, 0) if student_counts else 0
    
    if min_students == 0 and max_students == 0:
        return course.sws
    
    min_classes = calculate_classes(min_students, course.max_participants)
    max_classes = calculate_classes(max_students, course.max_participants)
    
    min_sws = course.sws * min_classes
    max_sws = course.sws * max_classes
    
    if min_sws == max_sws:
        return min_sws
    else:
        return f"{min_sws}-{max_sws}"

@register.filter
def module_sws_range(module, student_counts):
    """Calculate SWS range for a module based on courses and class requirements."""
    if not hasattr(module, 'get_sws_range'):
        return module.total_sws
    return module.get_sws_range(student_counts)

@register.filter
def module_semester_range(module):
    """Get the semester range for a module."""
    if not hasattr(module, 'get_semester_range'):
        return None
    return module.get_semester_range()

@register.filter
def programme_ects_by_course_type(programme):
    """Get ECTS breakdown by course type for a programme."""
    if not hasattr(programme, 'get_ects_by_course_type'):
        return {}
    return programme.get_ects_by_course_type()

@register.filter
def programme_ects_by_discipline(programme):
    """Get ECTS breakdown by discipline for a programme."""
    if not hasattr(programme, 'get_ects_by_discipline'):
        return {}
    return programme.get_ects_by_discipline()

@register.filter
def programme_ects_by_lpo(programme):
    """Get ECTS breakdown by LPO category for a programme."""
    if not hasattr(programme, 'get_ects_by_lpo_category'):
        return {}
    return programme.get_ects_by_lpo_category()

@register.filter
def programme_sws_range_total(programme, student_counts):
    """Get total SWS range for a programme."""
    if not hasattr(programme, 'get_sws_range_total'):
        return programme.total_sws if hasattr(programme, 'total_sws') else 0
    return programme.get_sws_range_total(student_counts)

@register.filter
def programme_sws_range_by_course_type(programme, student_counts):
    """Get SWS range breakdown by course type for a programme."""
    if not hasattr(programme, 'get_sws_range_by_course_type'):
        return {}
    return programme.get_sws_range_by_course_type(student_counts)

@register.filter
def programme_sws_range_by_discipline(programme, student_counts):
    """Get SWS range breakdown by discipline for a programme."""
    if not hasattr(programme, 'get_sws_range_by_discipline'):
        return {}
    return programme.get_sws_range_by_discipline(student_counts)

@register.filter
def get_display_name(value, choices_class):
    """Get display name for a choice field value."""
    try:
        for choice_value, choice_display in choices_class.choices:
            if choice_value == value:
                return choice_display
        return value
    except:
        return value

@register.filter
def semester_ects_total(programme, semester):
    """Get total ECTS for a specific semester in a programme."""
    if not hasattr(programme, 'get_semester_ects_total'):
        # Fallback calculation
        total = 0
        for module in programme.modules.all():
            for course in module.courses.filter(semester=semester):
                total += course.ects or 0
        return total
    return programme.get_semester_ects_total(semester)

@register.filter
def semester_sws_range(programme, semester):
    """Get SWS range for a specific semester in a programme."""
    try:
        semester = int(semester)
        min_total = 0
        max_total = 0
        
        # Get all courses for this semester
        for module in programme.modules.all():
            for course in module.courses.filter(semester=semester):
                course_sws = course.sws or 0
                
                if course.max_participants:
                    # Since we don't have access to student_counts in this context,
                    # we'll use reasonable defaults or check if programme has student data
                    min_students = 20  # Default minimum
                    max_students = 30  # Default maximum
                    
                    min_classes = calculate_classes(min_students, course.max_participants)
                    max_classes = calculate_classes(max_students, course.max_participants)
                    
                    min_total += course_sws * min_classes
                    max_total += course_sws * max_classes
                else:
                    # No participant limit, courses run once
                    min_total += course_sws
                    max_total += course_sws
        
        if min_total == max_total:
            return min_total
        else:
            return f"{min_total}-{max_total}"
    except Exception:
        return "Error"

@register.filter
def semester_sws_with_students(programme, args):
    """Get SWS range for a specific semester with explicit student counts."""
    try:
        # Parse arguments: semester:min_students:max_students
        parts = str(args).split(':')
        if len(parts) >= 3:
            semester = int(parts[0])
            min_students = int(parts[1]) if parts[1] else 0
            max_students = int(parts[2]) if parts[2] else 0
        else:
            semester = int(parts[0])
            min_students = 20  # Default
            max_students = 30  # Default
        
        min_total = 0
        max_total = 0
        
        # Get all courses for this semester
        for module in programme.modules.all():
            for course in module.courses.filter(semester=semester):
                course_sws = course.sws or 0
                
                if course.max_participants and min_students > 0 and max_students > 0:
                    min_classes = calculate_classes(min_students, course.max_participants)
                    max_classes = calculate_classes(max_students, course.max_participants)
                    
                    min_total += course_sws * min_classes
                    max_total += course_sws * max_classes
                else:
                    # No participant limit or no students, courses run once
                    min_total += course_sws
                    max_total += course_sws
        
        if min_total == max_total:
            return min_total
        else:
            return f"{min_total}-{max_total}"
    except Exception:
        return "Error"

@register.filter
def programme_target_ects_per_semester(programme_type):
    """Get target ECTS per semester for programme type."""
    target_ects = {
        'bachelor_100': 30,
        'bachelor_60': 20,  # Assuming 60 ECTS over 3 semesters
        'bachelor_30': 15,  # Assuming 30 ECTS over 2 semesters
        'lehramt_vertieft': 30,
        'lehramt_nicht_vertieft': 25,
        'lehramt_mittelschule': 25,
        'lehramt_grundschule': 25,
        'master_hg': 30,
        'master_pg': 30,
    }
    return target_ects.get(programme_type, 30)  # Default to 30

@register.simple_tag
def semester_sws_calculation(programme, semester, student_counts):
    """Calculate SWS range for a semester using student counts."""
    try:
        semester = int(semester)
        min_students = student_counts.get('min', {}).get(semester, 0) if student_counts else 0
        max_students = student_counts.get('max', {}).get(semester, 0) if student_counts else 0
        
        min_total = 0
        max_total = 0
        
        # Get all courses for this semester
        for module in programme.modules.all():
            for course in module.courses.filter(semester=semester):
                course_sws = course.sws or 0
                
                if course.max_participants and min_students > 0 and max_students > 0:
                    min_classes = calculate_classes(min_students, course.max_participants)
                    max_classes = calculate_classes(max_students, course.max_participants)
                    
                    min_total += course_sws * min_classes
                    max_total += course_sws * max_classes
                else:
                    # No participant limit or no students, courses run once
                    min_total += course_sws
                    max_total += course_sws
        
        if min_total == max_total:
            return min_total
        else:
            return f"{min_total}-{max_total}"
    except Exception:
        return "Error"

@register.filter
def get_programme_type_display(programme_type_code):
    """Get display name for programme type code."""
    from ..models import ProgrammeType
    programme_types_dict = dict(ProgrammeType.choices)
    return programme_types_dict.get(programme_type_code, programme_type_code)

@register.filter
def programme_sws_range_with_revision_counts(programme, revision):
    """Get SWS range for a programme using the revision's aggregated student counts."""
    if not programme or not revision:
        return "—"
    
    # Get aggregated student counts from the revision
    student_counts_data = revision.get_aggregate_student_counts()
    student_counts = {
        'min': {sem: data['min_students'] for sem, data in student_counts_data.items()},
        'max': {sem: data['max_students'] for sem, data in student_counts_data.items()}
    }
    
    return programme.get_sws_range_total(student_counts)
