from django import forms


class MonthForm(forms.Form):
    month = forms.DateField(label="Mês", input_formats=["%Y-%m"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month"}))
