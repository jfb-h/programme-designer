from django.db import models
from django.conf import settings

class LogMessage(models.Model):
    message = models.CharField(max_length=300)
    log_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message} ({self.log_date})"

class Programme(models.Model):
    DEGREE_CHOICES = [
        ('bachelor', "Bachelor"),
        ('master', "Master"),
        ('teaching', "Staatsexamen"),
    ]
    SCHOOL_CHOICES = [
        ("none", "Keine (BA oder MA)"),
        ("elementary", "Grund-/Mittel-/Realschule"),
        ("high", "Gymnasium"),
        ("didactic", "Didaktikfach"),
    ]
    name = models.CharField(max_length=200)
    degree_type = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    school_type = models.CharField(max_length=40, choices=SCHOOL_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='programmes', null=True, blank=True)
    is_public = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, db_index=True)
    def __str__(self):
        if self.degree_type == 'teaching':
            school_type_str = ": "+self.school_type
        else:
            school_type_str = ""
        return f"{self.name} ({self.degree_type}{school_type_str})"

class Semester(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='semesters')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.order + 1}. Semester"

class Course(models.Model):
    TYPE_CHOICES = [
        ('lecture', 'VL (Vorlesung)'),
        ('seminar', 'S (Seminar)'),
        ('tutorial', 'Ü (Übung)'),
        ('fieldtrip', 'G (Exkursion)'),
        ('thesis', 'T (Thesis)'),
        ('external', 'E (Extern)'),
    ]
    GROUP_CHOICES = [
        ('PG', 'PG'),
        ('HG', 'HG'),
        ('WÜ', 'WÜ'),
        ('MA', 'MA'),
        ('RG', 'RG'),
        ('DI', 'DI'),
        ('EX', 'EX'),
    ]
    name = models.CharField(max_length=200)
    ects = models.PositiveIntegerField()
    sws = models.DecimalField(max_digits=3, decimal_places=1)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    max_participants = models.PositiveIntegerField()
    group = models.CharField(max_length=24, choices=GROUP_CHOICES)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.semester})"

class ProgrammeExpectedStudents(models.Model):
    DEGREE_CHOICES = Programme.DEGREE_CHOICES
    semester = models.PositiveIntegerField()
    degree_type = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    min_students = models.PositiveIntegerField()
    max_students = models.PositiveIntegerField()

    class Meta:
        unique_together = ('semester', 'degree_type')
        ordering = ['degree_type', 'semester']

    def __str__(self):
        return f"{self.degree_type} Sem {self.semester}: {self.min_students}/{self.max_students}"

