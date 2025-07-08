from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Revision, Programme, Module
from .forms import CourseForm, RevisionForm, ProgrammeForm, ModuleForm, ModuleCourseForm
from django.forms import formset_factory

# All possible programme types and names
POSSIBLE_PROGRAMMES = [
    ('bachelor100', "Bachelor 100"),
    ('bachelor60', "Bachelor 60"),
    ('bachelor30', "Bachelor 30"),
    ('teaching_vert', "Lehramt vertieft"),
    ('teaching_nvert', "Lehramt nicht vertieft"),
    ('teaching_gs', "Lehramt Grundschule"),
    ('teaching_ms', "Lehramt Mittelschule"),
    ('master_pg', "Master Phys Geo"),
    ('master_hg', "Master Humangeo"),
]

def course_overview(request):
    courses = Course.objects.all().order_by('name')
    form = CourseForm()
    edit_course = None

    if request.method == 'POST':
        course_id = request.POST.get('edit_course_id')
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            form = CourseForm(request.POST, instance=course)
            edit_course = course
        else:
            form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('v2_course_overview')

    # If GET with ?edit=<id>, prefill form
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_course = get_object_or_404(Course, id=edit_id)
        form = CourseForm(instance=edit_course)

    return render(request, 'studyprogrammes_v2/course_overview.html', {
        'courses': courses,
        'form': form,
        'edit_course': edit_course,
    })

def revision_overview(request):
    revisions = Revision.objects.all().order_by('-created_at')
    form = RevisionForm()
    if request.method == 'POST':
        form = RevisionForm(request.POST)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.author = request.user
            revision.save()
            return redirect('v2_revision_overview')
    return render(request, 'studyprogrammes_v2/revision_overview.html', {
        'revisions': revisions,
        'form': form,
    })

def edit_revision(request, revision_id):
    revision = get_object_or_404(Revision, id=revision_id)
    # Get all programmes for this revision as a dict: {degree_type: Programme}
    existing_programmes = {p.degree_type: p for p in Programme.objects.filter(revision=revision)}
    # Build a list of all possible, marking if present or missing
    programmes = []
    for degree_type, display_name in POSSIBLE_PROGRAMMES:
        programme = existing_programmes.get(degree_type)
        programmes.append({
            'degree_type': degree_type,
            'display_name': display_name,
            'programme': programme,
            'completed': programme is not None,
        })
    return render(request, 'studyprogrammes_v2/edit_revision.html', {
        'revision': revision,
        'programmes': programmes,
    })

