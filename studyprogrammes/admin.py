# Admin for studyprogrammes app (formerly 'static/studyprogrammes')

from django.contrib import admin
from .models import Semester, Course, Programme

admin.site.register(Semester)
admin.site.register(Course)
admin.site.register(Programme)
