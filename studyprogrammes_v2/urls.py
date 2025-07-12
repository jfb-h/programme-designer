from django.urls import path
from django.shortcuts import redirect
from . import views
from . import auth_views

def redirect_to_programmes(request):
    """Redirect root V2 URL to programmes overview"""
    if request.user.is_authenticated:
        return redirect('v2_programme_overview')
    else:
        return redirect('v2_login')

urlpatterns = [
    # Root redirect
    path('', redirect_to_programmes, name='v2_home'),
    
    # Authentication URLs
    path('login/', auth_views.login_view, name='v2_login'),
    path('logout/', auth_views.logout_view, name='v2_logout'),
    
    # Overview pages
    path('courses/', views.course_overview, name='v2_course_overview'),
    path('modules/', views.module_overview, name='v2_module_overview'),
    path('programmes/', views.programme_overview, name='v2_programme_overview'),
    path('revisions/', views.revision_overview, name='v2_revision_overview'),
    
    # Detail/edit pages
    path('programmes/<int:programme_id>/edit/', views.programme_detail, name='v2_programme_detail'),
    path('programmes/<int:programme_id>/reorder-modules/', views.reorder_modules, name='v2_reorder_modules'),
    path('revisions/<int:revision_id>/', views.revision_detail, name='v2_revision_detail'),
    path('revisions/<int:revision_id>/edit/', views.edit_revision, name='v2_edit_revision'),
    path('revisions/<int:revision_id>/programme/<str:programme_type>/', views.edit_programme, name='v2_edit_programme'),
    
    # AJAX endpoints for revision programme management
    path('revisions/<int:revision_id>/available-programmes/<str:programme_type>/', views.get_available_programmes, name='v2_get_available_programmes'),
    path('revisions/<int:revision_id>/update-programme/', views.update_revision_programme, name='v2_update_revision_programme'),
    
    # Delete views
    path('courses/<int:course_id>/delete/', views.delete_course, name='v2_delete_course'),
    path('modules/<int:module_id>/delete/', views.delete_module, name='v2_delete_module'),
    path('programmes/<int:programme_id>/delete/', views.delete_programme, name='v2_delete_programme'),
    path('revisions/<int:revision_id>/delete/', views.delete_revision, name='v2_delete_revision'),
]