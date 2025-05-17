from django.db import models
from django.utils import timezone

class LogMessage(models.Model):
    message = models.CharField(max_length=300)
    log_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message} ({self.log_date})"

class Programme(models.Model):
    DEGREE_CHOICES = [
        ('bachelor', "Bachelor"),
        ('master', "Master"),
        ('teaching', "Lehramt"),
    ]
    name = models.CharField(max_length=200)
    degree_type = models.CharField(max_length=20, choices=DEGREE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.get_degree_type_display()})"

class Semester(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='semesters')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.order + 1}. Semester"

class Course(models.Model):
    TYPE_CHOICES = [
        ('lecture', 'Lecture'),
        ('seminar', 'Seminar'),
        ('tutorial', 'Tutorial'),
        ('fieldtrip', 'Field Trip'),
        ('thesis', 'Thesis'),
        ('external', 'External'),
    ]
    GROUP_CHOICES = [
        ('PG', 'PG'),
        ('HG', 'HG'),
        ('MU', 'MÜ'),
    ]
    name = models.CharField(max_length=200)
    ects = models.IntegerField()
    sws = models.DecimalField(max_digits=3, decimal_places=1)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    max_participants = models.PositiveIntegerField()
    group = models.CharField(max_length=24, choices=GROUP_CHOICES)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.semester})"
