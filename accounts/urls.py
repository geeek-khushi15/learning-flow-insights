from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing_page'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/trainer/', views.trainer_register, name='trainer_register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.StudentProfileView.as_view(), name='student_profile'),
    path('trainer/profile/', views.TrainerProfileView.as_view(), name='trainer_profile'),
]
