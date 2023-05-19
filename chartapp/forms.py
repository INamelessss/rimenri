from django import forms

class DateFilterForm(forms.Form):
    fecha_inicial = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_final = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
