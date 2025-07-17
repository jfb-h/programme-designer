from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db import models
from .models import Course, Module, Programme, Revision, ProgrammeType, ProgrammeModule, ProgrammeStudentCount, ProgrammeNebenfach, DefaultStudentCount, CourseType, Discipline, CourseModule, CertificateOption, CertificateGroup, ModuleCertificate, ModuleCertificateGroup
from .forms import CourseForm, ModuleForm, ProgrammeForm, RevisionForm, ModuleCertificateForm


@login_required
def course_overview(request):
    """Overview of all courses with ability to add/edit and share."""
    from django.utils import timezone
    
    # Handle tab selection
    current_tab = request.GET.get('tab', 'my')
    
    # Get courses based on tab
    if current_tab == 'shared':
        # Show shared courses (courses where is_shared=True)
        courses = Course.objects.filter(is_shared=True)
    else:
        # Show user's own courses
        courses = Course.objects.filter(user=request.user, is_shared=False)
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'name')
    sort_order = request.GET.get('order', 'asc')
    
    # Valid sortable fields
    valid_sorts = ['name', 'course_type', 'discipline']
    if sort_by not in valid_sorts:
        sort_by = 'name'
    
    # Apply sorting
    if sort_order == 'desc':
        sort_by = f'-{sort_by}'
    
    courses = courses.order_by(sort_by)
    
    # Get counts for tab badges
    my_courses_count = Course.objects.filter(user=request.user, is_shared=False).count()
    shared_courses_count = Course.objects.filter(is_shared=True).count()
    
    form = CourseForm()
    edit_course = None

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        
        if action == 'copy':
            # Handle course copying
            course_id = request.POST.get('course_id')
            if course_id:
                try:
                    original_course = Course.objects.get(id=course_id)
                    # Create a copy with modified name
                    copied_course = Course.objects.create(
                        name=f"{original_course.name} (Kopie)",
                        description=original_course.description,
                        course_type=original_course.course_type,
                        ects=original_course.ects,
                        sws=original_course.sws,
                        max_participants=original_course.max_participants,
                        discipline=original_course.discipline,
                        user=request.user,  # Set to current user
                        is_shared=False,  # Copies are always private initially
                    )
                    # Copy many-to-many relationships (LPO relevance)
                    copied_course.lpo_relevance.set(original_course.lpo_relevance.all())
                    messages.success(request, f'Kurs "{original_course.name}" wurde kopiert.')
                    
                except Course.DoesNotExist:
                    messages.error(request, 'Kurs nicht gefunden!')
                
                # Check if there's a return URL
                return_url = request.POST.get('return_url') or request.GET.get('return_url')
                if return_url:
                    return redirect(return_url)
                
                # Preserve tab state
                current_tab = request.GET.get('tab', 'my')
                from django.shortcuts import reverse
                from urllib.parse import urlencode
                url = reverse('v2_course_overview')
                return redirect(f'{url}?{urlencode({"tab": current_tab})}')
        
        elif action == 'share':
            # Handle course sharing
            course_id = request.POST.get('course_id')
            if course_id:
                try:
                    course = Course.objects.get(id=course_id, user=request.user)
                    if not course.is_shared:
                        # Create a shared copy
                        shared_course = Course.objects.create(
                            name=course.name,
                            description=course.description,
                            course_type=course.course_type,
                            ects=course.ects,
                            sws=course.sws,
                            max_participants=course.max_participants,
                            discipline=course.discipline,
                            user=course.user,  # Keep original user
                            is_shared=True,
                            shared_by=request.user,
                            shared_at=timezone.now(),
                            original_course=course
                        )
                        # Copy many-to-many relationships
                        shared_course.lpo_relevance.set(course.lpo_relevance.all())
                        messages.success(request, f'Kurs "{course.name}" wurde geteilt.')
                    else:
                        messages.info(request, 'Dieser Kurs ist bereits geteilt.')
                        
                except Course.DoesNotExist:
                    messages.error(request, 'Kurs nicht gefunden oder Sie haben keine Berechtigung!')
                
                # Preserve tab state
                current_tab = request.GET.get('tab', 'my')
                from django.shortcuts import reverse
                from urllib.parse import urlencode
                url = reverse('v2_course_overview')
                return redirect(f'{url}?{urlencode({"tab": current_tab})}')
        
        else:
            # Handle normal save/edit functionality
            course_id = request.POST.get('edit_course_id')
            if course_id:
                # Edit existing course
                edit_course = get_object_or_404(Course, id=course_id)
                form = CourseForm(request.POST, instance=edit_course)
            else:
                # Create new course
                form = CourseForm(request.POST)
            
            if form.is_valid():
                course = form.save(commit=False)
                # Always set user for new courses (when pk is None)
                if course.pk is None:
                    course.user = request.user
                    course.is_shared = False  # New courses are private by default
                course.save()
                # Save many-to-many relationships
                form.save_m2m()
                # Always redirect after successful save (Post/Redirect/Get)
                return_url = request.POST.get('return_url') or request.GET.get('return_url')
                if return_url:
                    return redirect(return_url)
                
                # Remove edit_course from context by redirecting to overview with preserved tab
                current_tab = request.GET.get('tab', 'my')
                from django.shortcuts import reverse
                from urllib.parse import urlencode
                url = reverse('v2_course_overview')
                return redirect(f'{url}?{urlencode({"tab": current_tab})}')

    # Handle edit mode (GET with ?edit=<id>)
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_course = get_object_or_404(Course, id=edit_id)
        form = CourseForm(instance=edit_course)

    return render(request, 'studyprogrammes_v2/course_overview.html', {
        'courses': courses,
        'form': form,
        'edit_course': edit_course,
        'current_sort': request.GET.get('sort', 'name'),
        'current_order': request.GET.get('order', 'asc'),
        'current_tab': current_tab,
        'my_courses_count': my_courses_count,
        'shared_courses_count': shared_courses_count,
        'return_url': request.GET.get('return_url'),
    })


