from django import forms
from .models import Liability

class LiabilityForm(forms.ModelForm):
    class Meta:
        model = Liability
        fields = ['name', 'amount', 'interest_rate', 'end_date']
