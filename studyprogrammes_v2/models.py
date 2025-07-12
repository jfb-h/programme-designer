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
    MASTER_HG = 'master_hg', 'Master Phys Geo'
    MASTER_PG = 'master_pg', 'Master Humangeo'


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
    
    # Additional fields for practical course management
    ects = models.PositiveIntegerField(default=6, help_text="ECTS")
    sws = models.PositiveIntegerField(default=2, help_text="Semesterwochenstunden")
    max_participants = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Module(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Display order within programme")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
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
    modules = models.ManyToManyField(Module, through='ProgrammeModule', related_name='programmes', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_programme_type_display()})"

    def get_ordered_modules(self):
        """Get modules ordered by their position in this programme."""
        return self.modules.order_by('programmemodule__order')

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

    def get_semester_count(self):
        """Get the number of semesters for this programme type."""
        bachelor_types = ['bachelor_100', 'bachelor_60', 'bachelor_30']
        master_types = ['master_hg', 'master_pg']
        lehramt_types = ['lehramt_vertieft', 'lehramt_nicht_vertieft']
        
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
    """A revision corresponding to Julia struct Revision."""
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
