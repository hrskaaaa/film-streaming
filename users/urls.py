from django.urls import path
from . import views



urlpatterns = [
    path('login/', views.loginPage, name="login"),
    
    path('', views.profile, name="profile")
]