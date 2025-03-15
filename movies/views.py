from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader


def home(request):
    return render(request, "main.html")

# Create your views here.

def movies(request):
    return render(request, "movies/movies.html")