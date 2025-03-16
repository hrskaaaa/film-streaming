
from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
# Create your views here.


def loginUser(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')
# if it would find the username that match the username and password that match that user it will return this user
        user = authenticate(request, username=username, password=password)

# if user exist login func will create a session for this user in database and it will add this session to browser cookies
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
             messages.error(request,"Username OR password is incorrect ")

    return render(request, 'users/login_register.html')

def logoutUser(request):
    logout(request)
    messages.success(request,"You were logged out ")

    return redirect('login')

def registerUser(request):
    page = 'register'
    form = UserCreationForm()
    context = {'page':page, 'form':form}

    if request.method =='POST':
        form = UserCreationForm(request.POST)
        # if everything is okay with info in form
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            messages.success(request, 'Account was created!')
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An arror has occurred diring registrations')


    return render(request, 'users/login_register.html', context)


def profile(request):
    return render(request, 'users/user-profile.html')
