from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.course_overview, name='v2_course_overview'),
    path('revisions/', views.revision_overview, name='v2_revision_overview'),
    path('revisions/<int:revision_id>/edit/', views.edit_revision, name='v2_edit_revision'),
    path('revisions/<int:revision_id>/programme/<str:degree_type>/', views.edit_programme, name='v2_edit_programme'),
]