from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        TRAINER = 'TRAINER', 'Trainer'
        ADMIN = 'ADMIN', 'Admin'
    
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
