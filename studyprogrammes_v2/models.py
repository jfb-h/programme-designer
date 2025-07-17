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
    DIDAKTIK = 'didaktik', 'Didaktik'


class LPOCategory(models.Model):
    """Model for LPO relevance categories to enable many-to-many relationships."""
    name = models.CharField(max_length=20, choices=LPO.choices, unique=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "LPO Category"
        verbose_name_plural = "LPO Categories"


class ProgrammeType(models.TextChoices):
    BACHELOR_100 = 'bachelor_100', 'Bachelor'
    BACHELOR_60 = 'bachelor_60', 'Bachelor 60'
    BACHELOR_30 = 'bachelor_30', 'Bachelor 30'
    LEHRAMT_VERTIEFT = 'lehramt_vertieft', 'Lehramt Vertieft'
    LEHRAMT_NICHT_VERTIEFT = 'lehramt_nicht_vertieft', 'Lehramt Nicht Vertieft'
    LEHRAMT_MITTELSCHULE = 'lehramt_mittelschule', 'Lehramt Mittelschule'
    LEHRAMT_GRUNDSCHULE = 'lehramt_grundschule', 'Lehramt Grundschule'
    MASTER_HG = 'master_hg', 'Master Humangeographie'
    MASTER_PG = 'master_pg', 'Master Physische Geographie'


class CertificateOption(models.Model):
    """Predefined certificate options that can be selected for modules."""
    name = models.CharField(max_length=200, unique=True, help_text="Name of the certificate option")
    description = models.TextField(blank=True, help_text="Optional description of this certificate option")
    order = models.PositiveIntegerField(default=0, help_text="Display order in selection lists")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Certificate Option"
        verbose_name_plural = "Certificate Options"
    
    def __str__(self):
        return self.name


class Course(models.Model):
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # semester field removed
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
    
    # Sharing functionality
    is_shared = models.BooleanField(default=False, help_text="Whether this course is shared with other users")
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_courses_v2', null=True, blank=True, help_text="Original creator who shared this course")
    shared_at = models.DateTimeField(null=True, blank=True, help_text="When this course was shared")
    original_course = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_copies', help_text="Reference to original course if this is a shared copy")

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
    
    def create_copy(self):
        """Create a copy of this course with all its attributes and relationships."""
        course_copy = Course.objects.create(
            name=self.name,
            description=self.description,
            course_type=self.course_type,
            discipline=self.discipline,
            user=self.user,
            ects=self.ects,
            sws=self.sws,
            max_participants=self.max_participants,
            is_shared=self.is_shared,
            shared_by=self.shared_by,
            shared_at=self.shared_at,
            original_course=self if not self.original_course else self.original_course,
            order=self.order
        )
        # Copy many-to-many relationships
        course_copy.lpo_relevance.set(self.lpo_relevance.all())
        return course_copy

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
        # Semester logic removed
        
        # Get student counts for this semester
        min_students = 0  # No semester logic
        max_students = 0  # No semester logic
        
        # Calculate required classes (round up)
        import math
        min_classes = math.ceil(min_students / self.max_participants) if min_students > 0 else 0
        max_classes = math.ceil(max_students / self.max_participants) if max_students > 0 else 0
        
        return {
            'min_classes': min_classes,
            'max_classes': max_classes,
            'no_limit': False,
            'min_students': min_students,
            'max_students': max_students
        }


class Module(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Display order within programme")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    responsible_person = models.CharField(max_length=200, blank=True, help_text="Modulverantwortliche(r)")
    qualification_goals = models.TextField(blank=True, null=True, help_text="Qualification goals and learning outcomes for this module")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='modules_v2', null=True, blank=True)
    courses = models.ManyToManyField('Course', through='CourseModule', related_name='modules', blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def total_ects(self):
        """Calculate total ECTS credits for this module."""
        return sum(cm.course.ects for cm in self.get_coursemodules())

    @property
    def total_sws(self):
        """Calculate total SWS credits for this module."""
        return sum(cm.course.sws for cm in self.get_coursemodules())

    def get_coursemodules(self):
        """Return all CourseModule objects for this module, ordered by 'order'."""
        return self.coursemodule_set.select_related('course').order_by('order')

    def get_sws_range(self, student_counts=None):
        """Calculate SWS range for this module based on courses and class requirements, using CourseModule semester info."""
        if not student_counts:
            return self.total_sws

        total_min_sws = 0
        total_max_sws = 0

        for cm in self.get_coursemodules():
            course = cm.course
            semester = cm.semester
            min_students = 0
            max_students = 0
            if student_counts:
                min_students = student_counts.get('min', {}).get(semester, 0)
                max_students = student_counts.get('max', {}).get(semester, 0)
            if course.max_participants and course.sws:
                import math
                min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 1
                max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 1
                total_min_sws += course.sws * min_classes
                total_max_sws += course.sws * max_classes
            else:
                total_min_sws += course.sws if course.sws else 0
                total_max_sws += course.sws if course.sws else 0
        if total_min_sws == total_max_sws:
            return total_min_sws
        else:
            return f"{total_min_sws}-{total_max_sws}"

    def get_lpo_relevance(self):
        """Get all unique LPO relevance categories from courses in this module."""
        lpo_names = set()
        for cm in self.get_coursemodules():
            for lpo in cm.course.lpo_relevance.all():
                lpo_names.add(lpo.name)
        return list(lpo_names)

    def has_regional_lpo(self):
        """Check if any course in this module has regional LPO relevance."""
        return 'regional' in self.get_lpo_relevance()

    def has_excursion_lpo(self):
        """Check if any course in this module has excursion LPO relevance."""
        return 'exkursion' in self.get_lpo_relevance()

    def get_semester_range(self):
        """Get the semester range for courses in this module using CourseModule.semester."""
        semesters = [cm.semester for cm in self.get_coursemodules()]
        if not semesters:
            return None
        min_semester = min(semesters)
        max_semester = max(semesters)
        if min_semester == max_semester:
            return f"{min_semester}. Sem"
        else:
            return f"{min_semester}.-{max_semester}. Sem"

    def get_certificate_display(self):
        """Get formatted certificate display string."""
        try:
            module_cert = self.module_certificate
            
            # Check if we have group structure (new JSON-based system)
            if hasattr(module_cert, 'group_structure') and module_cert.group_structure and module_cert.group_structure.get('groups'):
                group_displays = []
                groups = module_cert.group_structure.get('groups', [])
                
                for group in groups:
                    option_ids = group.get('options', [])
                    if option_ids:
                        # Get option names from IDs
                        options = CertificateOption.objects.filter(id__in=option_ids)
                        option_names = [opt.name for opt in options]
                        
                        if group.get('internal_operator') == 'and':
                            group_display = ' UND '.join(option_names)
                        else:
                            group_display = ' ODER '.join(option_names)
                        
                        # Only add parentheses if there are multiple options in the group
                        if len(option_names) > 1:
                            group_displays.append(f'({group_display})')
                        else:
                            group_displays.append(group_display)
                
                if group_displays:
                    global_operator = module_cert.group_structure.get('global_operator', module_cert.global_operator)
                    if global_operator == 'and':
                        result = ' UND '.join(group_displays)
                    else:
                        result = ' ODER '.join(group_displays)
                    
                    if module_cert.comment:
                        result += f' - {module_cert.comment}'
                    
                    # Add graded/ungraded status in parentheses
                    if result:
                        graded_status = "benotet" if module_cert.is_graded else "unbenotet"
                        result = f"{result} ({graded_status})"
                    
                    return result
            
            # Fallback to simple display if no group structure
            if not module_cert.comment:
                return ''
            
            parts = []
            
            if module_cert.comment:
                parts.append(module_cert.comment)
            
            result = ' - '.join(parts) if parts else ''
            
            # Add graded/ungraded status in parentheses
            if result:
                graded_status = "benotet" if module_cert.is_graded else "unbenotet"
                result = f"{result} ({graded_status})"
            
            return result
            
        except ModuleCertificate.DoesNotExist:
            return ''


class CertificateGroup(models.Model):
    """Predefined certificate groups for organizing options."""
    name = models.CharField(max_length=100, unique=True, help_text="Name of the certificate group")
    description = models.TextField(blank=True, help_text="Optional description of this group")
    order = models.PositiveIntegerField(default=0, help_text="Display order in selection lists")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Certificate Group"
        verbose_name_plural = "Certificate Groups"
    
    def __str__(self):
        return self.name


class ModuleCertificate(models.Model):
    """Certificate configuration for a module with group-based options."""
    
    LOGIC_CHOICES = [
        ('and', 'UND'),
        ('or', 'ODER'),
    ]
    
    module = models.OneToOneField('Module', on_delete=models.CASCADE, related_name='module_certificate')
    global_operator = models.CharField(max_length=3, choices=LOGIC_CHOICES, default='and', help_text="How certificate groups should be combined")
    comment = models.TextField(blank=True, help_text="Additional certificate details or comments")
    is_graded = models.BooleanField(default=True, help_text="Whether this module is graded (benotet) or ungraded (unbenotet)")
    group_structure = models.JSONField(default=dict, blank=True, null=True, help_text="Complete group structure with options, operators, and order")
    
    
    class Meta:
        verbose_name = "Module Certificate"
        verbose_name_plural = "Module Certificates"
    
    def __str__(self):
        return f"Certificate for {self.module.name}"
    
    def get_display_text(self):
        """Get formatted display text for this certificate configuration."""
        return self._get_group_display_text()
    
    def _get_group_display_text(self):
        """Get display text for group-based certificates."""
        group_texts = []
        for cert_group in self.certificate_groups.all().order_by('order'):
            if cert_group.selected_options.exists():
                option_names = [opt.name for opt in cert_group.selected_options.all()]
                if cert_group.internal_operator == 'and':
                    group_text = ' UND '.join(option_names)
                else:
                    group_text = ' ODER '.join(option_names)
                
                # Add parentheses if more than one option
                if len(option_names) > 1:
                    group_text = f"({group_text})"
                
                group_texts.append(group_text)
        
        # Combine groups with global operator
        if group_texts:
            if self.global_operator == 'and':
                result = ' UND '.join(group_texts)
            else:
                result = ' ODER '.join(group_texts)
        else:
            result = ''
        
        # Add comment if present
        if self.comment:
            result = f"{result} - {self.comment}" if result else self.comment
        
        return result
    


class ModuleCertificateGroup(models.Model):
    """Certificate group assignment for a module with specific options and operator."""
    
    LOGIC_CHOICES = [
        ('and', 'UND'),
        ('or', 'ODER'),
    ]
    
    module_certificate = models.ForeignKey(ModuleCertificate, on_delete=models.CASCADE, related_name='certificate_groups')
    group = models.ForeignKey(CertificateGroup, on_delete=models.CASCADE)
    internal_operator = models.CharField(max_length=3, choices=LOGIC_CHOICES, default='or', help_text="How options within this group should be combined")
    selected_options = models.ManyToManyField(CertificateOption, blank=True, help_text="Selected options for this group")
    order = models.PositiveIntegerField(default=0, help_text="Display order within the certificate")
    
    class Meta:
        ordering = ['order', 'group__name']
        unique_together = ('module_certificate', 'group')
        verbose_name = "Module Certificate Group"
        verbose_name_plural = "Module Certificate Groups"
    
    def __str__(self):
        return f"{self.module_certificate.module.name} - {self.group.name}"


class CourseModule(models.Model):
    """Through model to handle course assignment and semester within modules."""
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    semester = models.PositiveIntegerField(help_text="Semester number (1, 2, 3, etc.)")
    order = models.PositiveIntegerField(default=0, help_text="Order of course within this module")

    class Meta:
        ordering = ['order']
        unique_together = ('module', 'course')

    def __str__(self):
        return f"{self.module.name} - {self.course.name} (semester: {self.semester}, order: {self.order})"


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
    
    # Sharing functionality
    is_shared = models.BooleanField(default=False, help_text="Whether this programme is shared with other users")
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_programmes_v2', null=True, blank=True, help_text="Original creator who shared this programme")
    shared_at = models.DateTimeField(null=True, blank=True, help_text="When this programme was shared")
    original_programme = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_copies', help_text="Reference to original programme if this is a shared copy")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_programme_type_display()})"

    def get_ordered_modules(self):
        """Get modules ordered by their position in this programme."""
        from django.db.models import Prefetch
        return self.modules.prefetch_related(
            Prefetch('courses', queryset=Course.objects.select_related().prefetch_related('lpo_relevance'))
        ).order_by('programmemodule__order')

    @property
    def total_ects(self):
        """Calculate total ECTS credits for this programme including nebenfach."""
        module_ects = sum(module.total_ects for module in self.modules.all())
        nebenfach_ects = sum(nf.ects for nf in self.nebenfach_ects.all())
        return module_ects + nebenfach_ects
    
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
        
        # Didaktik LPO courses
        didaktik_ects = all_courses.filter(
            lpo_relevance__name='didaktik'
        ).aggregate(total=Sum('ects'))['total'] or 0
        if didaktik_ects > 0:
            lpo_ects['didaktik'] = didaktik_ects
        
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
        """Get SWS range breakdown by course type.
        TODO: Use context-based semester association instead of course.semester.
        """
        course_type_sws = {}
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        for course_type_choice in CourseType.choices:
            course_type_key = course_type_choice[0]
            courses = all_courses.filter(course_type=course_type_key)
            if not courses.exists():
                continue
            total_min_sws = 0
            total_max_sws = 0
            for course in courses:
                min_students = 0
                max_students = 0
                if student_counts and course.max_participants:
                    import math
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    total_min_sws += course.sws * min_classes if min_classes > 0 else course.sws
                    total_max_sws += course.sws * max_classes if max_classes > 0 else course.sws
                else:
                    total_min_sws += course.sws
                    total_max_sws += course.sws
            if total_min_sws > 0 or total_max_sws > 0:
                if total_min_sws == total_max_sws:
                    course_type_sws[course_type_key] = total_min_sws
                else:
                    course_type_sws[course_type_key] = f"{total_min_sws}-{total_max_sws}"
        return course_type_sws
    
    def get_sws_range_by_discipline(self, student_counts=None):
        """Get SWS range breakdown by discipline.
        TODO: Use context-based semester association instead of course.semester.
        """
        discipline_sws = {}
        all_courses = Course.objects.filter(modules__programmes=self).distinct()
        for discipline_choice in Discipline.choices:
            discipline_key = discipline_choice[0]
            courses = all_courses.filter(discipline=discipline_key)
            if not courses.exists():
                continue
            total_min_sws = 0
            total_max_sws = 0
            for course in courses:
                min_students = 0
                max_students = 0
                if student_counts and course.max_participants:
                    import math
                    min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                    max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                    total_min_sws += course.sws * min_classes if min_classes > 0 else course.sws
                    total_max_sws += course.sws * max_classes if max_classes > 0 else course.sws
                else:
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
            return 9  # 4.5 years * 2 semesters
        else:
            return 6  # Default

    def to_json(self):
        """Export programme as JSON representation."""
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        # Build the programme data structure
        programme_data = {
            'name': self.name,
            'programme_type': self.programme_type,
            'programme_type_display': self.get_programme_type_display(),
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_ects': self.total_ects,
            'total_sws': self.total_sws,
            'total_courses': self.total_courses,
            'semester_count': self.get_semester_count(),
            'modules': [],
            'student_counts': [],
            'nebenfach_ects': []
        }
        
        # Add modules with their courses
        for programme_module in self.programmemodule_set.all().order_by('order'):
            module = programme_module.module
            module_data = {
                'name': module.name,
                'description': module.description,
                'qualification_goals': module.qualification_goals,
                'responsible_person': module.responsible_person,
                'certificate_display': module.get_certificate_display(),
                'order': programme_module.order,
                'total_ects': module.total_ects,
                'total_sws': module.total_sws,
                'courses': []
            }
            
            # Add new certificate system data if available
            try:
                module_cert = module.module_certificate
                certificate_config = {
                    'is_graded': module_cert.is_graded,
                    'comment': module_cert.comment,
                    'global_operator': module_cert.global_operator,
                    'global_operator_display': 'UND' if module_cert.global_operator == 'and' else 'ODER',
                    
                    # Legacy fields for backward compatibility
                    'logic_operator': module_cert.logic_operator,
                    'logic_operator_display': module_cert.get_logic_operator_display(),
                    'selected_options': [
                        {
                            'id': option.id,
                            'name': option.name,
                            'description': option.description,
                            'order': option.order
                        } for option in CertificateOption.objects.none()  # Legacy field removed
                    ]
                }
                
                # Add group structure if it exists (new system)
                if hasattr(module_cert, 'group_structure') and module_cert.group_structure:
                    certificate_config['group_structure'] = module_cert.group_structure
                    
                    # Expand group structure with option details for easier reading
                    if module_cert.group_structure.get('groups'):
                        expanded_groups = []
                        for group in module_cert.group_structure['groups']:
                            expanded_group = {
                                'internal_operator': group.get('internal_operator', 'or'),
                                'internal_operator_display': 'UND' if group.get('internal_operator') == 'and' else 'ODER',
                                'order': group.get('order', 0),
                                'options': []
                            }
                            
                            # Get full option details
                            option_ids = group.get('options', [])
                            if option_ids:
                                options = CertificateOption.objects.filter(id__in=option_ids).order_by('order')
                                for option in options:
                                    expanded_group['options'].append({
                                        'id': option.id,
                                        'name': option.name,
                                        'description': option.description,
                                        'order': option.order
                                    })
                            
                            expanded_groups.append(expanded_group)
                        
                        certificate_config['groups_expanded'] = expanded_groups
                
                module_data['certificate_config'] = certificate_config
                
            except ModuleCertificate.DoesNotExist:
                module_data['certificate_config'] = None
            
            # Add courses within this module
            for course_module in module.coursemodule_set.all().order_by('semester', 'order'):
                course = course_module.course
                course_data = {
                    'name': course.name,
                    'description': course.description,
                    'semester': course_module.semester,
                    'order': course_module.order,
                    'course_type': course.course_type,
                    'course_type_display': course.get_course_type_display(),
                    'discipline': course.discipline,
                    'discipline_display': course.get_discipline_display(),
                    'ects': course.ects,
                    'sws': course.sws,
                    'max_participants': course.max_participants,
                    'lpo_relevance': [lpo.name for lpo in course.lpo_relevance.all()]
                }
                module_data['courses'].append(course_data)
            
            programme_data['modules'].append(module_data)
        
        # Add student counts
        for student_count in self.student_counts.all().order_by('semester'):
            programme_data['student_counts'].append({
                'semester': student_count.semester,
                'min_students': student_count.min_students,
                'max_students': student_count.max_students
            })
        
        # Add nebenfach ECTS
        for nebenfach in self.nebenfach_ects.all().order_by('semester'):
            programme_data['nebenfach_ects'].append({
                'semester': nebenfach.semester,
                'ects': nebenfach.ects
            })
        
        return json.dumps(programme_data, cls=DjangoJSONEncoder, indent=2, ensure_ascii=False)


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


class ProgrammeNebenfach(models.Model):
    """Model for tracking ECTS in minor subjects (Nebenfach) per semester."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='nebenfach_ects')
    semester = models.PositiveIntegerField(help_text="Semester number (1, 2, 3, etc.)")
    ects = models.PositiveIntegerField(default=0, help_text="ECTS for minor subject in this semester")

    class Meta:
        unique_together = ('programme', 'semester')
        ordering = ['programme', 'semester']

    def __str__(self):
        return f"{self.programme.name} Sem {self.semester}: {self.ects} ECTS Nebenfach"


class DefaultStudentCount(models.Model):
    """Model for storing default student counts per programme type and semester."""
    programme_type = models.CharField(max_length=30, choices=ProgrammeType.choices)
    semester = models.PositiveIntegerField(help_text="Semester number (1, 2, 3, etc.)")
    min_students = models.PositiveIntegerField(default=20, help_text="Default minimum expected students")
    max_students = models.PositiveIntegerField(default=30, help_text="Default maximum expected students")
    
    class Meta:
        unique_together = ('programme_type', 'semester')
        ordering = ['programme_type', 'semester']
        verbose_name = "Default Student Count"
        verbose_name_plural = "Default Student Counts"

    def __str__(self):
        return f"{self.get_programme_type_display()} Sem {self.semester}: {self.min_students}-{self.max_students}"


class DefaultNebenfach(models.Model):
    """Model for storing default nebenfach ECTS per programme type and semester."""
    programme_type = models.CharField(max_length=30, choices=ProgrammeType.choices)
    semester = models.PositiveIntegerField(help_text="Semester number (1, 2, 3, etc.)")
    ects = models.PositiveIntegerField(default=0, help_text="Default ECTS for minor subject in this semester")
    
    class Meta:
        unique_together = ('programme_type', 'semester')
        ordering = ['programme_type', 'semester']
        verbose_name = "Default Nebenfach ECTS"
        verbose_name_plural = "Default Nebenfach ECTS"

    def __str__(self):
        return f"{self.get_programme_type_display()} Sem {self.semester}: {self.ects} ECTS Nebenfach"


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
        
        # Didaktik LPO courses
        didaktik_ects = all_courses.filter(
            lpo_relevance__name='didaktik'
        ).aggregate(total=Sum('ects'))['total'] or 0
        if didaktik_ects > 0:
            lpo_ects['didaktik'] = didaktik_ects
        
        return lpo_ects
    
    def get_aggregate_student_counts(self):
        """Get aggregated student counts across all programmes by semester."""
        from django.db.models import Max
        
        # Get all student counts from programmes in this revision
        # Use MAX instead of SUM because shared courses serve all programmes simultaneously
        student_counts = ProgrammeStudentCount.objects.filter(
            programme__revisions=self
        ).values('semester').annotate(
            total_min=Max('min_students'),
            total_max=Max('max_students')
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
    
    def _get_unique_course_semester_combinations(self):
        """Get unique course-semester combinations across all programmes in this revision."""
        from collections import defaultdict
        
        # Dictionary to track unique (course, semester) combinations
        # Key: (course_id, semester), Value: course object
        unique_combinations = {}
        
        # Iterate through all programmes in this revision
        for programme in self.programmes.all():
            for module in programme.modules.all():
                for course_module in module.coursemodule_set.all():
                    key = (course_module.course.id, course_module.semester)
                    unique_combinations[key] = course_module.course
        
        return unique_combinations

    def _get_unique_courses_for_semester(self, semester):
        """Get unique courses for a specific semester across all programmes in this revision."""
        unique_courses = {}
        for programme in self.programmes.all():
            for module in programme.modules.all():
                for course_module in module.coursemodule_set.filter(semester=semester):
                    unique_courses[course_module.course.id] = course_module.course
        return unique_courses
    
    def _get_student_range_for_course(self, course_id, semester):
        """Get min/max sum of students taking a course in a semester across revised programmes."""
        total_min_students = 0
        total_max_students = 0
        
        for programme in self.programmes.all():
            # Check if this programme has this course in this semester
            has_course = programme.modules.filter(
                coursemodule__course_id=course_id,
                coursemodule__semester=semester
            ).exists()
            
            if has_course:
                # Get this programme's student counts for this semester
                student_count = ProgrammeStudentCount.objects.filter(
                    programme=programme, 
                    semester=semester
                ).first()
                
                if student_count:
                    total_min_students += student_count.min_students
                    total_max_students += student_count.max_students
        
        return total_min_students, total_max_students
    
    def _compute_needed_classes(self, max_participants, min_students, max_students):
        """Compute min/max classes needed for a course given student counts."""
        import math
        
        if not max_participants or max_participants <= 0:
            return 1, 1  # No limit, runs once
        
        min_classes = math.ceil(min_students / max_participants) if min_students > 0 else 1
        max_classes = math.ceil(max_students / max_participants) if max_students > 0 else 1
        
        return min_classes, max_classes
    
    def _compute_sws_for_course(self, course, min_classes, max_classes):
        """Compute SWS range for a course given class counts."""
        course_sws = course.sws or 0
        sws_min = course_sws * min_classes
        sws_max = course_sws * max_classes
        return sws_min, sws_max

    def compute_sws(self):
        """Compute SWS following the clean algorithm: semester-by-semester iteration."""
        WS_min = 0
        WS_max = 0
        SS_min = 0 
        SS_max = 0
        
        # Iterate through semesters 1-10
        for semester in range(1, 11):
            # Get unique courses for this semester
            courses_semester = self._get_unique_courses_for_semester(semester)
            
            for course_id, course in courses_semester.items():
                # Get min/max sum of students taking this course in this semester
                min_students, max_students = self._get_student_range_for_course(course_id, semester)
                
                # Get max participants for this course
                max_participants = course.max_participants
                
                # Compute needed classes
                class_min, class_max = self._compute_needed_classes(max_participants, min_students, max_students)
                
                # Compute SWS
                sws_min, sws_max = self._compute_sws_for_course(course, class_min, class_max)
                
                # Add to appropriate semester (odd = WS, even = SS)
                if semester % 2 == 0:  # Even semester = SS
                    SS_min += sws_min
                    SS_max += sws_max
                else:  # Odd semester = WS
                    WS_min += sws_min
                    WS_max += sws_max
        
        return {
            'WS_min': WS_min, 'WS_max': WS_max,
            'SS_min': SS_min, 'SS_max': SS_max,
            'total_min': WS_min + SS_min,
            'total_max': WS_max + SS_max
        }

    def get_sws_range_total(self):
        """Get total SWS range across all programmes in this revision, accounting for shared courses."""
        sws_data = self.compute_sws()
        total_min = sws_data['total_min']
        total_max = sws_data['total_max']
        
        if total_min == total_max:
            return total_min
        else:
            return f"{total_min}-{total_max}"
    
    def get_sws_by_course_type(self):
        """Get SWS breakdown by course type across all programmes in this revision, accounting for shared courses."""
        from collections import defaultdict
        
        # Group by course type
        course_type_sws = defaultdict(lambda: {'min': 0, 'max': 0})
        
        # Iterate through semesters 1-10
        for semester in range(1, 11):
            courses_semester = self._get_unique_courses_for_semester(semester)
            
            for course_id, course in courses_semester.items():
                min_students, max_students = self._get_student_range_for_course(course_id, semester)
                class_min, class_max = self._compute_needed_classes(course.max_participants, min_students, max_students)
                sws_min, sws_max = self._compute_sws_for_course(course, class_min, class_max)
                
                course_type = course.course_type
                course_type_sws[course_type]['min'] += sws_min
                course_type_sws[course_type]['max'] += sws_max
        
        # Format results
        result = {}
        for course_type, sws_data in course_type_sws.items():
            min_sws = sws_data['min']
            max_sws = sws_data['max']
            if min_sws == max_sws:
                result[course_type] = min_sws
            else:
                result[course_type] = f"{min_sws}-{max_sws}"
        
        return result
    
    def get_sws_by_discipline(self):
        """Get SWS breakdown by discipline across all programmes in this revision, accounting for shared courses."""
        from collections import defaultdict
        
        # Group by discipline
        discipline_sws = defaultdict(lambda: {'min': 0, 'max': 0})
        
        # Iterate through semesters 1-10
        for semester in range(1, 11):
            courses_semester = self._get_unique_courses_for_semester(semester)
            
            for course_id, course in courses_semester.items():
                min_students, max_students = self._get_student_range_for_course(course_id, semester)
                class_min, class_max = self._compute_needed_classes(course.max_participants, min_students, max_students)
                sws_min, sws_max = self._compute_sws_for_course(course, class_min, class_max)
                
                discipline = course.discipline
                discipline_sws[discipline]['min'] += sws_min
                discipline_sws[discipline]['max'] += sws_max
        
        # Format results
        result = {}
        for discipline, sws_data in discipline_sws.items():
            min_sws = sws_data['min']
            max_sws = sws_data['max']
            if min_sws == max_sws:
                result[discipline] = min_sws
            else:
                result[discipline] = f"{min_sws}-{max_sws}"
        
        return result

    def get_sws_by_semester_and_type(self):
        """Get SWS breakdown by semester and course type, accounting for shared courses."""
        import math
        from collections import defaultdict
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        # Get unique course-semester combinations
        unique_combinations = self._get_unique_course_semester_combinations()
        
        # Structure: {semester: {course_type: {'min': X, 'max': Y}}}
        result = defaultdict(lambda: defaultdict(lambda: {'min': 0, 'max': 0}))
        
        # Calculate SWS for each unique course-semester combination
        for (course_id, semester), course in unique_combinations.items():
            # Get aggregated student counts for this semester
            semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
            min_students = semester_data['min_students']
            max_students = semester_data['max_students']
            
            course_sws = course.sws or 0
            course_type = course.course_type
            
            if course.max_participants and course_sws:
                # Calculate required classes based on aggregated student counts
                min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                
                # Add SWS for this course-semester combination
                result[semester][course_type]['min'] += course_sws * min_classes if min_classes > 0 else course_sws
                result[semester][course_type]['max'] += course_sws * max_classes if max_classes > 0 else course_sws
            else:
                # No participant limit, course runs once
                result[semester][course_type]['min'] += course_sws
                result[semester][course_type]['max'] += course_sws
        
        # Format results
        final_result = {}
        for semester, types_data in result.items():
            final_result[semester] = {}
            for course_type, sws_data in types_data.items():
                min_sws = sws_data['min']
                max_sws = sws_data['max']
                if min_sws == max_sws:
                    final_result[semester][course_type] = min_sws
                else:
                    final_result[semester][course_type] = f"{min_sws}-{max_sws}"
        
        return final_result

    def get_sws_by_semester_and_discipline(self):
        """Get SWS breakdown by semester and discipline, accounting for shared courses."""
        import math
        from collections import defaultdict
        
        # Get aggregate student counts
        student_counts_data = self.get_aggregate_student_counts()
        
        # Get unique course-semester combinations
        unique_combinations = self._get_unique_course_semester_combinations()
        
        # Structure: {semester: {discipline: {'min': X, 'max': Y}}}
        result = defaultdict(lambda: defaultdict(lambda: {'min': 0, 'max': 0}))
        
        # Calculate SWS for each unique course-semester combination
        for (course_id, semester), course in unique_combinations.items():
            # Get aggregated student counts for this semester
            semester_data = student_counts_data.get(semester, {'min_students': 0, 'max_students': 0})
            min_students = semester_data['min_students']
            max_students = semester_data['max_students']
            
            course_sws = course.sws or 0
            discipline = course.discipline
            
            if course.max_participants and course_sws:
                # Calculate required classes based on aggregated student counts
                min_classes = math.ceil(min_students / course.max_participants) if min_students > 0 else 0
                max_classes = math.ceil(max_students / course.max_participants) if max_students > 0 else 0
                
                # Add SWS for this course-semester combination
                result[semester][discipline]['min'] += course_sws * min_classes if min_classes > 0 else course_sws
                result[semester][discipline]['max'] += course_sws * max_classes if max_classes > 0 else course_sws
            else:
                # No participant limit, course runs once
                result[semester][discipline]['min'] += course_sws
                result[semester][discipline]['max'] += course_sws
        
        # Format results
        final_result = {}
        for semester, disciplines_data in result.items():
            final_result[semester] = {}
            for discipline, sws_data in disciplines_data.items():
                min_sws = sws_data['min']
                max_sws = sws_data['max']
                if min_sws == max_sws:
                    final_result[semester][discipline] = min_sws
                else:
                    final_result[semester][discipline] = f"{min_sws}-{max_sws}"
        
        return final_result

    def get_winter_summer_sws(self):
        """Get SWS breakdown by winter (odd) and summer (even) semesters with ranges."""
        sws_data = self.compute_sws()
        
        # Format winter SWS
        if sws_data['WS_min'] == sws_data['WS_max']:
            winter_sws = sws_data['WS_min']
        else:
            winter_sws = f"{sws_data['WS_min']}-{sws_data['WS_max']}"
            
        # Format summer SWS
        if sws_data['SS_min'] == sws_data['SS_max']:
            summer_sws = sws_data['SS_min']
        else:
            summer_sws = f"{sws_data['SS_min']}-{sws_data['SS_max']}"
        
        return {
            'winter_sws': winter_sws,
            'summer_sws': summer_sws
        }
