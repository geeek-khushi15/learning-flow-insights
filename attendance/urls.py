from django.urls import path
from . import views

urlpatterns = [
    # Trainer
    path('trainer/sessions/', views.trainer_session_list, name='trainer_session_list'),
    path('trainer/session/create/', views.create_session, name='create_session'),
    path('trainer/session/<int:session_id>/attendance/', views.mark_attendance, name='mark_attendance'),
    path('trainer/session/<int:session_id>/topics/', views.manage_session_topics, name='manage_session_topics'),
    
    # Student
    path('student/sessions/', views.student_session_list, name='student_session_list'),
    path('student/session/<int:session_id>/topics/', views.student_acknowledge_topics, name='student_acknowledge_topics'),
]