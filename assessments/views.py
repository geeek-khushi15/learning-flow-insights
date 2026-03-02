from django.views.generic import CreateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Test, Question, TestAttempt
from batches.models import Batch
from enrollments.models import Enrollment
from .forms import TestForm, QuestionForm

class TrainerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'TRAINER'

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'STUDENT'

class TestCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    model = Test
    form_class = TestForm
    template_name = 'assessments/test_form.html'
    
    def get_success_url(self):
        return reverse('test_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['trainer'] = self.request.user
        return kwargs

class TestDetailView(LoginRequiredMixin, TrainerRequiredMixin, DetailView):
    model = Test
    template_name = 'assessments/test_detail.html'
    context_object_name = 'test'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        return context

class QuestionCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'assessments/question_form.html'

    def form_valid(self, form):
        test = get_object_or_404(Test, pk=self.kwargs['test_id'])
        form.instance.test = test
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('test_detail', kwargs={'pk': self.kwargs['test_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = get_object_or_404(Test, pk=self.kwargs['test_id'])
        return context

class StudentTestListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = Test
    template_name = 'assessments/student_test_list.html'
    context_object_name = 'tests'

    def get_queryset(self):
        # Get batches the student is enrolled in
        enrolled_batches = Enrollment.objects.filter(student=self.request.user).values_list('batch', flat=True)
        return Test.objects.filter(batch__in=enrolled_batches).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass a list of test IDs the student has already attempted
        attempted_tests = TestAttempt.objects.filter(student=self.request.user).values_list('test_id', flat=True)
        context['attempted_test_ids'] = list(attempted_tests)
        return context

class TestAttemptView(LoginRequiredMixin, StudentRequiredMixin, View):
    def get(self, request, test_id):
        test = get_object_or_404(Test, pk=test_id)
        
        # Verify enrollment
        if not Enrollment.objects.filter(student=request.user, batch=test.batch).exists():
            messages.error(request, "You are not enrolled in the batch for this test.")
            return redirect('dashboard')
            
        # Check if already attempted
        if TestAttempt.objects.filter(student=request.user, test=test).exists():
            messages.info(request, "You have already attempted this test.")
            return redirect('dashboard')

        questions = test.questions.all()
        return render(request, 'assessments/test_attempt.html', {'test': test, 'questions': questions})

    def post(self, request, test_id):
        test = get_object_or_404(Test, pk=test_id)
        
        # Verify enrollment and duplicate attempt
        if not Enrollment.objects.filter(student=request.user, batch=test.batch).exists():
            return redirect('dashboard')
        if TestAttempt.objects.filter(student=request.user, test=test).exists():
            return redirect('dashboard')

        score = 0
        questions = test.questions.all()
        
        # Evaluate answers
        for question in questions:
            selected_option = request.POST.get(f'question_{question.id}')
            if selected_option and int(selected_option) == question.correct_option:
                score += 1
                
        # Save Attempt
        TestAttempt.objects.create(
            student=request.user,
            test=test,
            score=score
        )
        
        messages.success(request, f"Test submitted! Your score: {score}/{questions.count()}")
        return redirect('dashboard')
