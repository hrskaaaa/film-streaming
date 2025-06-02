from django.db import models
import uuid
from django.contrib.auth.models import User


class Profile(models.Model):

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=500, blank=True, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)    
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_image = models.ImageField(
        null=True, blank=True, upload_to='static/images/avatars/', default='static/images/avatars/user-default.png')
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, 
                            primary_key=True, editable=False)
    
    def __str__(self):
        return str( self.username)


# class Playlist(models.Model):
#     owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
#     title = models.CharField(max_length=200)
#     description = models.TextField(null=True, blank=True)
#     # videos = models.ManyToManyField('Video')  # Assuming you have a Video model
#     created = models.DateTimeField(auto_now_add=True)
#     id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

#     def __str__(self):
#         return self.title