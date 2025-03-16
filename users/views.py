
from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
# Create your views here.


def loginUser(request):

    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            print('Username does not exist')
# if it would find the username that match the username and password that match that user it will return this user
        user = authenticate(request, username=username, password=password)

# if user exist login func will create a session for this user in database and it will add this session to browser cookies
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            print("Username OR password is incorrect ")

    return render(request, 'users/login_register.html')

def logoutUser(request):
    logout(request)
    return redirect('login')

def profile(request):
    return render(request, 'users/user-profile.html')
