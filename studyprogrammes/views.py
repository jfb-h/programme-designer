import re
from django.utils.timezone import datetime
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from studyprogrammes.forms import LogMessageForm, CourseForm, ProgrammeForm, SemesterForm
from studyprogrammes.models import LogMessage, Semester, Course, Programme
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.db.models import Prefetch, Sum
from django.db import models
from django.contrib.auth.views import LogoutView as DjangoLogoutView


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

from django.shortcuts import get_object_or_404, redirect
from .models import Course

def programme_view(request, pk):
    programme = get_object_or_404(Programme, pk=pk)
    semesters = Semester.objects.filter(programme=programme).prefetch_related(
        Prefetch('courses', queryset=Course.objects.order_by('order', 'id'))
    ).order_by('order', 'id')
    # Define course type groups for template
    course_type_groups = [
        ('lectures', 'Vorlesungen'),
        ('seminars_tutorials', 'Seminare & Übungen'),
        ('fieldtrips_thesis_external', 'Sonstige'),
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
    # Calculate ECTS for all, winter (odd), and summer (even) semesters
    ects_winter = 0
    ects_summer = 0
    sws_odd_min = 0
    sws_odd_max = 0
    sws_even_min = 0
    sws_even_max = 0
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
        if idx % 2 == 1:
            ects_winter += ects_sum
            sws_odd_min += expected_sws_min
            sws_odd_max += expected_sws_max
        else:
            ects_summer += ects_sum
            sws_even_min += expected_sws_min
            sws_even_max += expected_sws_max
    course_form = CourseForm(request.POST or None)
    semester_form = SemesterForm(initial={'programme': programme})
    if request.method == "POST":
        if "add_course" in request.POST:
            edit_course_id = request.POST.get("edit_course_id")
            if edit_course_id:
                # Edit existing course
                course = get_object_or_404(Course, pk=edit_course_id)
                form = CourseForm(request.POST, instance=course)
                if form.is_valid():
                    form.save()
                    return redirect(request.path)
            else:
                # Add new course
                form = CourseForm(request.POST)
                if form.is_valid():
                    form.save()
                    return redirect(request.path)
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
    # Compute SWS group stats for detail view (lectures, seminars/tutorials, other)
    sws_groups_min = {'lectures': 0.0, 'seminars_tutorials': 0.0, 'other': 0.0}
    sws_groups_max = {'lectures': 0.0, 'seminars_tutorials': 0.0, 'other': 0.0}
    for sem in semester_contexts:
        # For each semester, group SWS by type
        for group, courses in sem['courses_by_type'].items():
            group_key = 'other'
            if group == 'lectures':
                group_key = 'lectures'
            elif group == 'seminars_tutorials':
                group_key = 'seminars_tutorials'
            # For each course, use min_classes/max_classes and sws
            for c in courses:
                if hasattr(c, 'min_classes') and c.min_classes and c.sws:
                    try:
                        sws_groups_min[group_key] += c.min_classes * float(c.sws)
                    except Exception:
                        pass
                if hasattr(c, 'max_classes') and c.max_classes and c.sws:
                    try:
                        sws_groups_max[group_key] += c.max_classes * float(c.sws)
                    except Exception:
                        pass
    context = {
        "programme": programme,
        "semesters": semester_contexts,
        "course_form": course_form,
        "semester_form": semester_form,
        "course_type_groups": course_type_groups,
        'total_ects': total_ects,
        'total_sws_min': total_sws_min,
        'total_sws_max': total_sws_max,
        'ects_winter': ects_winter,
        'ects_summer': ects_summer,
        'sws_odd_min': sws_odd_min,
        'sws_odd_max': sws_odd_max,
        'sws_even_min': sws_even_min,
        'sws_even_max': sws_even_max,
        'sws_lectures_min': sws_groups_min['lectures'],
        'sws_lectures_max': sws_groups_max['lectures'],
        'sws_seminars_min': sws_groups_min['seminars_tutorials'],
        'sws_seminars_max': sws_groups_max['seminars_tutorials'],
        'sws_other_min': sws_groups_min['other'],
        'sws_other_max': sws_groups_max['other'],
    }
    return render(request, "studyprogrammes/programme.html", context)

def programmes_view(request):
    programmes = Programme.objects.filter(user=request.user)
    form = ProgrammeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        programme = form.save(commit=False)
        programme.user = request.user
        programme.save()
        return redirect('programmes')
    # Compute stats for preview
    from .models import Semester, Course, ProgrammeExpectedStudents
    programme_stats = {}
    for prog in programmes:
        semesters = Semester.objects.filter(programme=prog)
        total_ects = 0
        total_sws_min = 0
        total_sws_max = 0
        sws_groups_min = {'lectures': 0.0, 'seminars_tutorials': 0.0, 'other': 0.0}
        sws_groups_max = {'lectures': 0.0, 'seminars_tutorials': 0.0, 'other': 0.0}
        for idx, semester in enumerate(semesters, 1):
            courses = list(Course.objects.filter(semester=semester))
            ects_sum = sum(c.ects for c in courses)
            total_ects += ects_sum
            expected_students = ProgrammeExpectedStudents.objects.filter(degree_type=prog.degree_type, semester=idx).first()
            expected_sws_min = {'lectures': 0.0, 'seminars_tutorials': 0.0, 'other': 0.0}
            expected_sws_max = {'lectures': 0.0, 'seminars_tutorials': 0.0, 'other': 0.0}
            for c in courses:
                min_classes = max_classes = None
                if expected_students and c.max_participants:
                    try:
                        min_val = int(expected_students.min_students)
                        max_val = int(expected_students.max_students)
                        maxp = int(c.max_participants)
                        min_classes = (min_val + maxp - 1) // maxp if min_val > 0 else 1
                        max_classes = (max_val + maxp - 1) // maxp if max_val > 0 else 1
                    except Exception:
                        min_classes = max_classes = None
                group = 'other'
                if c.type == 'lecture':
                    group = 'lectures'
                elif c.type in ('seminar', 'tutorial'):
                    group = 'seminars_tutorials'
                if min_classes and c.sws:
                    try:
                        expected_sws_min[group] += min_classes * float(c.sws)
                    except Exception:
                        pass
                if max_classes and c.sws:
                    try:
                        expected_sws_max[group] += max_classes * float(c.sws)
                    except Exception:
                        pass
            for group in ['lectures', 'seminars_tutorials', 'other']:
                sws_groups_min[group] += expected_sws_min[group]
                sws_groups_max[group] += expected_sws_max[group]
            total_sws_min += sum(expected_sws_min.values())
            total_sws_max += sum(expected_sws_max.values())
        programme_stats[prog.pk] = {
            'total_ects': total_ects,
            'total_sws_min': total_sws_min,
            'total_sws_max': total_sws_max,
            'sws_lectures_min': sws_groups_min['lectures'],
            'sws_lectures_max': sws_groups_max['lectures'],
            'sws_seminars_min': sws_groups_min['seminars_tutorials'],
            'sws_seminars_max': sws_groups_max['seminars_tutorials'],
            'sws_other_min': sws_groups_min['other'],
            'sws_other_max': sws_groups_max['other'],
        }
    # ...existing code...
    if request.method == "POST":
        if "delete_programme" in request.POST:
            programme_id = request.POST.get("delete_programme_id")
            Programme.objects.filter(pk=programme_id).delete()
            return redirect('programmes')
        elif "copy_programme" in request.POST:
            copy_id = request.POST.get("copy_programme_id")
            orig = Programme.objects.filter(pk=copy_id).first()
            if orig:
                new_prog = Programme.objects.create(
                    name=f"{orig.name} (Copy)",
                    degree_type=orig.degree_type,
                    user=request.user
                )
                # Deep copy semesters and courses
                orig_semesters = Semester.objects.filter(programme=orig).order_by('order', 'pk')
                for sem in orig_semesters:
                    new_sem = Semester.objects.create(
                        programme=new_prog,
                        order=sem.order
                    )
                    orig_courses = Course.objects.filter(semester=sem)
                    for course in orig_courses:
                        Course.objects.create(
                            name=course.name,
                            group=course.group,
                            ects=course.ects,
                            sws=course.sws,
                            type=course.type,
                            max_participants=course.max_participants,
                            semester=new_sem,
                            description=course.description,
                            order=course.order
                        )
            return redirect('programmes')
        elif form.is_valid():
            form.save()
            return redirect('programmes')
    return render(request, "studyprogrammes/programmes.html", {
        "programmes": programmes,
        "programme_form": form,
        "programme_stats": programme_stats,
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

from .models import Course

def course_detail_api(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise Http404("Course does not exist")
    return JsonResponse({
        "id": course.id,
        "name": course.name,
        "group": course.group,
        "type": course.type,
        "ects": course.ects,
        "sws": course.sws,
        "max_participants": course.max_participants,
        "semester": course.semester_id,
        "description": course.description,
    })

def logout_then_login(request):
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    logout(request)
    return redirect('/login/')
