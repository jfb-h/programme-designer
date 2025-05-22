from django import forms
from django.core.validators import MinValueValidator

from studyprogrammes.models import LogMessage
from .models import Course, Programme, Semester

DEFAULTS = {
    'seminar': {'ects': 3, 'sws': 2, 'max_participants': 30},
    'lecture': {'ects': 3, 'sws': 2, 'max_participants': 600},
    # Add more as needed
}

class LogMessageForm(forms.ModelForm):
    class Meta:
        model = LogMessage
        fields = ("message",)

class CourseForm(forms.ModelForm):
    group = forms.ChoiceField(
        choices=Course.GROUP_CHOICES,
        widget=forms.RadioSelect(attrs={'style': 'display:flex; gap:1em;'}),
        label="Gruppe"
    )
    class Meta:
        model = Course
        fields = [
            "name",
            "group",
            "ects",
            "sws",
            "type",
            "max_participants",
            "semester",
            "description",
        ]
        labels = {
            "name": "Kursname",
            "group": "Gruppe",
            "ects": "ECTS",
            "sws": "SWS",
            "type": "Typ",
            "max_participants": "Maximale Teilnehmer",
            "semester": "Semester",
            "description": "Beschreibung",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for new forms
        if not self.is_bound:
            course_type = self.initial.get('type', 'seminar')
            defaults = DEFAULTS.get(course_type, {})
            for field, value in defaults.items():
                self.fields[field].initial = value

class ProgrammeForm(forms.ModelForm):
    class Meta:
        model = Programme
        fields = ["name", "degree_type"]
        labels = {
            "name": "Name",
            "degree_type": "Abschlussart",
        }

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['programme']
        labels = {
            "programme": "Studiengang",
        }

# Forms for studyprogrammes app (formerly 'static/studyprogrammes')