@login_required
def module_overview(request):
    """Overview of all modules with ability to add/edit."""
    modules = Module.objects.all()
    form = ModuleForm()
    edit_module = None

    if request.method == 'POST':
        module_id = request.POST.get('edit_module_id')
        if module_id:
            # Edit existing module
            edit_module = get_object_or_404(Module, id=module_id)
            form = ModuleForm(request.POST, instance=edit_module)
        else:
            # Create new module
            form = ModuleForm(request.POST)

        if form.is_valid():
            module = form.save(commit=False)
            module.save()
            form.save_m2m()

            # Remove existing CourseModule links for this module (if editing)
            if module_id:
                module.coursemodule_set.all().delete()

            # For each selected course, create CourseModule with semester
            selected_courses = form.cleaned_data['courses']
            for course in selected_courses:
                semester_val = request.POST.get(f'semester_for_{course.id}')
                try:
                    semester = int(semester_val)
                except (TypeError, ValueError):
                    semester = 1
                # Order can be set to 0 or incremented if needed
                CourseModule.objects.create(module=module, course=course, semester=semester, order=0)

            return redirect('v2_module_overview')

    # Handle edit mode (GET with ?edit=<id>)
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_module = get_object_or_404(Module, id=edit_id)
        form = ModuleForm(instance=edit_module)

    return render(request, 'studyprogrammes_v2/module_overview.html', {
        'modules': modules,
        'form': form,
        'edit_module': edit_module,
    })


