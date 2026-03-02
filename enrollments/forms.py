from django import forms
from .models import Enrollment
from batches.models import Batch

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['batch']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Students should only be able to enroll in batches that make sense
        # For simplicity, we show all active batches here.
        self.fields['batch'].queryset = Batch.objects.all()
