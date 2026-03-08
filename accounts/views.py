from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .forms import StudentRegistrationForm, TrainerRegistrationForm, StudentDoubtForm
from .models import User, TrainerProfile, EmployeeAttendanceLog, StudentProfile, StudentDoubt

from enrollments.models import Enrollment
from batches.models import Batch
from assessments.models import TestAttempt


# ===============================
# STUDENT REGISTRATION
# ===============================

def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create empty profile automatically
            StudentProfile.objects.get_or_create(user=user)

            login(request, user)
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register_student.html', {'form': form})


# ===============================
# TRAINER REGISTRATION
# ===============================

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


# ===============================
# LOGIN
# ===============================

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dashboard')


# ===============================
# LOGOUT
# ===============================

def custom_logout(request):
    logout(request)
    return redirect('login')


# ===============================
# DASHBOARD
# ===============================

@login_required
def dashboard(request):

    if request.user.role == 'STUDENT':

        enrollments = Enrollment.objects.filter(
            student=request.user
        ).select_related('batch', 'batch__course')

        from attendance.models import TopicAcknowledgement

        pending_acknowledgements = TopicAcknowledgement.objects.filter(
            student=request.user,
            student_understood=False
        ).select_related('session_topic__session__batch', 'session_topic__session')

        if request.method == 'POST' and request.POST.get('action') == 'raise_doubt':
            doubt_form = StudentDoubtForm(request.POST, student=request.user)

            if doubt_form.is_valid():
                doubt = doubt_form.save(commit=False)
                doubt.student = request.user

                if doubt.related_session and not doubt.related_course:
                    doubt.related_course = doubt.related_session.batch.course

                if doubt.related_session and doubt.related_session.trainer:
                    doubt.trainer = doubt.related_session.trainer
                elif doubt.related_course:
                    first_enrollment = Enrollment.objects.filter(
                        student=request.user,
                        batch__course=doubt.related_course
                    ).select_related('batch__trainer').first()

                    if first_enrollment:
                        doubt.trainer = first_enrollment.batch.trainer

                doubt.save()
                return redirect(f"{reverse('dashboard')}#raise-doubt")
        else:
            doubt_form = StudentDoubtForm(student=request.user)

        submitted_doubts = StudentDoubt.objects.filter(
            student=request.user,
            status=StudentDoubt.Status.PENDING
        ).select_related('related_course', 'related_session', 'trainer')

        resolved_doubts = StudentDoubt.objects.filter(
            student=request.user,
            status=StudentDoubt.Status.RESOLVED
        ).select_related('related_course', 'related_session', 'trainer')

        return render(request, 'accounts/student_dashboard.html', {
            'enrollments': enrollments,
            'pending_acknowledgements': pending_acknowledgements,
            'doubt_form': doubt_form,
            'submitted_doubts': submitted_doubts,
            'resolved_doubts': resolved_doubts,
        })


    elif request.user.role == 'TRAINER':

        batches = Batch.objects.filter(
            trainer=request.user
        ).select_related('course')

        trainer_enrollments = Enrollment.objects.filter(
            batch__trainer=request.user
        ).select_related('student', 'batch__course')

        enrolled_students_count = trainer_enrollments.values('student').distinct().count()

        students_with_progress = []

        for en in trainer_enrollments:

            tests_attempted = TestAttempt.objects.filter(
                student=en.student,
                test__batch=en.batch
            ).count()

            total_tests = en.batch.tests.count()

            progress_val = 0

            if total_tests > 0:
                progress_val = int((tests_attempted / total_tests) * 100)

            students_with_progress.append({
                'enrollment': en,
                'progress': progress_val
            })

        from attendance.models import TopicAcknowledgement

        pending_acknowledgements = TopicAcknowledgement.objects.filter(
            session_topic__session__trainer=request.user,
            student_understood=False
        ).select_related(
            'session_topic__session',
            'student'
        ).order_by('-session_topic__session__date')

        from datetime import date

        today_log = EmployeeAttendanceLog.objects.filter(
            trainer=request.user,
            date=date.today()
        ).first()

        trainer_doubts = StudentDoubt.objects.filter(
            student__enrollments__batch__trainer=request.user
        ).distinct().select_related(
            'student',
            'related_course',
            'related_session',
            'trainer'
        )

        if request.method == 'POST' and request.POST.get('action') in {'trainer_reply', 'trainer_resolve'}:
            doubt = get_object_or_404(
                trainer_doubts,
                id=request.POST.get('doubt_id')
            )

            response_text = request.POST.get('response', '').strip()

            if response_text:
                doubt.response = response_text

            doubt.trainer = request.user

            if request.POST.get('action') == 'trainer_resolve':
                doubt.status = StudentDoubt.Status.RESOLVED
                doubt.resolved_at = timezone.now()

            doubt.save()
            return redirect(f"{reverse('dashboard')}#student-doubts")

        trainer_pending_doubts = trainer_doubts.filter(status=StudentDoubt.Status.PENDING)
        trainer_resolved_doubts = trainer_doubts.filter(status=StudentDoubt.Status.RESOLVED)[:10]

        return render(request, 'accounts/trainer_dashboard.html', {
            'pending_acknowledgements': pending_acknowledgements,
            'batches': batches,
            'enrolled_students_count': enrolled_students_count,
            'students_with_progress': students_with_progress,
            'today_log': today_log,
            'trainer_pending_doubts': trainer_pending_doubts,
            'trainer_resolved_doubts': trainer_resolved_doubts,
        })

    else:
        admin_doubts = StudentDoubt.objects.select_related(
            'student',
            'trainer',
            'related_course',
            'related_session'
        )

        if request.method == 'POST' and request.POST.get('action') in {'admin_reply', 'admin_resolve'}:
            doubt = get_object_or_404(admin_doubts, id=request.POST.get('doubt_id'))

            response_text = request.POST.get('response', '').strip()

            if response_text:
                doubt.response = response_text

            if request.POST.get('action') == 'admin_resolve':
                doubt.status = StudentDoubt.Status.RESOLVED
                doubt.resolved_at = timezone.now()

            doubt.save()
            return redirect(f"{reverse('dashboard')}#admin-doubts")

        return render(request, 'accounts/admin_dashboard.html', {
            'admin_pending_doubts': admin_doubts.filter(status=StudentDoubt.Status.PENDING),
            'admin_resolved_doubts': admin_doubts.filter(status=StudentDoubt.Status.RESOLVED)[:20],
        })