@login_required
def programme_overview(request):
    """Overview of all programmes with ability to add/edit and share."""
    from django.utils import timezone
    
    # Handle tab selection
    current_tab = request.GET.get('tab', 'my')
    
    # Get programmes based on tab
    if current_tab == 'shared':
        # Show shared programmes (programmes where is_shared=True)
        programmes = Programme.objects.filter(is_shared=True).order_by('name')
    else:
        # Show user's own programmes
        programmes = Programme.objects.filter(user=request.user, is_shared=False).order_by('name')
    
    # Handle sorting
    sort_param = request.GET.get('sort', 'name')
    if sort_param == 'name':
        programmes = programmes.order_by('name')
    elif sort_param == 'created':
        programmes = programmes.order_by('-created_at')
    else:
        programmes = programmes.order_by('name')
    
    # Get counts for tab badges
    my_programmes_count = Programme.objects.filter(user=request.user, is_shared=False).count()
    shared_programmes_count = Programme.objects.filter(is_shared=True).count()
    
    form = ProgrammeForm()
    edit_programme = None

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        
        if action == 'copy':
            # Handle programme copying
            programme_id = request.POST.get('programme_id')
            if programme_id:
                try:
                    original_programme = Programme.objects.get(id=programme_id)
                    # Create a copy with modified name
                    copied_programme = Programme.objects.create(
                        name=f"{original_programme.name} (Kopie)",
                        comment=original_programme.comment,
                        programme_type=original_programme.programme_type,
                        user=request.user,  # Set to current user
                        is_shared=False,  # Copies are always private initially
                    )
                    # Deep copy modules and their relationships
                    from .models import Module, ProgrammeModule, CourseModule
                    
                    for programme_module in original_programme.programmemodule_set.all().order_by('order'):
                        original_module = programme_module.module
                        
                        # Create a new module copy
                        copied_module = Module.objects.create(
                            name=original_module.name,
                            description=original_module.description,
                            certificate=original_module.certificate,
                            user=request.user,  # Set to current user
                            order=original_module.order
                        )
                        
                        # Copy course relationships
                        for course_module in original_module.coursemodule_set.all().order_by('order'):
                            CourseModule.objects.create(
                                module=copied_module,
                                course=course_module.course,  # Keep reference to same course
                                semester=course_module.semester,
                                order=course_module.order
                            )
                        
                        # Copy module certificate if it exists
                        try:
                            original_cert = original_module.module_certificate
                            from .models import ModuleCertificate
                            copied_cert = ModuleCertificate.objects.create(
                                module=copied_module,
                                logic_operator=original_cert.logic_operator,
                                comment=original_cert.comment,
                                is_graded=original_cert.is_graded
                            )
                            copied_cert.selected_options.set(original_cert.selected_options.all())
                        except:
                            pass  # No certificate to copy
                        
                        # Add module to programme with same order
                        ProgrammeModule.objects.create(
                            programme=copied_programme,
                            module=copied_module,
                            order=programme_module.order
                        )
                    
                    messages.success(request, f'Studiengang "{original_programme.name}" wurde kopiert.')
                    
                except Programme.DoesNotExist:
                    messages.error(request, 'Studiengang nicht gefunden!')
                
                # Preserve tab state
                current_tab = request.GET.get('tab', 'my')
                from django.shortcuts import reverse
                from urllib.parse import urlencode
                url = reverse('v2_programme_overview')
                return redirect(f'{url}?{urlencode({"tab": current_tab})}')
        
        elif action == 'share':
            # Handle programme sharing
            programme_id = request.POST.get('programme_id')
            if programme_id:
                try:
                    programme = Programme.objects.get(id=programme_id, user=request.user)
                    if not programme.is_shared:
                        # Create a shared copy
                        shared_programme = Programme.objects.create(
                            name=programme.name,
                            comment=programme.comment,
                            programme_type=programme.programme_type,
                            user=programme.user,  # Keep original user
                            is_shared=True,
                            shared_by=request.user,
                            shared_at=timezone.now(),
                            original_programme=programme
                        )
                        # Copy many-to-many relationships (modules)
                        shared_programme.modules.set(programme.modules.all())
                        
                        # Auto-share all courses in the programme
                        courses_to_share = []
                        for module in programme.modules.all():
                            for course in module.courses.filter(user=request.user, is_shared=False):
                                courses_to_share.append(course)
                        
                        # Mark unshared courses as shared (don't copy them)
                        shared_courses_count = 0
                        for course in courses_to_share:
                            course.is_shared = True
                            course.shared_by = request.user
                            course.shared_at = timezone.now()
                            course.save()
                            shared_courses_count += 1
                        
                        success_msg = f'Studiengang "{programme.name}" wurde geteilt.'
                        if shared_courses_count > 0:
                            success_msg += f' {shared_courses_count} Kurse wurden automatisch mitgeteilt.'
                        messages.success(request, success_msg)
                    else:
                        messages.info(request, 'Dieser Studiengang ist bereits geteilt.')
                        
                except Programme.DoesNotExist:
                    messages.error(request, 'Studiengang nicht gefunden oder Sie haben keine Berechtigung!')
                
                # Preserve tab state
                current_tab = request.GET.get('tab', 'my')
                from django.shortcuts import reverse
                from urllib.parse import urlencode
                url = reverse('v2_programme_overview')
                return redirect(f'{url}?{urlencode({"tab": current_tab})}')
        
        else:
            # Handle normal save/edit functionality
            programme_id = request.POST.get('edit_programme_id')
            if programme_id:
                # Edit existing programme
                edit_programme = get_object_or_404(Programme, id=programme_id)
                form = ProgrammeForm(request.POST, instance=edit_programme)
            else:
                # Create new programme
                form = ProgrammeForm(request.POST)
            
            if form.is_valid():
                programme = form.save(commit=False)
                # Always set user for new programmes (when pk is None)
                if programme.pk is None:
                    programme.user = request.user
                    programme.is_shared = False  # New programmes are private by default
                programme.save()
                
                # Preserve tab state
                current_tab = request.GET.get('tab', 'my')
                from django.shortcuts import reverse
                from urllib.parse import urlencode
                url = reverse('v2_programme_overview')
                return redirect(f'{url}?{urlencode({"tab": current_tab})}')

    # Handle edit mode (GET with ?edit=<id>)
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_programme = get_object_or_404(Programme, id=edit_id)
        form = ProgrammeForm(instance=edit_programme)

    return render(request, 'studyprogrammes_v2/programme_overview.html', {
        'programmes': programmes,
        'form': form,
        'edit_programme': edit_programme,
        'current_tab': current_tab,
        'my_programmes_count': my_programmes_count,
        'shared_programmes_count': shared_programmes_count,
    })


