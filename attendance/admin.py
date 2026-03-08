from django.contrib import admin
from .models import ClassSession, SessionTopic, Attendance, TopicAcknowledgement

@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('batch', 'date', 'trainer', 'created_at')
    list_filter = ('batch', 'trainer', 'date')
    search_fields = ('batch__name', 'topics_covered', 'trainer__username')

@admin.register(SessionTopic)
class SessionTopicAdmin(admin.ModelAdmin):
    list_display = ('session', 'topic_name', 'trainer_taught', 'taught_at')
    list_filter = ('trainer_taught', 'session__batch')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'is_present')
    list_filter = ('is_present', 'session__batch', 'session__date')
    search_fields = ('student__username', 'student__email')

@admin.register(TopicAcknowledgement)
class TopicAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('session_topic', 'student', 'student_understood', 'understood_at')
    list_filter = ('student_understood', 'session_topic__session__batch')
    search_fields = ('student__username', 'session_topic__topic_name')
