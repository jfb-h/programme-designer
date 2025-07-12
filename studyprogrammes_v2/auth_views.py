from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect


@csrf_protect
def login_view(request):
    """Custom login view for studyprogrammes_v2"""
    if request.user.is_authenticated:
        return redirect('v2_programme_overview')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'v2_programme_overview')
                return redirect(next_url)
        else:
            messages.error(request, 'Ungültige Anmeldedaten. Bitte versuchen Sie es erneut.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'studyprogrammes_v2/auth/login.html', {
        'form': form,
        'title': 'Anmelden'
    })


@csrf_protect
def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('v2_programme_overview')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            login(request, user)
            return redirect('v2_programme_overview')
        else:
            messages.error(request, 'Fehler bei der Registrierung. Bitte überprüfen Sie Ihre Eingaben.')
    else:
        form = UserCreationForm()
    
    return render(request, 'studyprogrammes_v2/auth/register.html', {
        'form': form,
        'title': 'Registrieren'
    })


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Custom logout view"""
    if request.user.is_authenticated:
        logout(request)
    return redirect('v2_login')


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    
    # Get user statistics
    from .models import Programme, Revision
    
    user_programmes = Programme.objects.filter(user=user).count()
    user_revisions = Revision.objects.filter(author=user).count()
    
    context = {
        'user': user,
        'user_programmes': user_programmes,
        'user_revisions': user_revisions,
        'title': 'Mein Profil'
    }
    
    return render(request, 'studyprogrammes_v2/auth/profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit user profile"""
    user = request.user
    
    if request.method == 'POST':
        # Update basic user info
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        return redirect('v2_profile')
    
    context = {
        'user': user,
        'title': 'Profil bearbeiten'
    }
    
    return render(request, 'studyprogrammes_v2/auth/edit_profile.html', context)


def user_list_view(request):
    """View to list all users - for admin purposes"""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Sie haben keine Berechtigung für diese Seite.')
        return redirect('v2_programme_overview')
    
    users = User.objects.all().order_by('username')
    
    context = {
        'users': users,
        'title': 'Benutzer verwalten'
    }
    
    return render(request, 'studyprogrammes_v2/auth/user_list.html', context)
