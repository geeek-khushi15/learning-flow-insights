from django.contrib import admin
from .models import Enrollment

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'batch', 'enrollment_date')
    list_filter = ('batch', 'enrollment_date')
    search_fields = ('student__username', 'student__email', 'student__first_name', 'student__last_name', 'batch__name')
