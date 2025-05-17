import re
from django.utils.timezone import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from studyprogrammes.forms import LogMessageForm, CourseForm, ProgrammeForm, SemesterForm
from studyprogrammes.models import LogMessage, Semester, Course, Programme
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.db.models import Prefetch
from django.db import models


class HomeListView(ListView):
    """Renders the home page, with a list of all messages."""
    model = LogMessage

    def get_context_data(self, **kwargs):
        context = super(HomeListView, self).get_context_data(**kwargs)
        return context

def about(request):
    return render(request, "studyprogrammes/about.html")


def log_message(request):
    form = LogMessageForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            message = form.save(commit=False)
            message.log_date = datetime.now()
            message.save()
            return redirect("home")
    else:
        return render(request, "studyprogrammes/log_message.html", {"form": form})

def programme_view(request, programme_id):
    programme = Programme.objects.get(pk=programme_id)
    semesters = Semester.objects.filter(programme=programme).prefetch_related(
        Prefetch('courses', queryset=Course.objects.order_by('order', 'id'))
    ).order_by('order', 'id')
    course_form = CourseForm(request.POST or None)
    semester_form = SemesterForm(initial={'programme': programme})
    if request.method == "POST":
        if 'add_course' in request.POST:
            post_data = request.POST.copy()
            if 'type' in post_data:
                post_data['type'] = post_data['type']
            course_form = CourseForm(post_data)
            if course_form.is_valid():
                course = course_form.save(commit=False)
                # Set order to max+1 for the semester
                max_order = Course.objects.filter(semester=course.semester).aggregate(max_order=models.Max('order'))['max_order']
                course.order = (max_order + 1) if max_order is not None else 0
                course.save()
                return redirect('programme', programme_id=programme_id)
        elif 'add_semester' in request.POST:
            semester_form = SemesterForm(request.POST)
            if semester_form.is_valid():
                semester_form.save()
                return redirect('programme', programme_id=programme_id)
        elif 'delete_semester' in request.POST:
            semester_id = request.POST.get('delete_semester_id')
            Semester.objects.filter(id=semester_id, programme=programme).delete()
            return redirect('programme', programme_id=programme_id)
        elif 'delete_course' in request.POST:
            course_id = request.POST.get('delete_course_id')
            Course.objects.filter(id=course_id, semester__programme=programme).delete()
            return redirect('programme', programme_id=programme_id)
    return render(request, "studyprogrammes/programme.html", {
        "programme": programme,
        "semesters": semesters,
        "course_form": course_form,
        "semester_form": semester_form,
    })

def programmes_view(request):
    programmes = Programme.objects.all()
    form = ProgrammeForm(request.POST or None)
    if request.method == "POST":
        if "delete_programme" in request.POST:
            programme_id = request.POST.get("delete_programme_id")
            Programme.objects.filter(id=programme_id).delete()
            return redirect('programmes')
        elif form.is_valid():
            form.save()
            return redirect('programmes')
    return render(request, "studyprogrammes/programmes.html", {
        "programmes": programmes,
        "programme_form": form,
    })

def home_redirect(request):
    return redirect('programmes')

def update_semester_order(request, programme_id):
    if request.method == "POST":
        data = json.loads(request.body)
        order = data.get("order", [])
        for idx, semester_id in enumerate(order):
            Semester.objects.filter(id=semester_id, programme_id=programme_id).update(order=idx)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
@require_POST
def update_course_order(request, programme_id):
    data = json.loads(request.body)
    semester_id = data.get('semester')
    order = data.get('order', [])
    if not semester_id or not order:
        return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)
    from .models import Course, Semester
    try:
        semester = Semester.objects.get(id=semester_id, programme_id=programme_id)
    except Semester.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Semester not found'}, status=404)
    # Update order for each course
    for idx, course_id in enumerate(order):
        Course.objects.filter(id=course_id, semester=semester).update(order=idx)
    return JsonResponse({'status': 'ok'})
