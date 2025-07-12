from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from .models import Course, Module, Programme, Revision, ProgrammeType, ProgrammeModule, ProgrammeStudentCount, CourseType, Discipline
from .forms import CourseForm, ModuleForm, ProgrammeForm, RevisionForm


@login_required
def course_overview(request):
    """Overview of all courses with ability to add/edit."""
    # Handle sorting
    sort_by = request.GET.get('sort', 'name')
    sort_order = request.GET.get('order', 'asc')
    
    # Valid sortable fields
    valid_sorts = ['name', 'semester', 'course_type', 'discipline']
    if sort_by not in valid_sorts:
        sort_by = 'name'
    
    # Apply sorting
    if sort_order == 'desc':
        sort_by = f'-{sort_by}'
    
    courses = Course.objects.all().order_by(sort_by)
    
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
                        semester=original_course.semester,
                        course_type=original_course.course_type,
                        ects=original_course.ects,
                        sws=original_course.sws,
                        max_participants=original_course.max_participants,
                        discipline=original_course.discipline
                    )
                    # Copy many-to-many relationships (LPO relevance)
                    copied_course.lpo_relevance.set(original_course.lpo_relevance.all())
                    
                except Course.DoesNotExist:
                    messages.error(request, 'Kurs nicht gefunden!')
                
                # Check if there's a return URL
                return_url = request.POST.get('return_url') or request.GET.get('return_url')
                if return_url:
                    return redirect(return_url)
                return redirect('v2_course_overview')
        
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
                form.save()
                
                # Check if there's a return URL
                return_url = request.POST.get('return_url') or request.GET.get('return_url')
                if return_url:
                    return redirect(return_url)
                return redirect('v2_course_overview')

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
            form.save()
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
    """Overview of all programmes with ability to add/edit."""
    # Handle sorting
    sort_param = request.GET.get('sort', 'name')  # Default to name sorting
    if sort_param == 'name':
        programmes = Programme.objects.all().order_by('name')
    elif sort_param == 'created':
        programmes = Programme.objects.all().order_by('-created_at')  # Most recent first
    else:
        programmes = Programme.objects.all().order_by('name')  # Fallback to name
    
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
                        user=request.user,  # Set to current user, not original
                        is_public=original_programme.is_public,
                        order=original_programme.order
                    )
                    # Copy many-to-many relationships (modules)
                    copied_programme.modules.set(original_programme.modules.all())
                    
                except Programme.DoesNotExist:
                    messages.error(request, 'Studiengang nicht gefunden!')
                return redirect('v2_programme_overview')
        
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
                programme.save()
                return redirect('v2_programme_overview')

    # Handle edit mode (GET with ?edit=<id>)
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_programme = get_object_or_404(Programme, id=edit_id)
        form = ProgrammeForm(instance=edit_programme)

    return render(request, 'studyprogrammes_v2/programme_overview.html', {
        'programmes': programmes,
        'form': form,
        'edit_programme': edit_programme,
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
    return redirect('v2_course_overview')


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
    return redirect('v2_programme_overview')


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
            module_certificate = request.POST.get('module_certificate', '')
            selected_courses = request.POST.getlist('module_courses')
            
            if module_name:
                # Create the new module and automatically add it to this programme
                new_module = Module.objects.create(
                    name=module_name.strip(),
                    description=module_description.strip(),
                    certificate=module_certificate.strip()
                )
                
                # Add selected courses to the module
                if selected_courses:
                    for course_id in selected_courses:
                        try:
                            course = Course.objects.get(id=course_id)
                            new_module.courses.add(course)
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
            module_certificate = request.POST.get('module_certificate', '')
            selected_courses = request.POST.getlist('module_courses')
            
            if module_id and module_name:
                try:
                    module = Module.objects.get(id=module_id)
                    # Update module details
                    module.name = module_name.strip()
                    module.description = module_description.strip()
                    module.certificate = module_certificate.strip()
                    module.save()
                    
                    # Update courses - first clear all, then add selected ones
                    module.courses.clear()
                    if selected_courses:
                        for course_id in selected_courses:
                            try:
                                course = Course.objects.get(id=course_id)
                                module.courses.add(course)
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
    student_counts = {
        'min': {int(sc.semester): int(sc.min_students) for sc in existing_counts},
        'max': {int(sc.semester): int(sc.max_students) for sc in existing_counts}
    }
    
    programme_modules = programme.get_ordered_modules()
    
    return render(request, 'studyprogrammes_v2/programme_detail.html', {
        'programme': programme,
        'programme_modules': programme_modules,
        'all_courses': all_courses,
        'semester_range': semester_range,
        'student_counts': student_counts,
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
    ).exclude(revisions=revision)
    
    # Include currently selected programme in options
    all_programmes = list(available_programmes)
    if current_programme and current_programme not in all_programmes:
        all_programmes.insert(0, current_programme)
    
    programmes_data = []
    for programme in all_programmes:
        programmes_data.append({
            'id': programme.id,
            'name': programme.name,
            'modules_count': programme.modules.count(),
            'total_ects': programme.total_ects,
            'total_courses': programme.total_courses,
            'author': programme.user.get_full_name() if programme.user else 'System',
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
