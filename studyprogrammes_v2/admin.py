from django.contrib import admin
from .models import (
    Course, Module, Programme, ProgrammeModule, ProgrammeStudentCount,
    ProgrammeType, DefaultStudentCount, Revision
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_type', 'ects', 'sws', 'discipline']
    list_filter = ['course_type', 'discipline']
    search_fields = ['name', 'description']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_ects', 'total_sws']
    search_fields = ['name', 'description']

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
