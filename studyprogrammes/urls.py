from django.contrib.auth.decorators import login_required
from django.urls import path
from studyprogrammes import views

urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("about/", views.about, name="about"),
    path("log/", views.log_message, name="log"),
    path("programmes/", login_required(views.programmes_view), name="programmes"),
    path("programme/<int:pk>/", login_required(views.programme_view), name="programme"),
    path("programme/<int:programme_id>/update_semester_order/", login_required(views.update_semester_order), name="update_semester_order"),
    path("programme/<int:programme_id>/update_course_order/", login_required(views.update_course_order), name="update_course_order"),
    path('api/course/<int:course_id>/', login_required(views.course_detail_api), name='course_detail_api'),
]
