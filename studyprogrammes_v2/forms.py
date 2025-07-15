from django import forms
from .models import Course, Module, Programme, Revision, CourseType, Discipline, LPO, LPOCategory, ProgrammeType, CertificateOption, ModuleCertificate


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'name', 'description', 'course_type', 
            'discipline', 'lpo_relevance', 'ects', 'sws', 'max_participants'
        ]
        labels = {
            'name': 'Kursname',
            'description': 'Beschreibung',
            'course_type': 'Typ',
            'discipline': 'Fachrichtung',
            'lpo_relevance': 'LPO-Relevanz',
            'ects': 'ECTS',
            'sws': 'SWS',
            'max_participants': 'Maximale Teilnehmer',
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors'
            }),
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors',
                'placeholder': 'z.B. Grundlagen Humangeographie I'
            }),
            'course_type': forms.RadioSelect(attrs={
                'class': 'flex flex-wrap gap-4'
            }),
            'discipline': forms.RadioSelect(attrs={
                'class': 'flex flex-wrap gap-4'
            }),
            'lpo_relevance': forms.CheckboxSelectMultiple(attrs={
                'class': 'flex flex-wrap gap-4'
            }),
            'ects': forms.NumberInput(attrs={
                'min': 1, 'max': 30,
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors'
            }),
            'sws': forms.NumberInput(attrs={
                'min': 1, 'max': 10,
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors'
            }),
            'max_participants': forms.NumberInput(attrs={
                'min': 1,
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors',
                'placeholder': ''
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the empty choice option for radio buttons by setting choices directly
        self.fields['course_type'].choices = CourseType.choices
        self.fields['discipline'].choices = Discipline.choices
        
        # Ensure LPO categories exist and set up the queryset
        for value, label in LPO.choices:
            LPOCategory.objects.get_or_create(name=value)
        
        # Set the queryset for LPO relevance field
        self.fields['lpo_relevance'].queryset = LPOCategory.objects.all()


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['order', 'name', 'description', 'certificate', 'courses']
        labels = {
            'order': 'Reihenfolge',
            'name': 'Modulname',
            'description': 'Beschreibung',
            'certificate': 'Leistungsnachweis',
            'courses': 'Kurse',
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'certificate': forms.Textarea(attrs={
                'rows': 2,
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'order': forms.NumberInput(attrs={
                'min': 0,
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'courses': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order courses by semester then by name
        self.fields['courses'].queryset = Course.objects.all().order_by('semester', 'name')


class ModuleCertificateForm(forms.ModelForm):
    """Form for handling module certificate configuration with selection and logic operator."""
    
    class Meta:
        model = ModuleCertificate
        fields = ['selected_options', 'logic_operator', 'comment', 'is_graded']
        labels = {
            'selected_options': 'Leistungsnachweis-Optionen',
            'logic_operator': 'Verknüpfung',
            'comment': 'Zusätzliche Angaben',
            'is_graded': 'Benotet',
        }
        widgets = {
            'selected_options': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
            'logic_operator': forms.RadioSelect(attrs={
                'class': 'flex gap-4'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 2,
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Zusätzliche Details zum Leistungsnachweis...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order certificate options by their order field
        self.fields['selected_options'].queryset = CertificateOption.objects.all().order_by('order', 'name')
        
        # Set help text for logic operator
        self.fields['logic_operator'].help_text = 'Wählen Sie, ob die ausgewählten Optionen mit UND oder ODER verknüpft werden sollen.'


class ProgrammeForm(forms.ModelForm):
    class Meta:
        model = Programme
        fields = ['name', 'comment', 'programme_type']
        labels = {
            'name': 'Studiengangsname',
            'comment': 'Kommentar',
            'programme_type': 'Studiengangstyp',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors',
                'placeholder': 'z.B. Geographie Bachelor 100'
            }),
            'programme_type': forms.RadioSelect(attrs={
                'class': 'flex flex-wrap gap-4'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'block w-full rounded-lg border-gray-400 shadow-sm focus:border-primary-500 focus:ring-primary-500 focus:ring-1 transition-colors',
                'placeholder': 'Notizen oder Kommentare'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make programme_type required and remove empty choice
        self.fields['programme_type'].required = True
        self.fields['programme_type'].choices = [choice for choice in self.fields['programme_type'].choices if choice[0] != '']


class RevisionForm(forms.ModelForm):
    class Meta:
        model = Revision
        fields = ['name', 'programmes']
        labels = {
            'name': 'Name der Revision',
            'programmes': 'Studiengänge',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'programmes': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow selection of both private and shared programmes
        user = kwargs.get('initial', {}).get('user')
        if user:
            self.fields['programmes'].queryset = Programme.objects.filter(
                models.Q(user=user) | models.Q(is_shared=True)
            ).order_by('name')
        else:
            self.fields['programmes'].queryset = Programme.objects.all().order_by('name')


# Additional form for quick course creation in modules
class QuickCourseForm(forms.ModelForm):
    """Simplified form for quick course creation when building modules."""
    class Meta:
        model = Course
        fields = ['name', 'course_type', 'discipline', 'ects', 'sws']
        labels = {
            'name': 'Kursname',
            'course_type': 'Typ',
            'discipline': 'Fachrichtung',
            'ects': 'ECTS',
            'sws': 'SWS',
        }
        widgets = {
            'ects': forms.NumberInput(attrs={'min': 1, 'max': 30}),
            'sws': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }


# Filter forms for overview pages
class CourseFilterForm(forms.Form):
    course_type = forms.ChoiceField(
        choices=[('', 'Alle Typen')] + CourseType.choices,
        required=False,
        label='Typ'
    )
    discipline = forms.ChoiceField(
        choices=[('', 'Alle Fachrichtungen')] + Discipline.choices,
        required=False,
        label='Fachrichtung'
    )
    semester = forms.IntegerField(
        required=False,
        label='Semester',
        widget=forms.NumberInput(attrs={'min': 1, 'max': 12})
    )


class ModuleFilterForm(forms.Form):
    min_ects = forms.IntegerField(
        required=False,
        label='Min. ECTS',
        widget=forms.NumberInput(attrs={'min': 0})
    )
    max_ects = forms.IntegerField(
        required=False,
        label='Max. ECTS',
        widget=forms.NumberInput(attrs={'min': 0})
    )
