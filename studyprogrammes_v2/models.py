from django.conf import settings
from django.db import models


class CourseType(models.TextChoices):
    VORLESUNG = 'vorlesung', 'Vorlesung'
    UEBUNG = 'uebung', 'Übung'
    SEMINAR = 'seminar', 'Seminar'
    FIELDTRIP = 'gelände', 'Geländeseminar'
    THESIS = 'thesis', 'Thesis'


class Discipline(models.TextChoices):
    PHYSISCHE_GEOGRAPHIE = 'physische_geographie', 'Physische Geographie'
    HUMANGEOGRAPHIE = 'humangeographie', 'Humangeographie'
    METHODEN = 'methoden', 'Methoden'
    UEBERGREIFEND = 'übergreifend', 'Übergreifend'


class LPO(models.TextChoices):
    REGIONAL = 'regional', 'Regional'
    EXKURSION = 'exkursion', 'Exkursion'


class LPOCategory(models.Model):
    """Model for LPO relevance categories to enable many-to-many relationships."""
    name = models.CharField(max_length=20, choices=LPO.choices, unique=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "LPO Category"
        verbose_name_plural = "LPO Categories"


class ProgrammeType(models.TextChoices):
    BACHELOR_100 = 'bachelor_100', 'Bachelor 100'
    BACHELOR_60 = 'bachelor_60', 'Bachelor 60'
    BACHELOR_30 = 'bachelor_30', 'Bachelor 30'
    LEHRAMT_VERTIEFT = 'lehramt_vertieft', 'Lehramt Vertieft'
    LEHRAMT_NICHT_VERTIEFT = 'lehramt_nicht_vertieft', 'Lehramt Nicht Vertieft'
    LEHRAMT_MITTELSCHULE = 'lehramt_mittelschule', 'Lehramt Mittelschule'
    LEHRAMT_GRUNDSCHULE = 'lehramt_grundschule', 'Lehramt Grundschule'
    MASTER_HG = 'master_hg', 'Master Humangeographie'
    MASTER_PG = 'master_pg', 'Master Physische Geographie'


class Course(models.Model):
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    semester = models.PositiveIntegerField(help_text="Recommended semester")
    course_type = models.CharField(max_length=20, choices=CourseType.choices)
    discipline = models.CharField(max_length=25, choices=Discipline.choices)
    lpo_relevance = models.ManyToManyField(
        LPOCategory,
        blank=True,
        help_text="LPO relevance categories"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_v2', null=True, blank=True)
    
    # Additional fields for practical course management
    ects = models.PositiveIntegerField(default=6, help_text="ECTS")
    sws = models.PositiveIntegerField(default=2, help_text="Semesterwochenstunden")
    max_participants = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def calculate_required_classes(self, programme, student_counts):
        """
        Calculate how many parallel classes are needed to serve all students.
        
        Args:
            programme: Programme instance
            student_counts: Dict with 'min' and 'max' student counts per semester
        
        Returns:
            Dict with 'min_classes' and 'max_classes' needed
        """
        if not self.max_participants:
            return {'min_classes': 'N/A', 'max_classes': 'N/A', 'no_limit': True}
        
        # Find which semester this course is offered in
        course_semester = self.semester
        
        # Get student counts for this semester
        min_students = student_counts.get('min', {}).get(course_semester, 0)
        max_students = student_counts.get('max', {}).get(course_semester, 0)
        
        # Calculate required classes (round up)
        import math
        min_classes = math.ceil(min_students / self.max_participants) if min_students > 0 else 0
        max_classes = math.ceil(max_students / self.max_participants) if max_students > 0 else 0
        
        return {
            'min_classes': min_classes,
            'max_classes': max_classes,
            'no_limit': False,
            'semester': course_semester,
            'min_students': min_students,
            'max_students': max_students
        }


class Module(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Display order within programme")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    certificate = models.TextField(blank=True, help_text="Certificate or qualification information for this module")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='modules_v2', null=True, blank=True)
    courses = models.ManyToManyField(Course, related_name='modules', blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def total_ects(self):
        """Calculate total ECTS credits for this module."""
        return sum(course.ects for course in self.courses.all())

    @property
    def total_sws(self):
        """Calculate total ECTS credits for this module."""
        return sum(course.sws for course in self.courses.all())
    
    def get_sws_range(self, student_counts=None):
        """Calculate SWS range for this module based on courses and class requirements."""
        if not student_counts:
            return self.total_sws
        
        total_min_sws = 0
        total_max_sws = 0
        
        for course in self.courses.all():
            if course.max_participants and course.sws:
                min_students = student_counts.get('min', {}).get(course.semester, 0)
                max_students = student_counts.get('max', {}).get(course.semester, 0)
                
                if min_students > 0 or max_students > 0:
                    import math
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    
                    total_min_sws += course.sws * min_classes
                    total_max_sws += course.sws * max_classes
                else:
                    # No student data, use base SWS
                    total_min_sws += course.sws
                    total_max_sws += course.sws
            else:
                # No max participants, use base SWS
                total_min_sws += course.sws
                total_max_sws += course.sws
        
        if total_min_sws == total_max_sws:
            return total_min_sws
        else:
            return f"{total_min_sws}-{total_max_sws}"

    def get_lpo_relevance(self):
        """Get all unique LPO relevance categories from courses in this module."""
        lpo_names = set()
        for course in self.courses.all():
            for lpo in course.lpo_relevance.all():
                lpo_names.add(lpo.name)
        return list(lpo_names)
    
    def has_regional_lpo(self):
        """Check if any course in this module has regional LPO relevance."""
        return 'regional' in self.get_lpo_relevance()
    
    def has_excursion_lpo(self):
        """Check if any course in this module has excursion LPO relevance."""
        return 'exkursion' in self.get_lpo_relevance()
    
    def get_semester_range(self):
        """Get the semester range for courses in this module."""
        semesters = [course.semester for course in self.courses.all() if course.semester]
        if not semesters:
            return None
        
        min_semester = min(semesters)
        max_semester = max(semesters)
        
        if min_semester == max_semester:
            return f"{min_semester}. Sem"
        else:
            return f"{min_semester}.-{max_semester}. Sem"


class ProgrammeModule(models.Model):
    """Through model to handle module ordering within programmes."""
    programme = models.ForeignKey('Programme', on_delete=models.CASCADE)
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="Order of module within this programme")
    
    class Meta:
        ordering = ['order']
        unique_together = ('programme', 'module')
    
    def __str__(self):
        return f"{self.programme.name} - {self.module.name} (order: {self.order})"


class Programme(models.Model):
    name = models.CharField(max_length=200)
    programme_type = models.CharField(max_length=30, choices=ProgrammeType.choices)
    comment = models.TextField(blank=True, help_text="Additional notes or comments about this programme")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='programmes_v2', null=True, blank=True)
    modules = models.ManyToManyField(Module, through='ProgrammeModule', related_name='programmes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_programme_type_display()})"

    def get_ordered_modules(self):
        """Get modules ordered by their position in this programme."""
        from django.db.models import Prefetch
        return self.modules.prefetch_related(
            Prefetch('courses', queryset=Course.objects.select_related().prefetch_related('lpo_relevance').order_by('semester'))
        ).order_by('programmemodule__order')

    @property
    def total_ects(self):
        """Calculate total ECTS credits for this programme."""
        return sum(module.total_ects for module in self.modules.all())
    
    @property
    def total_sws(self):
        """Calculate total SWS for this programme."""
        return sum(module.total_sws for module in self.modules.all())
    
    @property
    def total_courses(self):
        """Calculate total number of courses in this programme."""
        return sum(module.courses.count() for module in self.modules.all())

    # ECTS Statistics Methods
    def get_ects_by_course_type(self):
        """Get ECTS breakdown by course type."""
        from django.db.models import Sum
        course_type_ects = {}
        
        # Get all courses in this programme
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        
        for course_type_choice in CourseType.choices:
            course_type_key = course_type_choice[0]
            ects_sum = all_courses.filter(course_type=course_type_key).aggregate(
                total=Sum('ects')
            )['total'] or 0
            if ects_sum > 0:
                course_type_ects[course_type_key] = ects_sum
        
        return course_type_ects
    
    def get_ects_by_discipline(self):
        """Get ECTS breakdown by discipline."""
        from django.db.models import Sum
        discipline_ects = {}
        
        # Get all courses in this programme
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        
        for discipline_choice in Discipline.choices:
            discipline_key = discipline_choice[0]
            ects_sum = all_courses.filter(discipline=discipline_key).aggregate(
                total=Sum('ects')
            )['total'] or 0
            if ects_sum > 0:
                discipline_ects[discipline_key] = ects_sum
        
        return discipline_ects
    
    def get_ects_by_lpo_category(self):
        """Get ECTS breakdown by LPO category."""
        from django.db.models import Sum
        lpo_ects = {}
        
        # Get all courses in this programme
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        
        # Regional LPO courses
        regional_ects = all_courses.filter(
            lpo_relevance__name='regional'
        ).aggregate(total=Sum('ects'))['total'] or 0
        if regional_ects > 0:
            lpo_ects['regional'] = regional_ects
        
        # Excursion LPO courses
        excursion_ects = all_courses.filter(
            lpo_relevance__name='exkursion'
        ).aggregate(total=Sum('ects'))['total'] or 0
        if excursion_ects > 0:
            lpo_ects['exkursion'] = excursion_ects
        
        return lpo_ects

    # SWS Statistics Methods
    def get_sws_range_total(self, student_counts=None):
        """Get total SWS range for the programme."""
        if not student_counts:
            return self.total_sws
        
        total_min_sws = 0
        total_max_sws = 0
        
        for module in self.modules.all():
            sws_range = module.get_sws_range(student_counts)
            if isinstance(sws_range, str) and '-' in sws_range:
                min_sws, max_sws = map(int, sws_range.split('-'))
                total_min_sws += min_sws
                total_max_sws += max_sws
            else:
                sws_val = int(sws_range) if sws_range else 0
                total_min_sws += sws_val
                total_max_sws += sws_val
        
        if total_min_sws == total_max_sws:
            return total_min_sws
        else:
            return f"{total_min_sws}-{total_max_sws}"
    
    def get_sws_range_by_course_type(self, student_counts=None):
        """Get SWS range breakdown by course type."""
        course_type_sws = {}
        
        # Get all courses in this programme
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        
        for course_type_choice in CourseType.choices:
            course_type_key = course_type_choice[0]
            courses = all_courses.filter(course_type=course_type_key)
            
            if not courses.exists():
                continue
            
            total_min_sws = 0
            total_max_sws = 0
            
            for course in courses:
                if student_counts and course.max_participants:
                    # Calculate based on student counts
                    semester = course.semester
                    min_students = student_counts.get('min', {}).get(semester, 0)
                    max_students = student_counts.get('max', {}).get(semester, 0)
                    
                    import math
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    
                    total_min_sws += course.sws * min_classes
                    total_max_sws += course.sws * max_classes
                else:
                    # Use base SWS
                    total_min_sws += course.sws
                    total_max_sws += course.sws
            
            if total_min_sws > 0 or total_max_sws > 0:
                if total_min_sws == total_max_sws:
                    course_type_sws[course_type_key] = total_min_sws
                else:
                    course_type_sws[course_type_key] = f"{total_min_sws}-{total_max_sws}"
        
        return course_type_sws
    
    def get_sws_range_by_discipline(self, student_counts=None):
        """Get SWS range breakdown by discipline."""
        discipline_sws = {}
        
        # Get all courses in this programme
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        
        for discipline_choice in Discipline.choices:
            discipline_key = discipline_choice[0]
            courses = all_courses.filter(discipline=discipline_key)
            
            if not courses.exists():
                continue
            
            total_min_sws = 0
            total_max_sws = 0
            
            for course in courses:
                if student_counts and course.max_participants:
                    # Calculate based on student counts
                    semester = course.semester
                    min_students = student_counts.get('min', {}).get(semester, 0)
                    max_students = student_counts.get('max', {}).get(semester, 0)
                    
                    import math
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    
                    total_min_sws += course.sws * min_classes
                    total_max_sws += course.sws * max_classes
                else:
                    # Use base SWS
                    total_min_sws += course.sws
                    total_max_sws += course.sws
            
            if total_min_sws > 0 or total_max_sws > 0:
                if total_min_sws == total_max_sws:
                    discipline_sws[discipline_key] = total_min_sws
                else:
                    discipline_sws[discipline_key] = f"{total_min_sws}-{total_max_sws}"
        
        return discipline_sws

    def get_semester_count(self):
        """Get the number of semesters for this programme type."""
        bachelor_types = ['bachelor_100', 'bachelor_60', 'bachelor_30']
        master_types = ['master_hg', 'master_pg']
        lehramt_types = ['lehramt_vertieft', 'lehramt_nicht_vertieft', 'lehramt_mittelschule', 'lehramt_grundschule']
        
        if self.programme_type in bachelor_types:
            return 6  # 3 years * 2 semesters
        elif self.programme_type in master_types:
            return 4  # 2 years * 2 semesters
        elif self.programme_type in lehramt_types:
            return 8  # 4 years * 2 semesters
        else:
            return 6  # Default


class ProgrammeStudentCount(models.Model):
    """Model for tracking minimum and maximum expected student counts per semester."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='student_counts')
    semester = models.PositiveIntegerField(help_text="Semester number (1, 2, 3, etc.)")
    min_students = models.PositiveIntegerField(default=0, help_text="Minimum expected students")
    max_students = models.PositiveIntegerField(default=0, help_text="Maximum expected students")

    class Meta:
        unique_together = ('programme', 'semester')
        ordering = ['programme', 'semester']

    def __str__(self):
        return f"{self.programme.name} Sem {self.semester}: {self.min_students}-{self.max_students}"


class Revision(models.Model):
    """A revision corresponding to Julia struct Revision.
    
    A revision is a collection of programmes, ideally one for each programme type
    that exists in the system at the time of the revision.
    """
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='revisions'
    )
    programmes = models.ManyToManyField(Programme, related_name='revisions', blank=True)

    class Meta:
        ordering = ['-date', '-order']

    def __str__(self):
        return f"{self.name} ({self.author}, {self.date})"
    
    def get_programmes_by_type(self):
        """Get programmes in this revision organized by programme type."""
        programmes_by_type = {}
        for programme in self.programmes.all():
            programmes_by_type[programme.programme_type] = programme
        return programmes_by_type
    
    def get_missing_programme_types(self):
        """Get programme types that are not represented in this revision."""
        covered_types = set(self.programmes.values_list('programme_type', flat=True))
        all_types = set([choice[0] for choice in ProgrammeType.choices])
        return all_types - covered_types
    
    def is_complete(self):
        """Check if this revision has a programme for every programme type."""
        return len(self.get_missing_programme_types()) == 0
    
    def get_available_programmes_for_type(self, programme_type, user=None):
        """Get all available programmes of a specific type that could be added to this revision."""
        queryset = Programme.objects.filter(programme_type=programme_type)
        if user:
            queryset = queryset.filter(user=user)
        return queryset.exclude(revisions=self)
    
    # Aggregate Statistics Methods
    def get_total_ects(self):
        """Get total ECTS across all programmes in this revision."""
        return sum(programme.total_ects for programme in self.programmes.all())
    
    def get_total_sws(self):
        """Get total SWS across all programmes in this revision."""
        return sum(programme.total_sws for programme in self.programmes.all())
    
    def get_total_courses(self):
        """Get total number of courses across all programmes in this revision."""
        return sum(programme.total_courses for programme in self.programmes.all())
    
    def get_total_modules(self):
        """Get total number of modules across all programmes in this revision."""
        return sum(programme.modules.count() for programme in self.programmes.all())
    
    def get_ects_by_course_type(self):
        """Get ECTS breakdown by course type across all programmes."""
        from django.db.models import Sum
        from .models import Course, CourseType
        
        course_type_ects = {}
        
        # Get all courses from all programmes in this revision
        all_courses = Course.objects.filter(
            modules__programmes__revisions=self
        ).distinct()
        
        for course_type_choice in CourseType.choices:
            course_type_key = course_type_choice[0]
            ects_sum = all_courses.filter(course_type=course_type_key).aggregate(
                total=Sum('ects')
            )['total'] or 0
            if ects_sum > 0:
                course_type_ects[course_type_key] = ects_sum
        
        return course_type_ects
    
    def get_ects_by_discipline(self):
        """Get ECTS breakdown by discipline across all programmes."""
        from django.db.models import Sum
        from .models import Course, Discipline
        
        discipline_ects = {}
        
        # Get all courses from all programmes in this revision
        all_courses = Course.objects.filter(
            modules__programmes__revisions=self
        ).distinct()
        
        for discipline_choice in Discipline.choices:
            discipline_key = discipline_choice[0]
            ects_sum = all_courses.filter(discipline=discipline_key).aggregate(
                total=Sum('ects')
            )['total'] or 0
            if ects_sum > 0:
                discipline_ects[discipline_key] = ects_sum
        
        return discipline_ects
    
    def get_ects_by_lpo_category(self):
        """Get ECTS breakdown by LPO category across all programmes."""
        from django.db.models import Sum
        from .models import Course
        
        lpo_ects = {}
        
        # Get all courses from all programmes in this revision
        all_courses = Course.objects.filter(
            modules__programmes__revisions=self
        ).distinct()
        
        # Regional LPO courses
        regional_ects = all_courses.filter(
            lpo_relevance__name='regional'
        ).aggregate(total=Sum('ects'))['total'] or 0
        if regional_ects > 0:
            lpo_ects['regional'] = regional_ects
        
        # Excursion LPO courses
        excursion_ects = all_courses.filter(
            lpo_relevance__name='exkursion'
        ).aggregate(total=Sum('ects'))['total'] or 0
        if excursion_ects > 0:
            lpo_ects['excursion'] = excursion_ects
        
        return lpo_ects
    
    def get_aggregate_student_counts(self):
        """Get aggregated student counts across all programmes by semester."""
        from django.db.models import Sum
        
        # Get all student counts from programmes in this revision
        student_counts = ProgrammeStudentCount.objects.filter(
            programme__revisions=self
        ).values('semester').annotate(
            total_min=Sum('min_students'),
            total_max=Sum('max_students')
        ).order_by('semester')
        
        # Convert to dictionary format
        counts_by_semester = {}
        for count in student_counts:
            semester = count['semester']
            counts_by_semester[semester] = {
                'min_students': count['total_min'],
                'max_students': count['total_max']
            }
        
        return counts_by_semester
    
    def get_sws_range_total(self):
        """Get total SWS range across all programmes in this revision."""
        total_min_sws = 0
        total_max_sws = 0
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        student_counts = {
            'min': {sem: data['min_students'] for sem, data in student_counts_data.items()},
            'max': {sem: data['max_students'] for sem, data in student_counts_data.items()}
        }
        
        for programme in self.programmes.all():
            sws_range = programme.get_sws_range_total(student_counts)
            if isinstance(sws_range, str) and '-' in sws_range:
                min_sws, max_sws = map(int, sws_range.split('-'))
                total_min_sws += min_sws
                total_max_sws += max_sws
            else:
                sws_val = int(sws_range) if sws_range else 0
                total_min_sws += sws_val
                total_max_sws += sws_val
        
        if total_min_sws == total_max_sws:
            return total_min_sws
        else:
            return f"{total_min_sws}-{total_max_sws}"
    
    def get_sws_by_course_type(self):
        """Get SWS breakdown by course type across all programmes in this revision."""
        import math
        from collections import defaultdict
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        course_type_sws = {}
        
        # Get all courses in all programmes in this revision
        all_courses = Course.objects.filter(modules__programmes__in=self.programmes.all()).distinct()
        
        for course_type_choice in CourseType.choices:
            course_type_key = course_type_choice[0]
            courses = all_courses.filter(course_type=course_type_key)
            
            if not courses.exists():
                continue
            
            total_min_sws = 0
            total_max_sws = 0
            
            for course in courses:
                semester = course.semester
                semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
                min_students = semester_data['min_students']
                max_students = semester_data['max_students']
                
                if course.max_participants and course.sws and (min_students > 0 or max_students > 0):
                    # Calculate number of classes needed
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    
                    total_min_sws += course.sws * min_classes
                    total_max_sws += course.sws * max_classes
                else:
                    # No max participants or student data, use base SWS
                    total_min_sws += course.sws
                    total_max_sws += course.sws
            
            if total_min_sws > 0 or total_max_sws > 0:
                if total_min_sws == total_max_sws:
                    course_type_sws[course_type_key] = total_min_sws
                else:
                    course_type_sws[course_type_key] = f"{total_min_sws}-{total_max_sws}"
        
        return course_type_sws
    
    def get_sws_by_discipline(self):
        """Get SWS breakdown by discipline across all programmes in this revision."""
        import math
        from collections import defaultdict
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        discipline_sws = {}
        
        # Get all courses in all programmes in this revision
        all_courses = Course.objects.filter(modules__programmes__in=self.programmes.all()).distinct()
        
        for discipline_choice in Discipline.choices:
            discipline_key = discipline_choice[0]
            courses = all_courses.filter(discipline=discipline_key)
            
            if not courses.exists():
                continue
            
            total_min_sws = 0
            total_max_sws = 0
            
            for course in courses:
                semester = course.semester
                semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
                min_students = semester_data['min_students']
                max_students = semester_data['max_students']
                
                if course.max_participants and course.sws and (min_students > 0 or max_students > 0):
                    # Calculate number of classes needed
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    
                    total_min_sws += course.sws * min_classes
                    total_max_sws += course.sws * max_classes
                else:
                    # No max participants or student data, use base SWS
                    total_min_sws += course.sws
                    total_max_sws += course.sws
            
            if total_min_sws > 0 or total_max_sws > 0:
                if total_min_sws == total_max_sws:
                    discipline_sws[discipline_key] = total_min_sws
                else:
                    discipline_sws[discipline_key] = f"{total_min_sws}-{total_max_sws}"
        
        return discipline_sws

    def get_sws_by_semester_and_type(self):
        """Get SWS breakdown by semester and course type, accounting for shared courses."""
        import math
        from collections import defaultdict
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        # Structure: {semester: {course_type: sws_range}}
        result = defaultdict(lambda: defaultdict(int))
        
        # Get all courses across all programmes in this revision
        all_courses = Course.objects.filter(modules__programmes__in=self.programmes.all()).distinct()
        
        for course in all_courses:
            semester = course.semester
            course_type = course.course_type
            
            # Get total students needed for this course across all programmes
            semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
            min_students = semester_data['min_students']
            max_students = semester_data['max_students']
            
            if course.max_participants and course.sws and (min_students > 0 or max_students > 0):
                # Calculate number of classes needed
                min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                
                min_sws = course.sws * min_classes
                max_sws = course.sws * max_classes
                
                if min_sws == max_sws:
                    result[semester][course_type] += min_sws
                else:
                    # For ranges, we'll store as a tuple and format later
                    current = result[semester][course_type]
                    if isinstance(current, tuple):
                        result[semester][course_type] = (current[0] + min_sws, current[1] + max_sws)
                    else:
                        result[semester][course_type] = (current + min_sws, current + max_sws)
            else:
                # No max participants or student data, use base SWS
                result[semester][course_type] += course.sws
        
        # Convert tuples to range strings and ensure proper dict structure
        final_result = {}
        for semester in result:
            final_result[semester] = {}
            for course_type in result[semester]:
                value = result[semester][course_type]
                if isinstance(value, tuple) and value[0] != value[1]:
                    final_result[semester][course_type] = f"{value[0]}-{value[1]}"
                else:
                    final_result[semester][course_type] = value
        
        return final_result

    def get_sws_by_semester_and_discipline(self):
        """Get SWS breakdown by semester and discipline, accounting for shared courses."""
        import math
        from collections import defaultdict
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        # Structure: {semester: {discipline: sws_range}}
        result = defaultdict(lambda: defaultdict(int))
        
        # Get all courses across all programmes in this revision
        all_courses = Course.objects.filter(modules__programmes__in=self.programmes.all()).distinct()
        
        for course in all_courses:
            semester = course.semester
            discipline = course.discipline
            
            # Get total students needed for this course across all programmes
            semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
            min_students = semester_data['min_students']
            max_students = semester_data['max_students']
            
            if course.max_participants and course.sws and (min_students > 0 or max_students > 0):
                # Calculate number of classes needed
                min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                
                min_sws = course.sws * min_classes
                max_sws = course.sws * max_classes
                
                if min_sws == max_sws:
                    result[semester][discipline] += min_sws
                else:
                    # For ranges, we'll store as a tuple and format later
                    current = result[semester][discipline]
                    if isinstance(current, tuple):
                        result[semester][discipline] = (current[0] + min_sws, current[1] + max_sws)
                    else:
                        result[semester][discipline] = (current + min_sws, current + max_sws)
            else:
                # No max participants or student data, use base SWS
                result[semester][discipline] += course.sws
        
        # Convert tuples to range strings and ensure proper dict structure
        final_result = {}
        for semester in result:
            final_result[semester] = {}
            for discipline in result[semester]:
                value = result[semester][discipline]
                if isinstance(value, tuple) and value[0] != value[1]:
                    final_result[semester][discipline] = f"{value[0]}-{value[1]}"
                else:
                    final_result[semester][discipline] = value
        
        return final_result

    def get_winter_summer_sws(self):
        """Get SWS breakdown by winter (odd) and summer (even) semesters with ranges."""
        import math
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        winter_min_sws = 0  # odd semesters
        winter_max_sws = 0
        summer_min_sws = 0  # even semesters
        summer_max_sws = 0
        
        # Get all courses across all programmes in this revision
        all_courses = Course.objects.filter(modules__programmes__in=self.programmes.all()).distinct()
        
        for course in all_courses:
            semester = course.semester
            
            # Get total students needed for this course across all programmes
            semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
            min_students = semester_data['min_students']
            max_students = semester_data['max_students']
            
            if course.max_participants and course.sws and (min_students > 0 or max_students > 0):
                # Calculate number of classes needed for min and max students
                min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                course_min_sws = course.sws * min_classes
                course_max_sws = course.sws * max_classes
            else:
                # No max participants or student data, use base SWS
                course_min_sws = course.sws
                course_max_sws = course.sws
            
            # Odd semesters = Winter, Even semesters = Summer
            if semester % 2 == 1:  # Odd semester (1, 3, 5, 7, ...)
                winter_min_sws += course_min_sws
                winter_max_sws += course_max_sws
            else:  # Even semester (2, 4, 6, 8, ...)
                summer_min_sws += course_min_sws
                summer_max_sws += course_max_sws
        
        # Format as ranges or single values
        if winter_min_sws == winter_max_sws:
            winter_sws = winter_min_sws
        else:
            winter_sws = f"{winter_min_sws}-{winter_max_sws}"
            
        if summer_min_sws == summer_max_sws:
            summer_sws = summer_min_sws
        else:
            summer_sws = f"{summer_min_sws}-{summer_max_sws}"
        
        return {
            'winter_sws': winter_sws,
            'summer_sws': summer_sws
        }