# ===============================
# LANDING PAGE
# ===============================

class LandingPageView(TemplateView):
    template_name = 'accounts/landing_page.html'


@login_required
def student_raise_doubt(request):
    return redirect(f"{reverse('dashboard')}#raise-doubt")


# ===============================
# ROLE MIXINS
# ===============================

class StudentRequiredMixin(UserPassesTestMixin):

    raise_exception = True

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            getattr(self.request.user, 'role', '') == 'STUDENT'
        )


class TrainerRequiredMixin(UserPassesTestMixin):

    raise_exception = True

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            getattr(self.request.user, 'role', '') == 'TRAINER'
        )


# ===============================
# STUDENT PROFILE VIEW
# ===============================

class StudentProfileView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):

    template_name = 'accounts/student_profile.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # Fetch enrollments
        context['enrollments'] = Enrollment.objects.filter(
            student=self.request.user
        ).select_related('batch', 'batch__course')

        # Fetch or create profile
        profile, created = StudentProfile.objects.get_or_create(
            user=self.request.user
        )

        context['profile'] = profile

        return context


# ===============================
# TRAINER PROFILE
# ===============================

class TrainerProfileView(LoginRequiredMixin, TrainerRequiredMixin, TemplateView):

    template_name = 'accounts/trainer_profile.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['batches'] = Batch.objects.filter(
            trainer=self.request.user
        ).select_related('course')

        return context


# ===============================
# TRAINER FACE SETUP
# ===============================

def trainer_setup_face(request):

    trainer_id = request.session.get('pending_trainer_id')

    if not trainer_id:
        return redirect('login')

    try:
        trainer = User.objects.get(id=trainer_id, role='TRAINER')
    except User.DoesNotExist:
        return redirect('login')

    return render(request, 'accounts/trainer_setup_face.html', {
        'trainer': trainer
    })


# ===============================
# EMPLOYEE FACE LOGIN
# ===============================

@login_required
def employee_verification(request):

    if request.user.role != 'TRAINER':
        return redirect('dashboard')

    try:
        profile = TrainerProfile.objects.get(user=request.user)
    except TrainerProfile.DoesNotExist:
        return redirect('dashboard')

    if not profile.is_setup_complete or not profile.face_descriptor:
        return redirect('trainer_setup_face')

    from datetime import date

    already_logged_in = EmployeeAttendanceLog.objects.filter(
        trainer=request.user,
        date=date.today()
    ).exists()

    if already_logged_in:
        return redirect('dashboard')

    return render(request, 'accounts/employee_verification.html', {
        'trainer': request.user,
        'saved_descriptor': profile.face_descriptor
    })


# ===============================
# FACE API
# ===============================

import json

@csrf_exempt
def api_employee_verification(request):

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            action = data.get('action')

            user_auth = request.user if request.user.is_authenticated else None

            trainer_id = request.session.get('pending_trainer_id')

            if not user_auth and not trainer_id:
                return JsonResponse({'success': False})

            trainer = user_auth if user_auth else User.objects.get(id=trainer_id)

            if action == 'register_face':

                descriptor = data.get('descriptor')

                profile = TrainerProfile.objects.get(user=trainer)

                profile.face_descriptor = json.dumps(descriptor)

                profile.is_setup_complete = True

                profile.save()

                return JsonResponse({'success': True})

            elif action == 'verify_face':

                status = data.get('status') == 'success'

                lat = data.get('lat')
                lng = data.get('lng')

                if status:

                    from datetime import date

                    log, created = EmployeeAttendanceLog.objects.get_or_create(
                        trainer=trainer,
                        date=date.today(),
                        defaults={
                            'login_time': timezone.now().time(),
                            'latitude': lat,
                            'longitude': lng,
                            'face_verified': True
                        }
                    )

                    if not created:
                        return JsonResponse({'success': False})

                    return JsonResponse({'success': True})

        except Exception as e:

            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False})


# ===============================
# CHECKOUT API
# ===============================

@login_required
@csrf_exempt
def api_employee_checkout(request):

    if request.method == 'POST':

        if request.user.role != 'TRAINER':
            return JsonResponse({'success': False})

        from datetime import date

        try:

            today_log = EmployeeAttendanceLog.objects.get(
                trainer=request.user,
                date=date.today()
            )

            if today_log.logout_time:
                return JsonResponse({'success': False})

            today_log.logout_time = timezone.now().time()

            today_log.save()

            return JsonResponse({'success': True})

        except EmployeeAttendanceLog.DoesNotExist:

            return JsonResponse({'success': False})

    return JsonResponse({'success': False})