@login_required
def revision_overview(request):
    """Overview of all revisions."""
    revisions = Revision.objects.all()
    form = RevisionForm()
    
    if request.method == 'POST':
        form = RevisionForm(request.POST)
        
        if form.is_valid():
            revision = form.save(commit=False)
            revision.author = request.user
            revision.save()
            form.save_m2m()  # Save many-to-many relationships (programmes)
            return redirect('v2_revision_overview')

    return render(request, 'studyprogrammes_v2/revision_overview.html', {
        'revisions': revisions,
        'form': form,
    })


@login_required
def revision_detail(request, revision_id):
    """Detailed view of a specific revision with programme management."""
    revision = get_object_or_404(Revision, id=revision_id)
    
    # Use the new model methods for better organization
    programmes_by_type = revision.get_programmes_by_type()
    missing_programme_types = revision.get_missing_programme_types()
    
    # Get all programme types for display
    programme_types = ProgrammeType.choices
    
    # Get aggregate statistics for the revision
    revision_stats = {
        'total_ects': revision.get_total_ects(),
        'total_sws': revision.get_total_sws(),
        'total_courses': revision.get_total_courses(),
        'total_modules': revision.get_total_modules(),
        'ects_by_course_type': revision.get_ects_by_course_type(),
        'ects_by_discipline': revision.get_ects_by_discipline(),
        'ects_by_lpo_category': revision.get_ects_by_lpo_category(),
        'sws_range_total': revision.get_sws_range_total(),
        'sws_by_course_type': revision.get_sws_by_course_type(),
        'sws_by_discipline': revision.get_sws_by_discipline(),
        'sws_by_semester_and_type': revision.get_sws_by_semester_and_type(),
        'sws_by_semester_and_discipline': revision.get_sws_by_semester_and_discipline(),
    }
    
    # Add winter/summer SWS data
    winter_summer_data = revision.get_winter_summer_sws()
    revision_stats.update(winter_summer_data)
    
    # Get student count data
    student_counts_data = revision.get_aggregate_student_counts()

    return render(request, 'studyprogrammes_v2/revision_detail.html', {
        'revision': revision,
        'programme_types': programme_types,
        'programmes_by_type': programmes_by_type,
        'missing_programme_types': missing_programme_types,
        'is_complete': revision.is_complete(),
        'revision_stats': revision_stats,
        'student_counts_data': student_counts_data,
        'course_type_choices': CourseType.choices,
        'discipline_choices': Discipline.choices,
    })


@login_required
def edit_revision(request, revision_id):
    """Edit a specific revision and its programmes."""
    revision = get_object_or_404(Revision, id=revision_id)
    
    if request.method == 'POST':
        # Handle programme selection for each type
        for choice_value, choice_display in ProgrammeType.choices:
            programme_param = f'programme_{choice_value}'
            programme_id = request.POST.get(programme_param)
            
            # Remove existing programme of this type from revision
            existing_programme = revision.programmes.filter(programme_type=choice_value).first()
            if existing_programme:
                revision.programmes.remove(existing_programme)
            
            # Add selected programme if provided
            if programme_id:
                try:
                    programme = Programme.objects.get(id=programme_id, programme_type=choice_value)
                    revision.programmes.add(programme)
                except Programme.DoesNotExist:
                    messages.error(request, f'Studiengang für {choice_display} nicht gefunden.')
        
        return redirect('v2_revision_detail', revision_id=revision.id)
    
    # Get existing programmes in this revision
    existing_programmes = list(revision.programmes.all())
    
    # Build list of all possible programme types with available options
    programme_options = []
    existing_types = [p.programme_type for p in existing_programmes]
    
    for choice_value, choice_display in ProgrammeType.choices:
        existing_programme = next(
            (p for p in existing_programmes if p.programme_type == choice_value), 
            None
        )
        
        # Get all available programmes of this type (user can select from)
        available_programmes = revision.get_available_programmes_for_type(
            choice_value, 
            user=revision.author if hasattr(revision, 'author') else None
        )
        
        # Include currently selected programme in options even if not available
        all_options = list(available_programmes)
        if existing_programme and existing_programme not in all_options:
            all_options.insert(0, existing_programme)
        
        programme_options.append({
            'type': choice_value,
            'display': choice_display,
            'selected_programme': existing_programme,
            'available_programmes': all_options,
            'exists': existing_programme is not None,
        })

    return render(request, 'studyprogrammes_v2/edit_revision.html', {
        'revision': revision,
        'programme_options': programme_options,
    })


