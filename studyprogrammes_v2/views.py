from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Course, Module, Programme, Revision, ProgrammeType, ProgrammeModule, ProgrammeStudentCount
from .forms import CourseForm, ModuleForm, ProgrammeForm, RevisionForm
def programme_detail(request, programme_id):
    """Detail view for a programme where modules can be managed."""
    programme = get_object_or_404(Programme, id=programme_id)
    all_courses = Course.objects.all()
    
    # Get semester range based on programme type
    semester_count = programme.get_semester_count()
    semester_range = range(1, semester_count + 1)
    
    # Get existing student counts
    existing_counts = ProgrammeStudentCount.objects.filter(programme=programme)
    student_counts = {
        'min': {count.semester: count.min_students for count in existing_counts},
        'max': {count.semester: count.max_students for count in existing_counts}
    }
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_student_count':
            # Handle AJAX student count updates
            programme_id = request.POST.get('programme_id')
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
                
                student_count.save()
                
                return JsonResponse({'status': 'success'})
                
            except (ValueError, TypeError) as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        
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
            selected_courses = request.POST.getlist('module_courses')
            
            if module_name:
                # Create the new module and automatically add it to this programme
                new_module = Module.objects.create(
                    name=module_name.strip(),
                    description=module_description.strip()
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
            selected_courses = request.POST.getlist('module_courses')
            
            if module_id and module_name:
                try:
                    module = Module.objects.get(id=module_id)
                    # Update module details
                    module.name = module_name.strip()
                    module.description = module_description.strip()
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
    
    # Get existing student counts
    existing_counts = ProgrammeStudentCount.objects.filter(programme=programme)
    student_counts = {
        'min': {sc.semester: sc.min_students for sc in existing_counts},
        'max': {sc.semester: sc.max_students for sc in existing_counts}
    }
    
    return render(request, 'studyprogrammes_v2/programme_detail.html', {
        'programme': programme,
        'programme_modules': programme.get_ordered_modules(),
        'all_courses': all_courses,
        'semester_range': semester_range,
        'student_counts': student_counts,
    })


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
                    
                    messages.success(request, f'Kurs "{copied_course.name}" erfolgreich kopiert!')
                except Course.DoesNotExist:
                    messages.error(request, 'Kurs nicht gefunden!')
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
                messages.success(request, 'Kurs gespeichert!')
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
    })


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
            messages.success(request, 'Modul gespeichert!')
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


def programme_overview(request):
    """Overview of all programmes with ability to add/edit."""
    programmes = Programme.objects.all()
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
                        user=original_programme.user,
                        is_public=original_programme.is_public,
                        order=original_programme.order
                    )
                    # Copy many-to-many relationships (modules)
                    copied_programme.modules.set(original_programme.modules.all())
                    
                    messages.success(request, f'Studiengang "{copied_programme.name}" erfolgreich kopiert!')
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
                form.save()
                messages.success(request, 'Studiengang gespeichert!')
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
            messages.success(request, f'Revision "{revision.name}" erstellt!')
            return redirect('v2_revision_overview')

    return render(request, 'studyprogrammes_v2/revision_overview.html', {
        'revisions': revisions,
        'form': form,
    })


def revision_detail(request, revision_id):
    """Detailed view of a specific revision with programme management."""
    revision = get_object_or_404(Revision, id=revision_id)
    
    # Get all programme types and existing programmes
    from .models import ProgrammeType
    programme_types = ProgrammeType.choices
    programmes_by_type = {}
    
    # Get all programmes associated with this revision
    programmes = Programme.objects.filter(revisions=revision)
    for programme in programmes:
        programmes_by_type[programme.programme_type] = programme

    return render(request, 'studyprogrammes_v2/revision_detail.html', {
        'revision': revision,
        'programme_types': programme_types,
        'programmes_by_type': programmes_by_type,
    })


def edit_revision(request, revision_id):
    """Edit a specific revision and its programmes."""
    revision = get_object_or_404(Revision, id=revision_id)
    
    # Get existing programmes in this revision
    existing_programmes = list(revision.programmes.all())
    
    # Build list of all possible programme types with status
    programme_options = []
    existing_types = [p.programme_type for p in existing_programmes]
    
    for choice_value, choice_display in ProgrammeType.choices:
        existing_programme = next(
            (p for p in existing_programmes if p.programme_type == choice_value), 
            None
        )
        programme_options.append({
            'type': choice_value,
            'display': choice_display,
            'programme': existing_programme,
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
            programme_type=programme_type
        )
        revision.programmes.add(programme)

    form = ProgrammeForm(instance=programme)
    
    if request.method == 'POST':
        form = ProgrammeForm(request.POST, instance=programme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Studiengang gespeichert!')
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
        messages.success(request, f'Kurs "{course.name}" gelöscht!')
    return redirect('v2_course_overview')


def delete_module(request, module_id):
    """Delete a module."""
    module = get_object_or_404(Module, id=module_id)
    if request.method == 'POST':
        module.delete()
        messages.success(request, f'Modul "{module.name}" gelöscht!')
    return redirect('v2_module_overview')


def delete_programme(request, programme_id):
    """Delete a programme."""
    programme = get_object_or_404(Programme, id=programme_id)
    if request.method == 'POST':
        programme.delete()
        messages.success(request, f'Studiengang "{programme.name}" gelöscht!')
    return redirect('v2_programme_overview')


def delete_revision(request, revision_id):
    """Delete a revision."""
    revision = get_object_or_404(Revision, id=revision_id)
    if request.method == 'POST':
        revision.delete()
        messages.success(request, f'Revision "{revision.name}" gelöscht!')
    return redirect('v2_revision_overview')


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
            selected_courses = request.POST.getlist('module_courses')
            
            if module_name:
                # Create the new module and automatically add it to this programme
                new_module = Module.objects.create(
                    name=module_name.strip(),
                    description=module_description.strip()
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
            selected_courses = request.POST.getlist('module_courses')
            
            if module_id and module_name:
                try:
                    module = Module.objects.get(id=module_id)
                    # Update module details
                    module.name = module_name.strip()
                    module.description = module_description.strip()
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
    
    # Get existing student counts
    existing_counts = ProgrammeStudentCount.objects.filter(programme=programme)
    student_counts = {
        'min': {sc.semester: sc.min_students for sc in existing_counts},
        'max': {sc.semester: sc.max_students for sc in existing_counts}
    }
    
    return render(request, 'studyprogrammes_v2/programme_detail.html', {
        'programme': programme,
        'programme_modules': programme.get_ordered_modules(),
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
        # Clear existing relationships
        ProgrammeModule.objects.filter(programme=programme).delete()
        
        # Re-create relationships with proper ordering
        for order, module_id in enumerate(module_ids):
            if module_id:
                module = get_object_or_404(Module, id=module_id)
                ProgrammeModule.objects.create(
                    programme=programme,
                    module=module,
                    order=order
                )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)
