from django.conf import settings
from django.db import models

class Revision(models.Model):
    """A revision groups a set of programmes and their structure."""
    name = models.CharField(max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='revisions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.author})"

class Programme(models.Model):
    """A programme within a revision."""
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE, related_name='programmes')
    name = models.CharField(max_length=200)
    degree_type = models.CharField(max_length=20, choices=[
        ('bachelor100', "Bachelor 100"),
        ('bachelor60', "Bachelor 60"),
        ('bachelor30', "Bachelor 30"),
        ('teaching_vert', "Lehramt Vertieft"),
        ('teaching_nvert', "Lehramt nicht Vertieft"),
        ('teaching_gs', "Lehramt Grundschule"),
        ('teaching_ms', "Lehramt Mittelschule"),
        ('master_pg', "Master Phys Geo"),
        ('master_hg', "Master Humangeo"),
    ])

    def __str__(self):
        return f"{self.name} ({self.degree_type})"

class Module(models.Model):
    """A module within a programme."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    certificate = models.TextField(blank=True)
    # The associated list of courses is managed via ModuleCourse

    def __str__(self):
        return self.name

    @property
    def courses(self):
        """Return the courses associated with this module."""
        return [mc.course for mc in self.module_courses.all()]

class Course(models.Model):
    """A course in the global pool, reusable in many modules/programmes."""
    TYPE_CHOICES = [
        ('lecture', 'Vorlesung'),
        ('seminar', 'Seminar'),
        ('exercise', 'Übung'),
        ('fieldtrip', 'Exkursion'),
        ('thesis', 'Abschlussarbeit'),
        ('other', 'Sonstiges'),
    ]
    DISCIPLINE_CHOICES = [
        ('human', 'Humangeographie'),
        ('physical', 'Physische Geographie'),
        ('methods', 'Methoden'),
        ('variable', 'Übergreifend'),
        ('external', 'Extern'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ects = models.PositiveIntegerField()
    sws = models.PositiveIntegerField()
    max_participants = models.PositiveIntegerField()
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    discipline = models.CharField(max_length=16, choices=DISCIPLINE_CHOICES)

    def __str__(self):
        return self.name

class ModuleCourse(models.Model):
    """A through model to assign courses from the pool to modules, with semester info."""
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='module_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='module_courses')
    semester = models.PositiveIntegerField()  # The semester in which this course is taken
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('module', 'course', 'semester')
        ordering = ['semester', 'order']

    def __str__(self):
        return f"{self.module} - {self.course} (Semester {self.semester})"
