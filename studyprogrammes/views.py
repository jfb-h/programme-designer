import re
from django.utils.timezone import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from studyprogrammes.forms import LogMessageForm, CourseForm, ProgrammeForm, SemesterForm
from studyprogrammes.models import LogMessage, Semester, Course, Programme
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.db.models import Prefetch, Sum
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

def programme_view(request, pk):
    programme = get_object_or_404(Programme, pk=pk)
    semesters = Semester.objects.filter(programme=programme).prefetch_related(
        Prefetch('courses', queryset=Course.objects.order_by('order', 'id'))
    ).order_by('order', 'id')
    # Define course type groups for template
    course_type_groups = [
        ('lectures', 'Lectures'),
        ('seminars_tutorials', 'Seminars & Tutorials'),
        ('fieldtrips_thesis_external', 'Other'),
    ]
    from .models import ProgrammeExpectedStudents
    expected_students_lookup = {}
    for es in ProgrammeExpectedStudents.objects.filter(degree_type=programme.degree_type):
        expected_students_lookup[es.semester] = {'min': es.min_students, 'max': es.max_students}
    # Build a list of semester dicts with grouped courses and ects_sum
    semester_contexts = []
    total_ects = 0
    total_sws_min = 0
    total_sws_max = 0
    for idx, semester in enumerate(semesters, 1):
        courses = list(getattr(semester, 'courses').all())
        ects_sum = sum(c.ects for c in courses)
        courses_by_type = {
            'lectures': [],
            'seminars_tutorials': [],
            'fieldtrips_thesis_external': [],
        }
        expected_students = expected_students_lookup.get(idx, {'min': '', 'max': ''})
        expected_sws_min = 0
        expected_sws_max = 0
        for c in courses:
            min_classes = max_classes = None
            if expected_students['min'] and expected_students['max'] and c.max_participants:
                try:
                    min_val = int(expected_students['min'])
                    max_val = int(expected_students['max'])
                    maxp = int(c.max_participants)
                    min_classes = (min_val + maxp - 1) // maxp if min_val > 0 else 1
                    max_classes = (max_val + maxp - 1) // maxp if max_val > 0 else 1
                except Exception:
                    min_classes = max_classes = None
            c.min_classes = min_classes
            c.max_classes = max_classes
            if min_classes and c.sws:
                try:
                    expected_sws_min += min_classes * float(c.sws)
                except Exception:
                    pass
            if max_classes and c.sws:
                try:
                    expected_sws_max += max_classes * float(c.sws)
                except Exception:
                    pass
            if c.type == 'lecture':
                courses_by_type['lectures'].append(c)
            elif c.type in ('seminar', 'tutorial'):
                courses_by_type['seminars_tutorials'].append(c)
            elif c.type in ('fieldtrip', 'thesis', 'external'):
                courses_by_type['fieldtrips_thesis_external'].append(c)
        semester_contexts.append({
            'id': semester.pk,
            'order': getattr(semester, 'order', idx-1),
            'ects_sum': ects_sum,
            'courses_by_type': courses_by_type,
            'number': idx,
            'expected_students': expected_students,
            'expected_sws_min': expected_sws_min,
            'expected_sws_max': expected_sws_max,
        })
        total_ects += ects_sum
        total_sws_min += expected_sws_min
        total_sws_max += expected_sws_max
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
                return redirect('programme', pk=programme.pk)
        elif 'add_semester' in request.POST:
            semester_form = SemesterForm(request.POST)
            if semester_form.is_valid():
                semester_form.save()
                return redirect('programme', pk=programme.pk)
        elif 'delete_semester' in request.POST:
            semester_id = request.POST.get('delete_semester_id')
            Semester.objects.filter(id=semester_id, programme=programme).delete()
            return redirect('programme', pk=programme.pk)
        elif 'delete_course' in request.POST:
            course_id = request.POST.get('delete_course_id')
            Course.objects.filter(id=course_id, semester__programme=programme).delete()
            return redirect('programme', pk=programme.pk)
        elif "edit_programme" in request.POST:
            new_name = request.POST.get("programme_name", "").strip()
            if new_name:
                programme.name = new_name
                programme.save()
            # Optionally, redirect to avoid resubmission
            return redirect(request.path)
    return render(request, "studyprogrammes/programme.html", {
        "programme": programme,
        "semesters": semester_contexts,
        "course_form": course_form,
        "semester_form": semester_form,
        "course_type_groups": course_type_groups,
        "total_ects": total_ects,
        "total_sws_min": total_sws_min,
        "total_sws_max": total_sws_max,
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
    if not semester_id:
        return JsonResponse({'status': 'error', 'message': 'Missing semester id'}, status=400)
    from .models import Course, Semester
    try:
        semester = Semester.objects.get(id=semester_id, programme_id=programme_id)
    except Semester.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Semester not found'}, status=404)
    # Update order for each course
    for idx, course_id in enumerate(order):
        Course.objects.filter(id=course_id, semester=semester).update(order=idx)
    return JsonResponse({'status': 'ok'})