def edit_programme(request, revision_id, degree_type):
    revision = get_object_or_404(Revision, id=revision_id)
    programme = Programme.objects.filter(revision=revision, degree_type=degree_type).first()
    if not programme:
        # Create and save the programme if it doesn't exist
        programme = Programme(revision=revision, degree_type=degree_type)
        form = ProgrammeForm(request.POST or None, instance=programme)
        if request.method == 'POST' and form.is_valid():
            programme = form.save()  # Save and get the instance with pk
            return redirect('v2_edit_programme', revision_id=revision.id, degree_type=degree_type)
    else:
        form = ProgrammeForm(request.POST or None, instance=programme)
        if request.method == 'POST' and form.is_valid() and 'add_module' not in request.POST:
            form.save()
            return redirect('v2_edit_programme', revision_id=revision.id, degree_type=degree_type)

    # Always fetch modules for the current programme (after possible creation)
    modules = []
    if programme and programme.pk:
        modules = Module.objects.filter(programme=programme)

    # Build a list of modules with their courses and earliest semester
    module_cards = []
    for module in modules:
        module_courses = list(module.module_courses.all())
        if not module_courses:
            continue  # Only show modules with at least one course
        # Group courses by semester and collect all course info
        courses_info = []
        min_semester = min(mc.semester for mc in module_courses)
        for mc in sorted(module_courses, key=lambda x: (x.semester, x.course.name)):
            courses_info.append({
                'name': mc.course.name,
                'description': mc.course.description,
                'ects': mc.course.ects,
                'sws': mc.course.sws,
                'semester': mc.semester,
                'type': getattr(mc.course, 'get_type_display', lambda: '')(),
                'discipline': getattr(mc.course, 'get_discipline_display', lambda: '')(),
            })
        module_cards.append({
            'module': module,
            'min_semester': min_semester,
            'courses': courses_info,
        })
    # Sort modules by earliest semester
    module_cards.sort(key=lambda m: m['min_semester'])

    # Semester logic
    SEMESTER_COUNT = {
        'bachelor100': 6, 'bachelor60': 6, 'bachelor30': 6,
        'teaching_vert': 9, 'teaching_nvert': 7, 'teaching_gs': 7, 'teaching_ms': 7,
        'master_pg': 4, 'master_hg': 4,
    }
    num_semesters = SEMESTER_COUNT.get(degree_type, 6)
    semesters = list(range(1, num_semesters + 1))

    # Handle module creation via modal
    module_form = ModuleForm()
    course_formset = ModuleCourseFormSet()
    edit_module = None
    edit_module_id = request.GET.get('edit_module') or request.POST.get('edit_module_id')
    if edit_module_id:
        try:
            edit_module = Module.objects.get(pk=edit_module_id, programme=programme)
        except (Module.DoesNotExist, ValueError):
            edit_module = None
        if edit_module:
            if request.method == 'POST' and 'edit_module' in request.POST:
                module_form = ModuleForm(request.POST, instance=edit_module)
                course_formset = ModuleCourseFormSet(request.POST)
                if module_form.is_valid() and course_formset.is_valid():
                    pairs = []
                    has_course = False
                    duplicate = False
                    for form in course_formset:
                        course = form.cleaned_data.get('course')
                        semester = form.cleaned_data.get('semester')
                        if course and semester:
                            has_course = True
                            pair = (course.id, semester)
                            if pair in pairs:
                                duplicate = True
                            pairs.append(pair)
                    if not has_course:
                        module_form.add_error(None, "Mindestens ein Kurs und Semester muss angegeben werden.")
                    elif duplicate:
                        module_form.add_error(None, "Jede Kurs/Semester-Kombination darf nur einmal vorkommen.")
                    else:
                        module = module_form.save()
                        # Remove old module courses and add new ones
                        module.module_courses.all().delete()
                        for form in course_formset:
                            course = form.cleaned_data.get('course')
                            semester = form.cleaned_data.get('semester')
                            if course and semester:
                                module.module_courses.create(course=course, semester=semester)
                        return redirect('v2_edit_programme', revision_id=revision.id, degree_type=degree_type)
            else:
                # GET: prefill form and formset
                module_form = ModuleForm(instance=edit_module)
                initial = []
                for mc in edit_module.module_courses.all():
                    initial.append({'course': mc.course, 'semester': mc.semester})
                course_formset = ModuleCourseFormSet(initial=initial)
    elif request.method == 'POST' and 'add_module' in request.POST:
        module_form = ModuleForm(request.POST)
        course_formset = ModuleCourseFormSet(request.POST)
        if module_form.is_valid() and course_formset.is_valid():
            # Check that at least one course+semester is filled
            pairs = []
            has_course = False
            duplicate = False
            for form in course_formset:
                course = form.cleaned_data.get('course')
                semester = form.cleaned_data.get('semester')
                if course and semester:
                    has_course = True
                    pair = (course.id, semester)
                    if pair in pairs:
                        duplicate = True
                    pairs.append(pair)
            if not has_course:
                module_form.add_error(None, "Mindestens ein Kurs und Semester muss angegeben werden.")
            elif duplicate:
                module_form.add_error(None, "Jede Kurs/Semester-Kombination darf nur einmal vorkommen.")
            else:
                new_module = module_form.save(commit=False)
                new_module.programme = programme
                new_module.save()
                for form in course_formset:
                    course = form.cleaned_data.get('course')
                    semester = form.cleaned_data.get('semester')
                    if course and semester:
                        new_module.module_courses.create(course=course, semester=semester)
                return redirect('v2_edit_programme', revision_id=revision.id, degree_type=degree_type)

    # Pass 'semesters' in your context:
    return render(request, 'studyprogrammes_v2/edit_programme.html', {
        'revision': revision,
        'programme': programme,
        'form': form,
        'modules': modules,
        'module_form': module_form,
        'course_formset': course_formset,
        'num_semesters': num_semesters,
        'degree_type': degree_type,
        'semesters': semesters,
        'module_cards': module_cards,
        'programme_name': programme.name if programme else '',
    })

ModuleCourseFormSet = formset_factory(ModuleCourseForm, extra=1, min_num=1, validate_min=True)
