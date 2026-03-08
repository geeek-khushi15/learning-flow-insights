from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, StudentDoubt
from courses.models import Course
from attendance.models import ClassSession
from enrollments.models import Enrollment


# =========================
# Student Registration
# =========================

class StudentRegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user


# =========================
# Trainer Registration
# =========================

class TrainerRegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.TRAINER
        if commit:
            user.save()
        return user


# =========================
# Student Profile Form
# =========================

class StudentProfileForm(forms.ModelForm):

    class Meta:
        model = StudentProfile

        fields = [
            'full_name',
            'father_name',
            'mother_name',
            'date_of_birth',
            'contact_number',
            'caste_category',
            'highest_education',
            'address',
            'pincode',
            'course_start_date',
            'course_end_date',
            'profile_photo',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'course_start_date': forms.DateInput(attrs={'type': 'date'}),
            'course_end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StudentDoubtForm(forms.ModelForm):

    class Meta:
        model = StudentDoubt
        fields = ['title', 'description', 'related_course', 'related_session']
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'w-full rounded-lg border-gray-300',
                    'placeholder': 'Write a short title for your doubt'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full rounded-lg border-gray-300',
                    'rows': 5,
                    'placeholder': 'Describe your doubt in detail so trainers can help faster'
                }
            ),
            'related_course': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300'}),
            'related_session': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        self.fields['related_course'].required = False
        self.fields['related_session'].required = False

        self.fields['related_course'].empty_label = 'Optional: Select related course'
        self.fields['related_session'].empty_label = 'Optional: Select related session'

        self.fields['related_course'].queryset = Course.objects.none()
        self.fields['related_session'].queryset = ClassSession.objects.none()

        if student is not None:
            enrollments = Enrollment.objects.filter(
                student=student
            ).select_related('batch', 'batch__course')

            course_ids = enrollments.values_list('batch__course_id', flat=True)
            batch_ids = enrollments.values_list('batch_id', flat=True)

            self.fields['related_course'].queryset = Course.objects.filter(id__in=course_ids).distinct()
            self.fields['related_session'].queryset = ClassSession.objects.filter(
                batch_id__in=batch_ids
            ).select_related('batch').order_by('-date')

            self.fields['related_session'].label_from_instance = (
                lambda obj: f"{obj.batch.name} ({obj.date})"
            )