def edit_programme(request, revision_id, programme_type):
    """Edit a specific programme within a revision."""
    revision = get_object_or_404(Revision, id=revision_id)
    
    # Get or create programme
    programme = revision.programmes.filter(programme_type=programme_type).first()
    if not programme:
        # Create new programme
        programme = Programme.objects.create(
            name=f"{dict(ProgrammeType.choices)[programme_type]}",
            programme_type=programme_type,
            user=request.user
        )
        revision.programmes.add(programme)

    form = ProgrammeForm(instance=programme)
    
    if request.method == 'POST':
        form = ProgrammeForm(request.POST, instance=programme)
        if form.is_valid():
            form.save()
            return redirect('v2_edit_programme', revision_id=revision.id, programme_type=programme_type)

    return render(request, 'studyprogrammes_v2/edit_programme.html', {
        'revision': revision,
        'programme': programme,
        'form': form,
        'programme_type_display': dict(ProgrammeType.choices)[programme_type],
    })


def delete_course(request, course_id):
    """Delete a course."""
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
    
    # Preserve tab state
    current_tab = request.GET.get('tab', 'my')
    from django.shortcuts import reverse
    from urllib.parse import urlencode
    url = reverse('v2_course_overview')
    return redirect(f'{url}?{urlencode({"tab": current_tab})}')


def delete_module(request, module_id):
    """Delete a module."""
    module = get_object_or_404(Module, id=module_id)
    if request.method == 'POST':
        module.delete()
    return redirect('v2_module_overview')


def delete_programme(request, programme_id):
    """Delete a programme."""
    programme = get_object_or_404(Programme, id=programme_id)
    if request.method == 'POST':
        programme.delete()
    
    # Preserve tab state
    current_tab = request.GET.get('tab', 'my')
    from django.shortcuts import reverse
    from urllib.parse import urlencode
    url = reverse('v2_programme_overview')
    return redirect(f'{url}?{urlencode({"tab": current_tab})}')


def delete_revision(request, revision_id):
    """Delete a revision."""
    revision = get_object_or_404(Revision, id=revision_id)
    if request.method == 'POST':
        revision.delete()
    return redirect('v2_revision_overview')


