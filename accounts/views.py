from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import StudentRegistrationForm, TrainerRegistrationForm

def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register_student.html', {'form': form})

def trainer_register(request):
    if request.method == 'POST':
        form = TrainerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = TrainerRegistrationForm()
    return render(request, 'accounts/register_trainer.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        return reverse('dashboard')

@login_required
def dashboard(request):
    if request.user.role == 'STUDENT':
        return render(request, 'accounts/student_dashboard.html')
    elif request.user.role == 'TRAINER':
        return render(request, 'accounts/trainer_dashboard.html')
    else:
        return render(request, 'accounts/admin_dashboard.html')


from django.views.generic import TemplateView

class LandingPageView(TemplateView):
    template_name = 'accounts/landing_page.html'


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from enrollments.models import Enrollment

class StudentRequiredMixin(UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'STUDENT'

class StudentProfileView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    template_name = 'accounts/student_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch the student's enrollments to get assigned batch and course details
        context['enrollments'] = Enrollment.objects.filter(student=self.request.user).select_related('batch', 'batch__course')
        return context


from batches.models import Batch

class TrainerRequiredMixin(UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'TRAINER'

class TrainerProfileView(LoginRequiredMixin, TrainerRequiredMixin, TemplateView):
    template_name = 'accounts/trainer_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch the trainer's assigned batches
        context['batches'] = Batch.objects.filter(trainer=self.request.user).select_related('course')
        return context
