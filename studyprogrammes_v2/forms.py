from django import forms
from .models import Course, Revision, Programme, Module

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'name', 'description', 'type', 'discipline', 'ects', 'sws', 'max_participants'
        ]
        labels = {
            'name': 'Kursname',
            'description': 'Beschreibung',
            'type': 'Typ',
            'discipline': 'Fachrichtung',
            'ects': 'ECTS',
            'sws': 'SWS',
            'max_participants': 'Maximale Teilnehmer',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class RevisionForm(forms.ModelForm):
    class Meta:
        model = Revision
        fields = ['name']
        labels = {'name': 'Name der Revision'}

class ProgrammeForm(forms.ModelForm):
    class Meta:
        model = Programme
        fields = ['name']

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['name', 'description']

class ModuleCourseForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label="Kurs")
    semester = forms.IntegerField(min_value=1, max_value=12, label="Semester")