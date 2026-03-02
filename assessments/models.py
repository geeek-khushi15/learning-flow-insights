from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from batches.models import Batch

class Test(models.Model):
    title = models.CharField(max_length=200)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='tests')
    passing_marks = models.PositiveIntegerField(default=40, help_text="Minimum marks to pass")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.batch.name}"
        
    @property
    def total_marks(self):
        return self.questions.count()

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(help_text="The question text.")
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    
    correct_option = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Select 1, 2, 3, or 4."
    )

    def __str__(self):
        return f"Q: {self.text[:50]}"

class TestAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A student should only be able to attempt a specific test once.
        unique_together = ('student', 'test')

    def __str__(self):
        return f"{self.student.username} - {self.test.title} ({self.score})"
        
    @property
    def is_passed(self):
        return self.score >= self.test.passing_marks
