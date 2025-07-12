from django.contrib import admin
from .models import (
    Course, Module, Programme, ProgrammeModule, ProgrammeStudentCount,
    ProgrammeType
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
