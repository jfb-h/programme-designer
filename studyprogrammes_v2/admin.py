from django.contrib import admin
from .models import (
    Course, Module, Programme, ProgrammeModule, ProgrammeStudentCount,
    ProgrammeType, DefaultStudentCount, DefaultNebenfach, Revision, CertificateOption, ModuleCertificate
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_type', 'ects', 'sws', 'discipline']
    list_filter = ['course_type', 'discipline']
    search_fields = ['name', 'description']

class ModuleCertificateInline(admin.StackedInline):
    model = ModuleCertificate
    extra = 0
    max_num = 1
    filter_horizontal = ['selected_options']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_ects', 'total_sws', 'get_certificate_display']
    search_fields = ['name', 'description']
    inlines = [ModuleCertificateInline]

class ProgrammeModuleInline(admin.TabularInline):
    model = ProgrammeModule
    extra = 1
    autocomplete_fields = ['module']

class ProgrammeStudentCountInline(admin.TabularInline):
    model = ProgrammeStudentCount
    extra = 0
    fields = ['semester', 'min_students', 'max_students']
    
@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['name', 'programme_type', 'total_ects', 'total_sws', 'total_courses']
    list_filter = ['programme_type']
    search_fields = ['name', 'comment']
    inlines = [ProgrammeModuleInline, ProgrammeStudentCountInline]

@admin.register(ProgrammeStudentCount)
class ProgrammeStudentCountAdmin(admin.ModelAdmin):
    list_display = ['programme', 'semester', 'min_students', 'max_students']
    list_filter = ['programme', 'semester']
    search_fields = ['programme__name']


@admin.register(DefaultStudentCount)
class DefaultStudentCountAdmin(admin.ModelAdmin):
    list_display = ['programme_type', 'semester', 'min_students', 'max_students']
    list_filter = ['programme_type', 'semester']
    ordering = ['programme_type', 'semester']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'programme_type' in form.base_fields:
            form.base_fields['programme_type'].help_text = "Select the programme type for these default student counts"
        return form


@admin.register(DefaultNebenfach)
class DefaultNebenfachAdmin(admin.ModelAdmin):
    list_display = ['programme_type', 'semester', 'ects']
    list_filter = ['programme_type', 'semester']
    list_editable = ['ects']
    ordering = ['programme_type', 'semester']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'programme_type' in form.base_fields:
            form.base_fields['programme_type'].help_text = "Select the programme type for these default nebenfach ECTS"
        if 'semester' in form.base_fields:
            form.base_fields['semester'].help_text = "Semester number (1-10 depending on programme type)"
        if 'ects' in form.base_fields:
            form.base_fields['ects'].help_text = "ECTS credits for minor subject (Nebenfach) in this semester"
        return form


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'author', 'date', 'programme_count']
    list_filter = ['author', 'date']
    search_fields = ['name']
    filter_horizontal = ['programmes']
    ordering = ['-date', '-order']
    
    def programme_count(self, obj):
        return obj.programmes.count()
    programme_count.short_description = 'Programme Count'


@admin.register(CertificateOption)
class CertificateOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'description']
    list_editable = ['order']
    ordering = ['order', 'name']
    search_fields = ['name', 'description']


@admin.register(ModuleCertificate)
class ModuleCertificateAdmin(admin.ModelAdmin):
    list_display = ['module', 'logic_operator', 'get_selected_options', 'comment']
    list_filter = ['logic_operator']
    search_fields = ['module__name', 'comment']
    filter_horizontal = ['selected_options']
    
    def get_selected_options(self, obj):
        return ', '.join([opt.name for opt in obj.selected_options.all()])
    get_selected_options.short_description = 'Selected Options'