@login_required
def programme_detail(request, programme_id):
    """Detail view for a programme where modules can be managed."""
    programme = get_object_or_404(Programme, id=programme_id)
    all_courses = Course.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_student_count':
            # Handle AJAX student count updates
            semester = request.POST.get('semester')
            count_type = request.POST.get('type')  # 'min' or 'max'
            value = request.POST.get('value')
            
            try:
                semester = int(semester)
                value = int(value) if value else 0
                
                # Get or create the student count record
                student_count, created = ProgrammeStudentCount.objects.get_or_create(
                    programme=programme,
                    semester=semester,
                    defaults={'min_students': 0, 'max_students': 0}
                )
                
                # Update the appropriate field
                if count_type == 'min':
                    student_count.min_students = value
                elif count_type == 'max':
                    student_count.max_students = value
                else:
                    return JsonResponse({'status': 'error', 'message': 'Invalid type'})
                
                student_count.save()
                return JsonResponse({'status': 'success'})
                
            except (ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': 'Invalid data'})
        
        elif action == 'update_nebenfach':
            # Handle AJAX nebenfach ECTS updates
            semester = request.POST.get('semester')
            value = request.POST.get('value')
            
            try:
                semester = int(semester)
                value = int(value) if value else 0
                
                # Get or create the nebenfach record
                nebenfach, created = ProgrammeNebenfach.objects.get_or_create(
                    programme=programme,
                    semester=semester,
                    defaults={'ects': 0}
                )
                
                nebenfach.ects = value
                nebenfach.save()
                return JsonResponse({'status': 'success'})
                
            except (ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': 'Invalid data'})
        
        elif action == 'remove_module':
            module_id = request.POST.get('module_id')
            if module_id:
                # Remove using the through model
                ProgrammeModule.objects.filter(
                    programme=programme, 
                    module_id=module_id
                ).delete()
        
        elif action == 'create_module':
            module_name = request.POST.get('module_name')
            module_description = request.POST.get('module_description', '')
            module_qualification_goals = request.POST.get('module_qualification_goals', '')
            module_responsible_person = request.POST.get('module_responsible_person', '')
            selected_courses = request.POST.getlist('module_courses')
            
            # Certificate form data - handle both legacy and new group system
            # Legacy system (fallback)
            selected_options = request.POST.getlist('certificate_options')
            logic_operator = request.POST.get('logic_operator', 'or')
            
            # New group system
            certificate_group_count = int(request.POST.get('certificate_group_count', 0))
            global_operator = request.POST.get('global_operator', 'or')
            
            certificate_comment = request.POST.get('certificate_comment', '')
            is_graded = request.POST.get('is_graded') == 'on'
            
            if module_name:
                # Create the new module and automatically add it to this programme
                new_module = Module.objects.create(
                    name=module_name.strip(),
                    description=module_description.strip(),
                    qualification_goals=module_qualification_goals.strip(),
                    responsible_person=module_responsible_person.strip()
                )
                
                # Always create module certificate to preserve is_graded state
                module_cert, created = ModuleCertificate.objects.get_or_create(
                    module=new_module,
                    defaults={
                        'logic_operator': logic_operator,
                        'global_operator': global_operator,
                        'comment': certificate_comment.strip(),
                        'is_graded': is_graded
                    }
                )
                if not created:
                    module_cert.logic_operator = logic_operator
                    module_cert.global_operator = global_operator
                    module_cert.comment = certificate_comment.strip()
                    module_cert.is_graded = is_graded
                    module_cert.save()
                
                # Save complete group structure to JSON field
                all_options = []
                group_structure = {
                    "global_operator": global_operator,
                    "groups": []
                }
                
                if certificate_group_count > 0:
                    for group_num in range(1, certificate_group_count + 1):
                        group_options = request.POST.getlist(f'group_{group_num}_options')
                        group_operator = request.POST.get(f'group_{group_num}_operator', 'or')
                        
                        # Convert string IDs to integers
                        group_option_ids = [int(opt_id) for opt_id in group_options if opt_id]
                        
                        if group_option_ids:  # Only add groups with options
                            group_structure["groups"].append({
                                "options": group_option_ids,
                                "internal_operator": group_operator,
                                "order": group_num
                            })
                            all_options.extend(group_option_ids)
                    
                    # Save group structure
                    module_cert.group_structure = group_structure
                    
                    # Also save to legacy field for backward compatibility
                    unique_options = list(dict.fromkeys(all_options))  # Remove duplicates preserving order
                    module_cert.selected_options.set(unique_options)
                    
                else:
                    # Clear group structure and fallback to legacy system
                    module_cert.group_structure = {}
                    if selected_options:
                        module_cert.selected_options.set(selected_options)
                
                module_cert.save()
                
                # Add selected courses to the module with semester
                if selected_courses:
                    for course_id in selected_courses:
                        try:
                            original_course = Course.objects.get(id=course_id)
                            semester_val = request.POST.get(f'semester_for_{course_id}')
                            try:
                                semester = int(semester_val)
                            except (TypeError, ValueError):
                                semester = 1
                            
                            # Always use the original course - courses should be shared across modules
                            CourseModule.objects.create(module=new_module, course=original_course, semester=semester, order=0)
                        except Course.DoesNotExist:
                            pass
                
                # Always add to this programme since modules are unique to programmes
                # Get the next order value
                max_order = ProgrammeModule.objects.filter(programme=programme).count()
                ProgrammeModule.objects.create(
                    programme=programme,
                    module=new_module,
                    order=max_order
                )
            else:
                pass  # Module name is required but no error message
        
        elif action == 'edit_module':
            module_id = request.POST.get('module_id')
            module_name = request.POST.get('module_name')
            module_description = request.POST.get('module_description', '')
            module_qualification_goals = request.POST.get('module_qualification_goals', '')
            module_responsible_person = request.POST.get('module_responsible_person', '')
            selected_courses = request.POST.getlist('module_courses')
            
            # Certificate form data - handle both legacy and new group system
            # Legacy system (fallback)
            selected_options = request.POST.getlist('certificate_options')
            logic_operator = request.POST.get('logic_operator', 'or')
            
            # New group system
            certificate_group_count = int(request.POST.get('certificate_group_count', 0))
            global_operator = request.POST.get('global_operator', 'or')
            
            
            certificate_comment = request.POST.get('certificate_comment', '')
            is_graded = request.POST.get('is_graded') == 'on'
            
            if module_id and module_name:
                try:
                    module = Module.objects.get(id=module_id)
                    # Update module details
                    module.name = module_name.strip()
                    module.description = module_description.strip()
                    module.qualification_goals = module_qualification_goals.strip()
                    module.responsible_person = module_responsible_person.strip()
                    module.save()
                    
                    # Always create or update module certificate to preserve is_graded state
                    module_cert, created = ModuleCertificate.objects.get_or_create(
                        module=module,
                        defaults={
                            'logic_operator': logic_operator,
                            'global_operator': global_operator,
                            'comment': certificate_comment.strip(),
                            'is_graded': is_graded
                        }
                    )
                    if not created:
                        module_cert.logic_operator = logic_operator
                        module_cert.global_operator = global_operator
                        module_cert.comment = certificate_comment.strip()
                        module_cert.is_graded = is_graded
                        module_cert.save()
                    
                    # Save complete group structure to JSON field
                    all_options = []
                    group_structure = {
                        "global_operator": global_operator,
                        "groups": []
                    }
                    
                    if certificate_group_count > 0:
                        for group_num in range(1, certificate_group_count + 1):
                            group_options = request.POST.getlist(f'group_{group_num}_options')
                            group_operator = request.POST.get(f'group_{group_num}_operator', 'or')
                            
                            # Convert string IDs to integers
                            group_option_ids = [int(opt_id) for opt_id in group_options if opt_id]
                            
                            if group_option_ids:  # Only add groups with options
                                group_structure["groups"].append({
                                    "options": group_option_ids,
                                    "internal_operator": group_operator,
                                    "order": group_num
                                })
                                all_options.extend(group_option_ids)
                        
                        # Save group structure
                        module_cert.group_structure = group_structure
                        
                        # Also save to legacy field for backward compatibility
                        unique_options = list(dict.fromkeys(all_options))  # Remove duplicates preserving order
                        module_cert.selected_options.set(unique_options)
                        
                    else:
                        # Clear group structure and fallback to legacy system
                        module_cert.group_structure = {}
                        if selected_options:
                            module_cert.selected_options.set(selected_options)
                        else:
                            module_cert.selected_options.clear()
                    
                    module_cert.save()
                    
                    # Update courses - first clear all CourseModule links, then add selected ones with semester
                    module.coursemodule_set.all().delete()
                    if selected_courses:
                        for course_id in selected_courses:
                            try:
                                original_course = Course.objects.get(id=course_id)
                                semester_val = request.POST.get(f'semester_for_{course_id}')
                                try:
                                    semester = int(semester_val)
                                except (TypeError, ValueError):
                                    semester = 1
                                
                                # Always use the original course - courses should be shared across modules
                                CourseModule.objects.create(module=module, course=original_course, semester=semester, order=0)
                            except Course.DoesNotExist:
                                pass
                except Module.DoesNotExist:
                    pass  # Module not found but no error message
        
        return redirect('v2_programme_detail', programme_id=programme.id)
    
    # Prepare student count data for template
    semester_count = programme.get_semester_count()
    semester_range = range(1, semester_count + 1)
    
    # Get existing student counts and ensure they're integers
    existing_counts = ProgrammeStudentCount.objects.filter(programme=programme)
    existing_counts_dict = {
        'min': {int(sc.semester): int(sc.min_students) for sc in existing_counts},
        'max': {int(sc.semester): int(sc.max_students) for sc in existing_counts}
    }
    
    # Get default student counts for this programme type
    default_counts = DefaultStudentCount.objects.filter(programme_type=programme.programme_type)
    default_counts_dict = {
        'min': {int(dc.semester): int(dc.min_students) for dc in default_counts},
        'max': {int(dc.semester): int(dc.max_students) for dc in default_counts}
    }
    
    # Build final student_counts dict with fallback logic
    student_counts = {'min': {}, 'max': {}}
    for semester in semester_range:
        # Use programme-specific value if exists, otherwise use default, otherwise use fallback
        student_counts['min'][semester] = (
            existing_counts_dict['min'].get(semester) or 
            default_counts_dict['min'].get(semester) or 
            20  # fallback
        )
        student_counts['max'][semester] = (
            existing_counts_dict['max'].get(semester) or 
            default_counts_dict['max'].get(semester) or 
            30  # fallback
        )
    
    # Get existing nebenfach ECTS
    existing_nebenfach = ProgrammeNebenfach.objects.filter(programme=programme)
    nebenfach_ects = {int(nf.semester): int(nf.ects) for nf in existing_nebenfach}
    
    programme_modules = programme.get_ordered_modules()
    
    # Get certificate options and groups for the forms
    certificate_options = CertificateOption.objects.all().order_by('order', 'name')
    certificate_groups = CertificateGroup.objects.all().order_by('order', 'name')
    
    return render(request, 'studyprogrammes_v2/programme_detail.html', {
        'programme': programme,
        'programme_modules': programme_modules,
        'all_courses': all_courses,
        'semester_range': semester_range,
        'student_counts': student_counts,
        'nebenfach_ects': nebenfach_ects,
        'certificate_options': certificate_options,
        'certificate_groups': certificate_groups,
    })


def reorder_modules(request, programme_id):
    """Handle module reordering for a programme."""
    if request.method == 'POST':
        programme = get_object_or_404(Programme, id=programme_id)
        module_ids = request.POST.getlist('module_ids[]')
        
        # Update the order using the ProgrammeModule through model
        # More robust approach: update existing relationships instead of deleting
        for order, module_id in enumerate(module_ids):
            if module_id:
                try:
                    programme_module = ProgrammeModule.objects.get(
                        programme=programme,
                        module_id=module_id
                    )
                    programme_module.order = order
                    programme_module.save()
                except ProgrammeModule.DoesNotExist:
                    # If the relationship doesn't exist, create it
                    try:
                        module = Module.objects.get(id=module_id)
                        ProgrammeModule.objects.create(
                            programme=programme,
                            module=module,
                            order=order
                        )
                    except Module.DoesNotExist:
                        continue
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


def get_available_programmes(request, revision_id, programme_type):
    """AJAX endpoint to get available programmes for a specific type."""
    revision = get_object_or_404(Revision, id=revision_id)
    
    # Get current programme of this type in the revision
    current_programme = revision.programmes.filter(programme_type=programme_type).first()
    
    # Get all available programmes of this type
    # Include programmes without user assignment (user=None) and programmes belonging to the revision author
    available_programmes = Programme.objects.filter(programme_type=programme_type).filter(
        models.Q(user=revision.author) | models.Q(user__isnull=True)
    )
    
    # Include currently selected programme in options
    all_programmes = list(available_programmes)
    if current_programme and current_programme not in all_programmes:
        all_programmes.insert(0, current_programme)
    
    # Get aggregate student counts for this revision
    student_counts_data = revision.get_aggregate_student_counts()
    student_counts = {
        'min': {sem: data['min_students'] for sem, data in student_counts_data.items()},
        'max': {sem: data['max_students'] for sem, data in student_counts_data.items()}
    }

    programmes_data = []
    for programme in all_programmes:
        sws_range = programme.get_sws_range_total(student_counts)
        programmes_data.append({
            'id': programme.id,
            'name': programme.name,
            'modules_count': programme.modules.count(),
            'total_ects': programme.total_ects,
            'total_sws': programme.total_sws,
            'sws_range': sws_range,
            'total_courses': programme.total_courses,
            'author': (programme.user.get_full_name() or programme.user.username) if programme.user else 'System',
            'created': programme.created_at.strftime('%d.%m.%Y') if programme.created_at else '',
            'is_shared': programme.is_shared,
            'programme_type_display': programme.get_programme_type_display() if hasattr(programme, 'get_programme_type_display') else str(programme.programme_type),
            'description': programme.comment,
        })
    
    return JsonResponse({
        'programmes': programmes_data,
        'current_programme_id': current_programme.id if current_programme else None,
    })


def update_revision_programme(request, revision_id):
    """AJAX endpoint to update programme selection for a revision."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    revision = get_object_or_404(Revision, id=revision_id)
    programme_type = request.POST.get('programme_type')
    programme_id = request.POST.get('programme_id')
    
    if not programme_type:
        return JsonResponse({'success': False, 'error': 'Programme type required'})
    
    # Remove existing programme of this type from revision
    existing_programme = revision.programmes.filter(programme_type=programme_type).first()
    if existing_programme:
        revision.programmes.remove(existing_programme)
    
    # Add selected programme if provided
    if programme_id:
        try:
            programme = Programme.objects.get(id=programme_id, programme_type=programme_type)
            # Check if user has permission (programme belongs to same user as revision OR programme has no user)
            if programme.user is not None and programme.user != revision.author:
                return JsonResponse({'success': False, 'error': 'Keine Berechtigung für dieses Programm'})
            revision.programmes.add(programme)
        except Programme.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Programm nicht gefunden'})
    
    return JsonResponse({'success': True})


@login_required
def landing_page(request):
    """Landing page with usage information and navigation."""
    return render(request, 'studyprogrammes_v2/landing.html')


@login_required
def download_programme(request, programme_id):
    """Download a programme as JSON file."""
    programme = get_object_or_404(Programme, id=programme_id)
    
    # Generate JSON representation
    json_data = programme.to_json()
    
    # Create HTTP response with JSON content
    response = HttpResponse(json_data, content_type='application/json')
    
    # Create safe filename
    safe_name = programme.name.replace(' ', '_').replace('/', '_')
    filename = f"{safe_name}_{programme.programme_type}.json"
    
    # Set headers for download
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(json_data.encode('utf-8'))
    
    return response


