from django import forms

class RadioForm(forms.Form):
    options = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )

    radio_choice = forms.ChoiceField(
        choices=options,
        widget=forms.RadioSelect
    )
