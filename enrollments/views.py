from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from .models import Enrollment
from batches.models import Batch
from .forms import EnrollmentForm

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'STUDENT'

class EnrollmentCreateView(LoginRequiredMixin, StudentRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'enrollments/enrollment_form.html'
    success_url = reverse_lazy('enrollment_list')

    def form_valid(self, form):
        form.instance.student = self.request.user
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=self.request.user, batch=form.cleaned_data['batch']).exists():
            messages.error(self.request, "You are already enrolled in this batch.")
            return self.form_invalid(form)
            
        messages.success(self.request, f"Successfully enrolled in {form.cleaned_data['batch'].name}!")
        return super().form_valid(form)

class StudentEnrollmentListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = Enrollment
    template_name = 'enrollments/enrollment_list.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related('batch', 'batch__course')
