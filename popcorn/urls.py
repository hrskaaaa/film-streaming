from django.contrib import admin
from django.urls import include, path

from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", include("movies.urls")),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),

    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="reset_password.html"), 
         name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="reset_password_sent.html"), 
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="reset.html"), 
         name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="reset_password_complete.html"), 
         name="password_reset_complete"),
]
