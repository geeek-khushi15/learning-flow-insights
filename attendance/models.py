from django.db import models
from accounts.models import User
from batches.models import Batch

class ClassSession(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    # topics_covered is kept for backwards compatibility or as a summary, but granular tracking is done via SessionTopic
    topics_covered = models.TextField(help_text="Describe the topics covered in this session", blank=True)
    trainer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'TRAINER'}, related_name='conducted_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.batch.name} - {self.date}"

class SessionTopic(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='topics')
    topic_name = models.CharField(max_length=255)
    trainer_taught = models.BooleanField(default=False)
    taught_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.topic_name} - {self.session.date}"

class Attendance(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='session_attendances')
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.username} - {self.session.date} ({status})"

class TopicAcknowledgement(models.Model):
    session_topic = models.ForeignKey(SessionTopic, on_delete=models.CASCADE, related_name='acknowledgements')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='topic_acknowledgements')
    student_understood = models.BooleanField(default=False)
    understood_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('session_topic', 'student')

    def __str__(self):
        status = "Understood" if self.student_understood else "Pending"
        return f"{self.student.username} - {self.session_topic.topic_name} ({status})"
