from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, ProfileForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile

def loginUser(request):
    page = 'login'
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm(request)
    
    context = {
        'page': page,
        'form': form
    }
    return render(request, 'main.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    page = 'register'
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    context = {
        'page': page,
        'form': form
    }
    
    return render(request, 'main.html', context)

def userProfile(request, pk):
    profile = Profile.objects.get(id=pk)
    # playlists = Playlist.objects.filter(owner=profile)
    
    context = {
        'profile': profile,
        # 'playlists': playlists
    }
    return render(request, 'users/user-profile.html', context)

@login_required(login_url='login')
def userAccount(request):
    profile = request.user.profile

    context = {
        'profile': profile
    }
    return render(request, 'users/account.html', context)


@login_required(login_url='login')
def editAccount(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Check if the profile image clear checkbox was selected
            if request.POST.get('profile_image-clear') == 'on':
                # If the user had a custom image (not the default), delete it
                if profile.profile_image and profile.profile_image.name != 'static/images/avatars/user-default.png':
                    # Delete the file but don't save yet
                    profile.profile_image.delete(save=False)
                
                # Reset to default image path
                profile.profile_image = 'static/images/avatars/user-default.png'
            
            form.save()
            return redirect('account')
            
    context = {'form': form}
    return render(request, 'users/account-form.html', context)


@login_required(login_url='login')
def deleteAccount(request):
    if request.method == 'POST':
        request.user.delete()
        logout(request)
        return redirect('home')
    
    return redirect('edit-account')