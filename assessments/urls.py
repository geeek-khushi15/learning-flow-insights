from django.urls import path
from . import views

urlpatterns = [
    # Trainer
    path('test/create/', views.TestCreateView.as_view(), name='test_create'),
    path('test/<int:pk>/', views.TestDetailView.as_view(), name='test_detail'),
    path('test/<int:test_id>/question/add/', views.QuestionCreateView.as_view(), name='question_create'),
    
    # Student
    path('tests/', views.StudentTestListView.as_view(), name='student_test_list'),
    path('test/<int:test_id>/attempt/', views.TestAttemptView.as_view(), name='test_attempt'),
]
