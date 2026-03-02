from django import forms
from .models import Test, Question
from batches.models import Batch

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'batch', 'passing_marks']

    def __init__(self, *args, **kwargs):
        trainer = kwargs.pop('trainer', None)
        super().__init__(*args, **kwargs)
        if trainer:
            self.fields['batch'].queryset = Batch.objects.filter(trainer=trainer)

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_option']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }
